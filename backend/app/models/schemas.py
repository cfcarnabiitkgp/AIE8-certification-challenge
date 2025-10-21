"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from enum import Enum
import operator
from typing import List, Optional, Literal, TypedDict
from typing_extensions import Annotated
from langgraph.graph import add_messages


class DocType(str, Enum):
    """Types of documents stored in vector database."""
    CLARITY = "clarity"
    RIGOR = "rigor"
    # INTEGRITY = "integrity"


class SuggestionType(str, Enum):
    """Types of suggestions the system can provide."""
    CLARITY = "clarity"
    RIGOR = "rigor"
    COHERENCE = "coherence"
    CITATION = "citation"
    BEST_PRACTICES = "best_practices"
    STRUCTURE = "structure"


class SeverityLevel(str, Enum):
    """Severity levels for suggestions."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Suggestion(BaseModel):
    """A single peer review suggestion."""

    id: str = Field(..., description="Unique identifier for the suggestion")
    type: SuggestionType = Field(..., description="Type of suggestion")
    severity: SeverityLevel = Field(..., description="Severity level")
    title: str = Field(..., description="Short title of the suggestion")
    description: str = Field(..., description="Detailed explanation")
    section: str = Field(..., description="Section where the issue was found")
    line_start: Optional[int] = Field(None, description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix if applicable")
    references: List[str] = Field(default_factory=list, description="Related references")


class ReviewRequest(BaseModel):
    """Request model for peer review."""
    content: str = Field(..., description="Markdown content to review")
    session_id: str = Field(..., description="Session identifier")
    target_venue: Optional[str] = Field(None, description="Target publication venue")
    analysis_types: List[str] = Field(default_factory=lambda: ["clarity", "rigor"], description="Types of analysis to perform")


class ReviewResponse(BaseModel):
    """Response model for peer review."""
    suggestions: List[Suggestion] = Field(..., description="List of suggestions")
    session_id: str = Field(..., description="Session identifier")
    processing_time: float = Field(..., description="Processing time in seconds")


class UploadResponse(BaseModel):
    """Response model for guideline upload."""
    message: str = Field(..., description="Status message")
    filename: str = Field(..., description="Uploaded filename")
    chunks_indexed: int = Field(..., description="Number of chunks indexed")


class Section(BaseModel):
    """A parsed section from markdown content."""

    title: str = Field(..., description="Section title/heading")
    content: str = Field(..., description="Section content (including all subsection content)")
    level: int = Field(..., description="Heading level (1-6)")
    line_start: int = Field(..., description="Starting line number in original document")
    line_end: int = Field(..., description="Ending line number in original document")
    section_number: Optional[str] = Field(None, description="Section number (e.g., '3.1.2')")
    parent_section: Optional[str] = Field(None, description="Parent section number (e.g., '3.1' for section '3.1.2')")
    subsections: List[str] = Field(default_factory=list, description="List of subsection numbers")


class ClarityIssue(BaseModel):
    """A single clarity issue identified by the agent."""
    line_hint: str = Field(..., description="Brief description of location")
    issue: str = Field(..., description="What is unclear or confusing")
    suggestion: str = Field(..., description="Specific improvement recommendation")
    severity: SeverityLevel = Field(..., description="Severity level")


class ClarityAnalysisResponse(BaseModel):
    """Structured response from clarity agent analysis."""
    issues: List[ClarityIssue] = Field(default_factory=list, description="List of clarity issues found")


class ClarityReflectionResponse(BaseModel):
    """Structured response from clarity agent self-reflection."""
    validated_suggestions: List[ClarityIssue] = Field(default_factory=list, description="Validated clarity issues")
    reasoning: str = Field(..., description="Explanation of validation decisions")


class RigorIssue(BaseModel):
    """A single rigor issue identified by the agent."""
    line_hint: str = Field(..., description="Brief description of location")
    issue: str = Field(..., description="What rigor issue was found")
    suggestion: str = Field(..., description="Specific improvement recommendation")
    severity: SeverityLevel = Field(..., description="Severity level")
    external_sources: List[str] = Field(
        default_factory=list,
        description="URLs from external searches (e.g., Tavily) that support this rigor assessment"
    )


class RigorAnalysisResponse(BaseModel):
    """Structured response from rigor agent analysis."""
    issues: List[RigorIssue] = Field(default_factory=list, description="List of rigor issues found")


class RigorReflectionResponse(BaseModel):
    """Structured response from rigor agent self-reflection."""
    validated_suggestions: List[RigorIssue] = Field(default_factory=list, description="Validated rigor issues")
    reasoning: str = Field(..., description="Explanation of validation decisions")


class OrchestratorDecision(BaseModel):
    """Structured response from orchestrator validation."""
    final_suggestions: List[str] = Field(default_factory=list, description="Array of suggestion IDs to keep")
    reasoning: str = Field(..., description="Brief explanation of decisions")
    priority_order: List[str] = Field(default_factory=list, description="Array of suggestion IDs in priority order")


class ReviewState(BaseModel):
    """LangGraph state for peer review workflow using Pydantic BaseModel."""
    # Input
    content: str = Field(default="", description="Original markdown content to review")
    session_id: str = Field(default="", description="Session identifier")
    target_venue: Optional[str] = Field(default=None, description="Target publication venue")
    analysis_types: List[str] = Field(default_factory=lambda: ["clarity", "rigor"], description="Types of analysis to perform")

    # Parsed sections
    sections: List[Section] = Field(default_factory=list, description="Parsed document sections")
    current_section_index: int = Field(default=0, description="Current section being processed")

    # Agent outputs - using Annotated with operator.add for list accumulation
    clarity_suggestions: Annotated[List[Suggestion], operator.add] = Field(
        default_factory=list,
        description="Suggestions from clarity agent"
    )
    rigor_suggestions: Annotated[List[Suggestion], operator.add] = Field(
        default_factory=list,
        description="Suggestions from rigor agent"
    )

    # Final output
    all_suggestions: List[Suggestion] = Field(default_factory=list, description="All validated suggestions")
    processing_complete: bool = Field(default=False, description="Whether processing is complete")

    class Config:
        arbitrary_types_allowed = True

