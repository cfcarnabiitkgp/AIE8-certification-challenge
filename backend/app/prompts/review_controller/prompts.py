"""Review controller (orchestrator) prompt templates."""
from langchain_core.prompts import ChatPromptTemplate


def build_validation_prompt() -> ChatPromptTemplate:
    """Build orchestrator validation prompt."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are the orchestrator for a peer review system.

Your agents (ClarityAgent and RigorAgent) have analyzed a paper and provided suggestions.
Each agent has already self-reflected on their findings.

Your task:
1. **Cross-validate**: Check for contradictions between agents
2. **Prioritize**: Identify the most important suggestions
3. **Filter**: Remove redundant or low-value suggestions
4. **Decide**: Make final decisions on what to include

Return suggestions that are:
- Non-contradictory
- Actionable and specific
- High-impact for the paper quality"""),
        ("user", """Review these suggestions from the agents:

**Clarity Suggestions ({clarity_count})**:
{clarity_suggestions}

**Rigor Suggestions ({rigor_count})**:
{rigor_suggestions}

Return a JSON object with:
- final_suggestions: Array of suggestion IDs to keep
- reasoning: Brief explanation of your decisions
- priority_order: Array of suggestion IDs in priority order

Format:
{{"final_suggestions": ["id1", "id2", ...], "reasoning": "...", "priority_order": ["id1", ...]}}""")
    ])


def build_validation_prompt_langgraph() -> ChatPromptTemplate:
    """Build orchestrator validation prompt for LangGraph (with structured output)."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are the orchestrator for a peer review system.

Your agents have analyzed a paper and provided suggestions.
Each agent has already self-reflected on their findings.

Your task:
1. **Cross-validate**: Check for contradictions between agents
2. **Prioritize**: Identify the most important suggestions
3. **Filter**: Remove redundant or low-value suggestions
4. **Decide**: Make final decisions on what to include

Return suggestions that are:
- Non-contradictory
- Actionable and specific
- High-impact for the paper quality

Return a structured response with your decisions."""),
        ("user", """Review these suggestions from the agents:

**Clarity Suggestions ({clarity_count})**:
{clarity_suggestions}

**Rigor Suggestions ({rigor_count})**:
{rigor_suggestions}

Provide your orchestrator decision with the list of suggestion IDs to keep, reasoning, and priority order.""")
    ])

