"""
LangGraph-based Review Controller using Pydantic BaseModel for state management.

This implementation uses LangGraph's StateGraph to model the peer review workflow
with explicit state transitions and conditional logic.
"""
from typing import List, Dict, Any
import logging
import json

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI

from app.models.schemas import ReviewState, Suggestion, OrchestratorDecision, DocType
from app.agents.section import SectionAnalyzer
from app.agents.clarity import ClarityAgent
from app.agents.rigor import RigorAgent
from app.services.vector_store import VectorStoreService
from app.retrievers.registry import RetrieverRegistry
from app.retrievers.config_helper import RetrieverConfigHelper
from app.retrievers.builders import *  # Auto-register all builders
from app.config import settings
from app.prompts.review_controller.prompts import build_validation_prompt_langgraph

logger = logging.getLogger(__name__)


class LangGraphReviewController:
    """
    LangGraph-based orchestrator for peer review workflow.

    Uses StateGraph with Pydantic BaseModel state for:
    - Explicit state management
    - Conditional branching
    - Type-safe state transitions
    - Graph-based workflow visualization
    """

    def __init__(self):
        """Initialize the LangGraph review controller."""
        # Initialize vector store service for RAG
        self.vector_store = VectorStoreService()

        # Log available retriever types
        available_retrievers = RetrieverRegistry.list_available()
        logger.info(f"[LangGraph] Available retriever types: {available_retrievers}")

        # Create retrievers for each agent using registry pattern
        self.clarity_retriever = self._create_agent_retriever("clarity", DocType.CLARITY)
        self.rigor_retriever = self._create_agent_retriever("rigor", DocType.RIGOR)

        # Initialize Tavily tool for Rigor Agent (if enabled)
        self.tavily_tool = None
        if settings.is_tavily_enabled:
            try:
                from app.services.tavily_service import TavilyService
                tavily_service = TavilyService(
                    api_key=settings.tavily_api_key,
                    search_depth=settings.tavily_search_depth,
                    max_results=settings.tavily_max_results
                )
                self.tavily_tool = tavily_service.create_search_tool()
                logger.info("[LangGraph] Tavily search tool initialized for Rigor Agent")
            except Exception as e:
                logger.warning(f"[LangGraph] Failed to initialize Tavily: {e}")
                logger.info("[LangGraph] Rigor Agent will use LLM knowledge only")
        else:
            logger.info("[LangGraph] Tavily disabled - Rigor Agent will use LLM knowledge only")

        # Initialize components
        self.section_analyzer = SectionAnalyzer()
        self.clarity_agent = ClarityAgent(retriever=self.clarity_retriever)
        self.rigor_agent = RigorAgent(
            retriever=self.rigor_retriever,
            tavily_tool=self.tavily_tool
        )

        self.orchestrator_llm = ChatOpenAI(
            model=settings.orchestrator_model,
            temperature=0.1,
            openai_api_key=settings.openai_api_key
        )

        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
        logger.info("[LangGraph] Initialized LangGraph ReviewController with flexible retrieval support")

    def _create_agent_retriever(self, agent_name: str, doc_type: DocType):
        """
        Create retriever for a specific agent using the registry pattern.

        Args:
            agent_name: Name of the agent (e.g., "clarity", "rigor")
            doc_type: Document type to filter

        Returns:
            LangChain BaseRetriever instance
        """
        # Get retriever type and config for this agent
        retriever_type = RetrieverConfigHelper.get_agent_retriever_type(agent_name)
        config = RetrieverConfigHelper.get_agent_retriever_config(agent_name, doc_type)

        logger.info(
            f"[LangGraph] Creating {retriever_type} retriever for {agent_name} agent "
            f"(k={config.get('k')}, doc_type={doc_type})"
        )

        # Use registry to create retriever
        return RetrieverRegistry.create(
            retriever_type=retriever_type,
            vector_store=self.vector_store,
            config=config
        )

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph StateGraph for the review workflow.

        Workflow:
        1. parse_sections: Parse markdown into sections
        2. should_continue: Check if more sections to process
        3. analyze_section: Analyze current section with agents
        4. next_section: Move to next section
        5. validate_suggestions: Final orchestrator validation
        6. END: Complete
        """
        # Create StateGraph with Pydantic ReviewState
        workflow = StateGraph(ReviewState)

        # Add nodes
        workflow.add_node("parse_sections", self._parse_sections_node)
        workflow.add_node("analyze_section", self._analyze_section_node)
        workflow.add_node("next_section", self._next_section_node)
        workflow.add_node("validate_suggestions", self._validate_suggestions_node)

        # Set entry point
        workflow.set_entry_point("parse_sections")

        # Add edges
        workflow.add_edge("parse_sections", "analyze_section")
        workflow.add_edge("analyze_section", "next_section")

        # Conditional edge: continue processing or validate
        workflow.add_conditional_edges(
            "next_section",
            self._should_continue,
            {
                "continue": "analyze_section",
                "validate": "validate_suggestions"
            }
        )

        # End after validation
        workflow.add_edge("validate_suggestions", END)

        # Compile the workflow
        return workflow.compile()

    def _parse_sections_node(self, state: ReviewState) -> Dict[str, Any]:
        """
        Node: Parse markdown content into sections.

        Args:
            state: Current ReviewState

        Returns:
            State update with parsed sections
        """
        logger.info("[LangGraph] Node: parse_sections")
        sections = self.section_analyzer.parse_markdown(state.content)
        logger.info("[LangGraph] Parsed %d sections", len(sections))

        return {
            "sections": sections,
            "current_section_index": 0
        }

    async def _analyze_section_node(self, state: ReviewState) -> Dict[str, Any]:
        """
        Node: Analyze current section with clarity and rigor agents.

        Args:
            state: Current ReviewState

        Returns:
            State update with new suggestions
        """
        current_idx = state.current_section_index
        if current_idx >= len(state.sections):
            logger.warning("[LangGraph] No more sections to analyze")
            return {}

        section = state.sections[current_idx]
        logger.info("[LangGraph] Node: analyze_section - %s (%d/%d)", section.title, current_idx + 1, len(state.sections))

        # Truncate section if needed
        truncated_section = self.section_analyzer.truncate_section_content(section, max_tokens=2000)

        # Convert Section to dict for agent compatibility
        section_dict = {
            "title": truncated_section.title,
            "content": truncated_section.content,
            "level": truncated_section.level,
            "line_start": truncated_section.line_start,
            "line_end": truncated_section.line_end,
            "section_number": truncated_section.section_number,
            "parent_section": truncated_section.parent_section,
            "subsections": truncated_section.subsections
        }

        # Run agents based on selected analysis types
        import asyncio
        tasks = []

        if "clarity" in state.analysis_types:
            tasks.append(("clarity", self.clarity_agent.analyze(section_dict)))
        if "rigor" in state.analysis_types:
            tasks.append(("rigor", self.rigor_agent.analyze(section_dict)))

        # Execute selected agents
        results = {}
        if tasks:
            agent_results = await asyncio.gather(*[task[1] for task in tasks])
            for (agent_type, _), result in zip(tasks, agent_results):
                results[agent_type] = result

        # Convert dicts to Suggestion models
        clarity_models = [Suggestion(**s) for s in results.get("clarity", [])]
        rigor_models = [Suggestion(**s) for s in results.get("rigor", [])]

        # Return updates - LangGraph will merge with state using Annotated reducer
        return {
            "clarity_suggestions": clarity_models,
            "rigor_suggestions": rigor_models
        }

    def _next_section_node(self, state: ReviewState) -> Dict[str, Any]:
        """
        Node: Move to next section.

        Args:
            state: Current ReviewState

        Returns:
            State update with incremented index
        """
        next_idx = state.current_section_index + 1
        logger.info("[LangGraph] Node: next_section - moving to index %d", next_idx)

        return {
            "current_section_index": next_idx
        }

    def _should_continue(self, state: ReviewState) -> str:
        """
        Conditional edge: Determine if we should continue processing sections.

        Args:
            state: Current ReviewState

        Returns:
            "continue" if more sections, "validate" if done
        """
        if state.current_section_index < len(state.sections):
            logger.info("[LangGraph] Conditional: continue - %d/%d", state.current_section_index, len(state.sections))
            return "continue"
        else:
            logger.info("[LangGraph] Conditional: validate - all sections processed")
            return "validate"

    async def _validate_suggestions_node(self, state: ReviewState) -> Dict[str, Any]:
        """
        Node: Orchestrator validation and prioritization.

        Args:
            state: Current ReviewState

        Returns:
            State update with final validated suggestions
        """
        logger.info("[LangGraph] Node: validate_suggestions")

        all_suggestions = state.clarity_suggestions + state.rigor_suggestions
        logger.info("[LangGraph] Validating %d total suggestions", len(all_suggestions))

        # If too few, skip validation
        if len(all_suggestions) < 3:
            logger.info("[LangGraph] Too few suggestions, skipping orchestrator validation")
            return {
                "all_suggestions": all_suggestions,
                "processing_complete": True
            }

        # Prepare summaries
        clarity_summary = json.dumps([
            {
                "id": s.id,
                "section": s.section,
                "severity": s.severity.value,
                "description": s.description[:100]
            }
            for s in state.clarity_suggestions
        ], indent=2)

        rigor_summary = json.dumps([
            {
                "id": s.id,
                "section": s.section,
                "severity": s.severity.value,
                "description": s.description[:100]
            }
            for s in state.rigor_suggestions
        ], indent=2)

        # Build validation prompt
        validation_prompt = build_validation_prompt_langgraph()

        try:
            # Invoke orchestrator with structured output
            structured_llm = self.orchestrator_llm.with_structured_output(OrchestratorDecision)
            decision = await structured_llm.ainvoke(
                validation_prompt.format_messages(
                    clarity_count=len(state.clarity_suggestions),
                    rigor_count=len(state.rigor_suggestions),
                    clarity_suggestions=clarity_summary,
                    rigor_suggestions=rigor_summary
                )
            )

            # Extract decision fields
            final_ids = set(decision.final_suggestions)
            reasoning = decision.reasoning
            priority_order = decision.priority_order

            logger.info("[LangGraph] Orchestrator reasoning: %s", reasoning)
            logger.info("[LangGraph] Keeping %d/%d suggestions", len(final_ids), len(all_suggestions))

            # Filter and sort
            validated = [s for s in all_suggestions if s.id in final_ids]

            if priority_order:
                priority_map = {sid: i for i, sid in enumerate(priority_order)}
                validated.sort(key=lambda s: priority_map.get(s.id, 999))

            return {
                "all_suggestions": validated,
                "processing_complete": True
            }

        except Exception as e:
            logger.error("[LangGraph] Validation error: %s, using all suggestions", e)
            return {
                "all_suggestions": all_suggestions,
                "processing_complete": True
            }

    async def review(
        self,
        content: str,
        session_id: str,
        target_venue: str = None,
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Perform peer review using LangGraph workflow.

        Args:
            content: Markdown content
            session_id: Session identifier
            target_venue: Target publication venue (optional)

        Returns:
            Dictionary with suggestions and metadata
        """
        logger.info("[LangGraph] Starting review for session: %s", session_id)

        # Initialize state
        initial_state = ReviewState(
            content=content,
            session_id=session_id,
            target_venue=target_venue,
            analysis_types=analysis_types or ["clarity", "rigor"]
        )

        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state)

        # Convert Pydantic models to dicts for API response
        suggestions_dicts = [s.model_dump() for s in final_state["all_suggestions"]]

        logger.info("[LangGraph] Review complete: %d final suggestions", len(suggestions_dicts))

        return {
            "suggestions": suggestions_dicts,
            "session_id": session_id,
            "metadata": {
                "total_sections": len(final_state["sections"]),
                "target_venue": target_venue,
                "clarity_suggestions": len(final_state["clarity_suggestions"]),
                "rigor_suggestions": len(final_state["rigor_suggestions"]),
                "final_suggestions": len(suggestions_dicts)
            }
        }

    def get_section_structure(self, content: str) -> str:
        """
        Get a summary of the paper's section structure.

        Args:
            content: Markdown content

        Returns:
            Formatted string showing document structure
        """
        sections = self.section_analyzer.parse_markdown(content)
        return self.section_analyzer.get_section_summary(sections)
