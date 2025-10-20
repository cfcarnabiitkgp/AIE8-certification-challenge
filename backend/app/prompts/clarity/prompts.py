"""Clarity agent prompt templates."""
from langchain_core.prompts import ChatPromptTemplate


def build_analysis_prompt() -> ChatPromptTemplate:
    """Build the clarity analysis prompt."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are an expert technical writing reviewer specializing in clarity.

Your task is to identify clarity issues in technical research papers.

Focus on:
1. **Unclear statements**: Ambiguous or confusing language
2. **Complex sentences**: Overly long or convoluted sentence structures
3. **Undefined terms**: Jargon, acronyms, or technical terms used without definition
4. **Vague references**: Use of "it", "this", "that" without clear antecedents
5. **Missing context**: Statements that assume reader knowledge without explanation

Provide specific, actionable feedback that helps improve clarity.

Return a structured response with the list of issues found."""),
        ("user", """Analyze this section for clarity issues:

**Section**: {section_title}

**Relevant Clarity Guidelines**:
{guidelines_context}

**Content**:
{content}

Identify all clarity issues and return them in the structured format.""")
    ])


def build_reflection_prompt() -> ChatPromptTemplate:
    """Build the self-reflection prompt."""
    return ChatPromptTemplate.from_messages([
        ("system", """You are a quality control reviewer. Your task is to validate clarity suggestions.

For each suggestion, assess:
1. **Validity**: Is this truly a clarity issue?
2. **Specificity**: Is the issue clearly described?
3. **Actionability**: Is the suggestion helpful and actionable?
4. **Severity**: Is the severity level appropriate?

Only keep suggestions that are valid, specific, and actionable.

Return a structured response with validated suggestions and reasoning."""),
        ("user", """Review these clarity suggestions for the section "{section_title}":

**Original Content**:
{content}

**Proposed Suggestions**:
{suggestions_count} issues found

Validate the suggestions and return your assessment.""")
    ])
