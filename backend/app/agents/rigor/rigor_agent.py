"""Rigor analysis agent for experimental and mathematical soundness."""
from typing import Dict, Any, List, Optional
import logging
from langchain_core.retrievers import BaseRetriever
from langchain_core.tools import BaseTool
from langchain_core.messages import AIMessage, ToolMessage

from app.agents.base_agent import BaseReviewerAgent
from app.models.schemas import RigorAnalysisResponse, RigorReflectionResponse
from app.prompts.rigor import build_analysis_prompt, build_reflection_prompt

logger = logging.getLogger(__name__)


class RigorAgent(BaseReviewerAgent):
    """
    Agent focused on analyzing experimental and mathematical rigor.

    Sample rigor checks include
    - Control experiments before causal claims
    - Statistical test appropriateness
    - Sample sizes and statistical power
    - Confidence intervals, p-values, effect sizes
    - Experimental setup clarity
    - Mathematical assumptions and proofs
    """

    def __init__(
        self,
        retriever: Optional[BaseRetriever] = None,
        tavily_tool: Optional[BaseTool] = None
    ):
        """
        Initialize Rigor Agent.

        Args:
            retriever: Optional LangChain retriever for RAG (uploaded guidelines)
            tavily_tool: Optional Tavily search tool for external best practices
        """
        from app.config import settings
        super().__init__(
            agent_name="RigorAgent",
            agent_description="Analyzes experimental and mathematical rigor",
            model=settings.rigor_agent_model
        )
        self.analysis_prompt = build_analysis_prompt()
        self.reflection_prompt = build_reflection_prompt()
        self.retriever = retriever
        self.tavily_tool = tavily_tool
        self.enable_tavily = settings.is_tavily_enabled and tavily_tool is not None

        if self.enable_tavily:
            logger.info("[RigorAgent] Tavily search enabled for best practices validation")
        else:
            logger.info("[RigorAgent] Tavily search disabled (using LLM knowledge only)")

    def _is_rigor_relevant(self, section: Dict[str, Any]) -> bool:
        """
        Check if section is relevant for rigor analysis.

        Args:
            section: Section dictionary

        Returns:
            True if section should be analyzed for rigor
        """
        title_lower = section["title"].lower()
        relevant_keywords = [
            "method", "methodology", "experiment", "evaluation",
            "result", "analysis", "proof", "theorem", "lemma",
            "implementation", "setup", "design", "procedure"
        ]
        return any(keyword in title_lower for keyword in relevant_keywords)

    async def analyze(self, section: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze a section for rigor issues with self-reflection (ReAct pattern).

        Uses structured outputs with Pydantic models for guaranteed data contracts.

        Steps:
        1. Check if section requires rigor analysis
        2. Analyze section for rigor issues (structured output)
        3. Self-reflect and validate findings (structured output)
        4. Return validated suggestions

        Args:
            section: Section dictionary with 'title', 'content', 'line_start', 'line_end'

        Returns:
            List of validated rigor suggestion dictionaries
        """
        # Step 1: Skip if not relevant
        if not self._is_rigor_relevant(section):
            logger.debug("[RigorAgent] Skipping non-relevant section: %s", section['title'])
            return []

        logger.info("[RigorAgent] Analyzing section: %s", section['title'])

        # Step 1.5: Retrieve relevant rigor guidelines using LangChain retriever (RAG)
        guidelines_context = ""
        if self.retriever:
            try:
                # Use first 500 chars of section content as query
                query_text = section["content"][:500] if len(section["content"]) > 500 else section["content"]

                # Use LangChain's ainvoke method for async retrieval
                langchain_docs = await self.retriever.ainvoke(query_text)

                if langchain_docs:
                    # Convert LangChain Documents to context string
                    guidelines_list = [
                        f"- {doc.page_content[:200]}..."
                        if len(doc.page_content) > 200
                        else f"- {doc.page_content}"
                        for doc in langchain_docs
                    ]
                    guidelines_context = "\n".join(guidelines_list)
                    logger.info(
                        "[RigorAgent] Retrieved %d relevant guidelines using %s",
                        len(langchain_docs),
                        type(self.retriever).__name__
                    )
                else:
                    logger.info("[RigorAgent] No relevant guidelines found")
            except Exception as e:
                logger.warning(f"[RigorAgent] Error retrieving guidelines: {e}")

        # Step 2: Initial analysis with Tavily function calling (if enabled)
        if self.enable_tavily:
            analysis_response = await self._analyze_with_tavily(
                section=section,
                guidelines_context=guidelines_context
            )
        else:
            # Original flow without Tavily (backward compatible)
            analysis_response = await self._invoke_llm_structured(
                self.analysis_prompt,
                RigorAnalysisResponse,
                section_title=section["title"],
                content=section["content"],
                guidelines_context=guidelines_context
            )

        if not analysis_response or not analysis_response.issues:
            logger.info("[RigorAgent] No issues found in %s", section['title'])
            return []

        logger.info("[RigorAgent] Found %d potential issues", len(analysis_response.issues))

        # Step 3: Self-reflection with structured output
        reflection_response = await self._invoke_llm_structured(
            self.reflection_prompt,
            RigorReflectionResponse,
            section_title=section["title"],
            content=section["content"][:1000],  # Truncate for reflection
            suggestions_count=len(analysis_response.issues)
        )

        if not reflection_response:
            logger.warning("[RigorAgent] Reflection failed, using original suggestions")
            validated_issues = analysis_response.issues
            reasoning = "Reflection failed, using all original suggestions"
        else:
            validated_issues = reflection_response.validated_suggestions
            reasoning = reflection_response.reasoning
            logger.info("[RigorAgent] Reflection: %s", reasoning)

        # Step 4: Convert to standardized suggestions
        suggestions = []
        for issue in validated_issues:
            suggestion = self._create_suggestion(
                suggestion_type="rigor",
                severity=issue.severity.value,
                title="Rigor Issue",
                description=issue.issue,
                section=section["title"],
                line_start=section.get("line_start"),
                line_end=section.get("line_end"),
                suggested_fix=issue.suggestion
            )
            suggestions.append(suggestion)

        logger.info("[RigorAgent] Validated %d suggestions for %s", len(suggestions), section['title'])
        return suggestions

    async def _analyze_with_tavily(
        self,
        section: Dict[str, Any],
        guidelines_context: str
    ) -> Optional[RigorAnalysisResponse]:
        """
        Analyze section with Tavily tool calling enabled.

        This method implements a multi-step agentic workflow:
        1. LLM analyzes section with Tavily tool available
        2. If LLM requests Tavily search, execute it
        3. LLM re-analyzes with search results to produce final structured output

        Args:
            section: Section dictionary
            guidelines_context: RAG guidelines context

        Returns:
            RigorAnalysisResponse with validated issues
        """
        from langchain_core.prompts import ChatPromptTemplate

        # Step 1: Invoke LLM with Tavily tool available
        logger.info("[RigorAgent] Step 1: Initial analysis with Tavily tool available")

        response, tool_calls = await self._invoke_llm_with_tools(
            self.analysis_prompt,
            tools=[self.tavily_tool],
            section_title=section["title"],
            content=section["content"],
            guidelines_context=guidelines_context
        )

        # Step 2: If LLM requested tool calls, execute them
        if tool_calls:
            # Apply rate limiting: max calls per section
            from app.config import settings
            max_calls = settings.tavily_max_calls_per_section

            if len(tool_calls) > max_calls:
                logger.warning(
                    f"[RigorAgent] LLM requested {len(tool_calls)} tool calls, "
                    f"limiting to {max_calls} per section (rate limit)"
                )
                tool_calls = tool_calls[:max_calls]

            logger.info(
                f"[RigorAgent] Step 2: Executing {len(tool_calls)} tool call(s)"
            )

            # Execute all tool calls and collect results
            tool_messages = []
            for tool_call in tool_calls:
                try:
                    # Extract tool name and arguments
                    tool_name = tool_call.get('name')
                    tool_args = tool_call.get('args', {})

                    logger.info(
                        f"[RigorAgent] Calling tool '{tool_name}' with args: {tool_args}"
                    )

                    # Execute the tool (Tavily search)
                    tool_result = await self.tavily_tool.ainvoke(tool_args)

                    # Create tool message for context
                    tool_messages.append(
                        ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_call.get('id', 'unknown')
                        )
                    )

                    logger.info(
                        f"[RigorAgent] Tool '{tool_name}' returned "
                        f"{len(str(tool_result))} chars"
                    )

                except Exception as e:
                    logger.error(f"[RigorAgent] Tool execution error: {e}")
                    tool_messages.append(
                        ToolMessage(
                            content=f"Error: {str(e)}",
                            tool_call_id=tool_call.get('id', 'unknown')
                        )
                    )

            # Step 3: Re-invoke LLM with tool results to get structured response
            logger.info(
                "[RigorAgent] Step 3: Generating structured response with tool results"
            )

            # Create follow-up prompt with tool results
            followup_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert in experimental design and mathematical rigor.

You have just searched for best practices and now have authoritative information.

Use this information to provide a rigorous analysis of the section, focusing on:
1. Statistical method appropriateness
2. Experimental design standards
3. Sample size requirements
4. Mathematical proof validity

When you cite information from the search results, mention the source URL in your issue description.

Return a structured response with all rigor issues found."""),
                ("user", """**Section**: {section_title}

**Content**:
{content}

**Retrieved Best Practices**:
{tool_results}

**Internal Guidelines**:
{guidelines_context}

Now provide your final rigor analysis in the structured format.""")
            ])

            # Combine tool results
            tool_results_text = "\n\n".join([msg.content for msg in tool_messages])

            # Get structured response
            analysis_response = await self._invoke_llm_structured(
                followup_prompt,
                RigorAnalysisResponse,
                section_title=section["title"],
                content=section["content"],
                tool_results=tool_results_text,
                guidelines_context=guidelines_context
            )

            return analysis_response

        else:
            # No tool calls - LLM didn't need external validation
            logger.info(
                "[RigorAgent] No tool calls requested - using LLM knowledge only"
            )

            # Get structured response directly
            analysis_response = await self._invoke_llm_structured(
                self.analysis_prompt,
                RigorAnalysisResponse,
                section_title=section["title"],
                content=section["content"],
                guidelines_context=guidelines_context
            )

            return analysis_response
