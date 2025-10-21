# LangGraph Peer Review Architecture

## Overview

This implementation uses **LangGraph's StateGraph** with **Pydantic BaseModel** for state management. Inspired by the [Rigorous Repository](https://github.com/Agentic-Systems-Lab/rigorous), it provides a clean, graph-based workflow for peer review.

### Key Principles

1. **StateGraph Workflow**: Explicit state management with LangGraph
2. **Section-wise Analysis**: Each section analyzed independently in a loop
3. **Specialized Agents**: Focused agents for clarity and rigor
4. **Orchestrator Validation**: Final cross-validation and prioritization step
5. **Type-Safe State**: Pydantic models with Annotated reducers
6. **Easy to Extend**: Add new nodes and agents to the graph

## Architecture

### LangGraph StateGraph Flow

```
┌─────────────────────────────────────────────────────────┐
│              LangGraph StateGraph Workflow               │
│                                                          │
│  START                                                   │
│    ↓                                                     │
│  [parse_sections] ─────────────────────────────────────┐│
│    Parse markdown, initialize sections                  ││
│    ↓                                                    ││
│  [analyze_section] ─────────────────────────────────┐  ││
│    Run ClarityAgent + RigorAgent concurrently        │  ││
│    ├─ Clarity: All sections                          │  ││
│    └─ Rigor: Filter by keywords (method, result...)  │  ││
│    ↓                                                 │  ││
│  [next_section] ────────────────────────────────────┤  ││
│    Increment current_section_index                   │  ││
│    ↓                                                 │  ││
│  <should_continue?> Conditional Edge                 │  ││
│    ├─ "continue" ──────────────────────────────────┘  ││
│    │   (more sections to process)                      ││
│    └─ "validate" ─────────────────────────────────────┤│
│        (all sections done)                             ││
│        ↓                                               ││
│      [validate_suggestions] ──────────────────────────┤│
│        Orchestrator cross-validation                   ││
│        - Check for contradictions                      ││
│        - Prioritize suggestions                        ││
│        - Filter redundancies                           ││
│        ↓                                               ││
│      END → Return final suggestions                    ││
└────────────────────────────────────────────────────────┘│
```

### Agent Details

```
┌──────────────────────┐     ┌────────────────────┐     ┌─────────────────────┐
│  ClarityAgent        │     │   RigorAgent       │     │ ReviewerController  │
│  (gpt-4o-mini+ReAct) │     │ (gpt-4o+ReAct+     │     │ (gpt-4o)            │
│                      │     │  Tools)            │     │                     │
│  • Unclear text      │     │ • Missing controls │     │ • Cross-validate    │
│  • Vague refs        │     │ • Statistical      │     │ • Prioritize        │
│  • Undefined terms   │     │   issues           │     │ • Filter            │
│  • Complex sentences │     │ • Mathematical     │     │   contradictions    │
│                      │     │   rigor            │     │ • Remove            │
│  All sections        │     │ Filtered sections  │     │   redundancies      │
│  Uses RAG retrieval  │     │ Uses RAG + Tavily  │     │                     │
└──────────────────────┘     └────────────────────┘     └─────────────────────┘
```

## Directory Structure

```
backend/app/
├── agents/
│   ├── base_agent.py                  # Abstract base class for agents
│   ├── review_controller_langgraph.py # ⭐ LangGraph StateGraph workflow
│   ├── review_controller.py           # Legacy simple controller
│   │
│   ├── section/                       # Section parsing utilities
│   │   ├── __init__.py
│   │   └── section_analyzer.py        # Markdown parser, truncation
│   │
│   ├── clarity/                       # Clarity agent module
│   │   ├── __init__.py
│   │   └── clarity_agent.py           # Writing clarity checks
│   │
│   └── rigor/                         # Rigor agent module
│       ├── __init__.py
│       └── rigor_agent.py             # Experimental/math rigor checks
│
├── retrievers/                        # RAG retrieval strategies
│   ├── registry.py                    # RetrieverRegistry (Singleton)
│   ├── config_helper.py               # Configuration helpers
│   ├── builders.py                    # Builder classes
│   ├── naive.py                       # Vector similarity retriever
│   ├── bm25.py                        # Hybrid BM25 + vector retriever
│   └── cohere_rerank.py               # Cohere reranking retriever
│
├── prompts/                           # Prompt templates
│   ├── clarity_agent/
│   │   └── prompts.py                 # Clarity prompts
│   ├── rigor_agent/
│   │   └── prompts.py                 # Rigor prompts
│   └── review_controller/
│       └── prompts.py                 # Orchestrator prompts
│
├── services/                          # External services
│   ├── vector_store.py                # Qdrant integration
│   └── tavily_service.py              # Tavily web search
│
└── models/
    ├── __init__.py
    └── schemas.py                     # Pydantic models for state, requests
```

## Core Components

### 1. LangGraph StateGraph (`review_controller_langgraph.py`) ⭐

The main orchestrator using LangGraph's StateGraph:

```python
class LangGraphReviewController:
    def __init__(self):
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(ReviewState)

        # Add nodes
        workflow.add_node("parse_sections", self._parse_sections_node)
        workflow.add_node("analyze_section", self._analyze_section_node)
        workflow.add_node("next_section", self._next_section_node)
        workflow.add_node("validate_suggestions", self._validate_suggestions_node)

        # Set entry and edges
        workflow.set_entry_point("parse_sections")
        workflow.add_edge("parse_sections", "analyze_section")
        workflow.add_edge("analyze_section", "next_section")

        # Conditional edge
        workflow.add_conditional_edges(
            "next_section",
            self._should_continue,
            {"continue": "analyze_section", "validate": "validate_suggestions"}
        )

        workflow.add_edge("validate_suggestions", END)
        return workflow.compile()

    async def review(self, content, session_id, target_venue=None):
        initial_state = ReviewState(...)
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state
```

### 2. ReviewState (`models/schemas.py`)

Pydantic BaseModel for state management:

```python
from typing_extensions import Annotated
import operator

class ReviewState(BaseModel):
    # Input
    content: str
    session_id: str
    target_venue: Optional[str] = None

    # Parsed
    sections: List[Section] = []
    current_section_index: int = 0

    # Accumulated suggestions (using Annotated reducer)
    clarity_suggestions: Annotated[List[Suggestion], operator.add] = []
    rigor_suggestions: Annotated[List[Suggestion], operator.add] = []

    # Output
    all_suggestions: List[Suggestion] = []
    processing_complete: bool = False
```

**Key Feature**: `Annotated[List[Suggestion], operator.add]` tells LangGraph to automatically accumulate suggestions across node updates.

### 3. BaseReviewerAgent (`base_agent.py`)

Abstract base class for agents:

```python
class BaseReviewerAgent:
    def __init__(self, agent_name, agent_description)
    async def analyze(self, section_dict: Dict) -> List[Dict]  # Implement in subclass

    # Helper methods:
    def _create_suggestion(...)
    async def _invoke_llm(...)
    def _parse_json_response(...)
```

### 4. SectionAnalyzer (`section/section_analyzer.py`)

Static utilities for section parsing:

```python
class SectionAnalyzer:
    @staticmethod
    def parse_markdown(content: str) -> List[Section]
        # Returns Pydantic Section models

    @staticmethod
    def filter_sections_by_keywords(sections, keywords) -> List[Section]

    @staticmethod
    def get_section_summary(sections) -> str

    @staticmethod
    def truncate_section_content(section: Section, max_tokens=2000) -> Section
        # Returns truncated Section model
```

### 5. ClarityAgent (`clarity/clarity_agent.py`)

Analyzes writing clarity:

```python
class ClarityAgent(BaseReviewerAgent):
    async def analyze(self, section: Dict) -> list

    # Checks:
    # - Unclear/ambiguous statements
    # - Complex sentence structures
    # - Undefined jargon/acronyms
    # - Vague references
    # - Missing definitions
```

### 6. RigorAgent (`rigor/rigor_agent.py`)

Analyzes experimental and mathematical rigor:

```python
class RigorAgent(BaseReviewerAgent):
    async def analyze(self, section: Dict) -> List[Dict]

    # Checks:
    # - Missing control experiments
    # - Statistical test appropriateness
    # - Sample sizes, confidence intervals
    # - Mathematical proofs and assumptions
    # - Experimental setup clarity
```

**Smart Filtering**: Only analyzes relevant sections using keyword matching (method, experiment, result, proof, etc.).

**Tavily Integration**: Uses web search to find recent best practices and validate claims.

### 7. Retrieval Layer (`retrievers/`)

Flexible RAG implementation with multiple retrieval strategies:

```python
# Registry pattern for managing retrievers
class RetrieverRegistry:
    @classmethod
    def create(cls, retriever_type: str, vector_store, config) -> BaseRetriever

    # Available types:
    # - "naive": Vector similarity search
    # - "bm25": Hybrid BM25 + vector search
    # - "cohere_rerank": Cohere reranking
```

**Retriever Strategies:**

1. **NaiveRetriever**: Simple vector similarity using embeddings
2. **BM25Retriever**: Hybrid approach combining keyword matching (BM25) and semantic search
3. **CohereRerankRetriever**: Uses Cohere's reranking API for improved relevance

**Configuration**: Each agent can use a different retriever strategy via `config.py`.

## StateGraph Workflow Details

### Node Functions

#### `_parse_sections_node(state: ReviewState) -> Dict`
- Parses markdown content into Section models
- Initializes `sections` list and `current_section_index`
- Returns state update dict

#### `_analyze_section_node(state: ReviewState) -> Dict`
- Gets current section from `state.sections[state.current_section_index]`
- Truncates section to 2000 tokens max
- Runs ClarityAgent and RigorAgent concurrently with `asyncio.gather()`
- Converts results to Suggestion Pydantic models
- Returns updates for `clarity_suggestions` and `rigor_suggestions`
- LangGraph automatically accumulates using `operator.add` reducer

#### `_next_section_node(state: ReviewState) -> Dict`
- Increments `current_section_index`
- Returns state update

#### `_should_continue(state: ReviewState) -> str`
- Conditional edge function
- Returns `"continue"` if more sections to process
- Returns `"validate"` if all sections done

#### `_validate_suggestions_node(state: ReviewState) -> Dict`
- Orchestrator validation with LLM
- Uses structured output with `OrchestratorDecision` Pydantic model
- Cross-validates clarity and rigor suggestions
- Filters contradictions and redundancies
- Prioritizes important suggestions
- Returns `all_suggestions` and `processing_complete=True`
- Graceful fallback if validation fails

## Key Advantages

### 1. Explicit State Management
- **Type-safe state**: Pydantic BaseModel validation
- **Automatic accumulation**: Annotated reducers handle list merging
- **Clear state transitions**: Explicit node returns
- **Debug visibility**: State logging at each node

### 2. Graph-Based Workflow
- **Visual workflow**: Can be visualized with LangGraph tools
- **Conditional branching**: `should_continue` for dynamic flow
- **Easy to extend**: Add nodes and edges to the graph
- **Reusable patterns**: StateGraph template for other workflows

### 3. Speed & Efficiency
- **Concurrent agents**: Clarity + Rigor run in parallel per section
- **Smart filtering**: RigorAgent skips ~40% of sections
- **Section looping**: Efficient graph-based iteration
- **Target: 5-10 seconds** for typical papers

### 4. Orchestrator Validation
- **Cross-validation**: Checks for agent contradictions
- **Prioritization**: Orders suggestions by importance
- **Quality filtering**: Removes redundancies and low-value items
- **Structured output**: Type-safe orchestrator decisions

## Usage

### Via API

```bash
# LangGraph workflow (default)
curl -X POST "http://localhost:8000/api/review/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "# Paper\n\n## Abstract\n\nText...",
    "session_id": "123",
    "target_venue": "NeurIPS"
  }'
```

### Via Python

```python
from app.agents.review_controller_langgraph import LangGraphReviewController

controller = LangGraphReviewController()

result = await controller.review(
    content=paper_markdown,
    session_id="session_123",
    target_venue="NeurIPS"
)

print(f"Found {len(result['suggestions'])} final suggestions")
print(f"Analyzed {result['metadata']['total_sections']} sections")
print(f"Clarity: {result['metadata']['clarity_suggestions']}")
print(f"Rigor: {result['metadata']['rigor_suggestions']}")
```

### Via Test Script

```bash
cd backend
python test_langgraph.py
```

## Extending the System

### Adding a New Agent to the Graph

1. **Create agent module**:
```python
# app/agents/citation/citation_agent.py
from app.agents.base_agent import BaseReviewerAgent

class CitationAgent(BaseReviewerAgent):
    def __init__(self):
        super().__init__(
            agent_name="CitationAgent",
            agent_description="Validates citations and references"
        )
        self.prompt = self._build_prompt()

    async def analyze(self, section: Dict) -> List[Dict]:
        # Implement citation analysis
        pass
```

2. **Update ReviewState** to include new agent suggestions:
```python
# app/models/schemas.py
class ReviewState(BaseModel):
    # ... existing fields ...
    citation_suggestions: Annotated[List[Suggestion], operator.add] = []
```

3. **Add to LangGraph workflow**:
```python
# app/agents/review_controller_langgraph.py
class LangGraphReviewController:
    def __init__(self):
        self.citation_agent = CitationAgent()  # Add agent
        # ...

    async def _analyze_section_node(self, state: ReviewState):
        # Update to include citation agent
        clarity, rigor, citation = await asyncio.gather(
            self.clarity_agent.analyze(section_dict),
            self.rigor_agent.analyze(section_dict),
            self.citation_agent.analyze(section_dict)  # Add
        )

        return {
            "clarity_suggestions": [Suggestion(**s) for s in clarity],
            "rigor_suggestions": [Suggestion(**s) for s in rigor],
            "citation_suggestions": [Suggestion(**s) for s in citation]  # Add
        }

    async def _validate_suggestions_node(self, state: ReviewState):
        # Include citation suggestions in orchestrator
        all_suggestions = (
            state.clarity_suggestions +
            state.rigor_suggestions +
            state.citation_suggestions  # Add
        )
        # ... rest of validation
```

4. **Test it**:
```bash
python test_langgraph.py
```

## Architecture Benefits

| Aspect | LangGraph StateGraph | Legacy Simple Controller |
|--------|---------------------|--------------------------|
| **State Management** | Type-safe Pydantic + Annotated reducers | Manual dict merging |
| **Workflow Visualization** | Can be graphed with LangGraph tools | No visualization |
| **Conditional Logic** | Built-in conditional edges | Manual if/else |
| **Extensibility** | Add nodes/edges to graph | Modify linear function |
| **Orchestration** | Final validation node | No orchestration |
| **Debugging** | State logged at each node | Limited visibility |
| **Agents** | 2 agents + orchestrator | 2 agents only |
| **Speed** | 5-10s | 7-15s |
| **Code Lines** | ~370 lines | ~300 lines |

## Implementation Details

### LangGraph Compilation

The workflow is compiled at initialization:

```python
self.workflow = workflow.compile()
```

This creates an executable graph that can be invoked with:

```python
final_state = await self.workflow.ainvoke(initial_state)
```

### State Updates

Each node returns a dict with updates:

```python
return {
    "clarity_suggestions": [suggestion1, suggestion2],
    "current_section_index": idx + 1
}
```

LangGraph merges these with the current state using the defined reducers (e.g., `operator.add` for lists).

### Logging

All nodes use `[LangGraph]` prefix for easy log filtering:

```python
logger.info("[LangGraph] Node: parse_sections")
logger.info(f"[LangGraph] Parsed {len(sections)} sections")
```

This makes debugging workflow execution straightforward.

## Testing

```bash
# Test LangGraph workflow
cd backend
python test_langgraph.py

# Expected output:
# [LangGraph] Starting review...
# [LangGraph] Node: parse_sections
# [LangGraph] Parsed 5 sections
# [LangGraph] Node: analyze_section - Abstract (1/5)
# [LangGraph] Section analysis: 3 clarity, 2 rigor
# [LangGraph] Node: next_section
# [LangGraph] Conditional: continue - 1/5
# ... (continues for all sections)
# [LangGraph] Conditional: validate - all sections processed
# [LangGraph] Node: validate_suggestions
# [LangGraph] Orchestrator reasoning: ...
# [LangGraph] Keeping 12/15 suggestions
# [LangGraph] Review complete: 12 final suggestions
#
# Processing time: 7-10s
# Total sections: 5
# Clarity suggestions: 8
# Rigor suggestions: 7
# Final suggestions: 12 (after orchestrator)
```

---

**Framework**: LangGraph StateGraph with Pydantic BaseModel

**Default workflow**: LangGraph (recommended)
