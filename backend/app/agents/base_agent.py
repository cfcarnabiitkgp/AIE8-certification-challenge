"""Base agent class for all reviewer agents."""
from abc import abstractmethod
import logging
import json
import uuid
from typing import Dict, Any, Optional, Type, TypeVar

from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseReviewerAgent:
    """
    Base class for all reviewer agents.

    Provides common functionality:
    - LLM initialization
    - Structured output generation
    - Error handling
    - Logging
    """

    def __init__(
        self,
        agent_name: str,
        agent_description: str,
        temperature: float = None,
        model: str = None
    ):
        """
        Initialize base reviewer agent.

        Args:
            agent_name: Unique name for this agent
            agent_description: Brief description of agent's role
            temperature: LLM temperature (uses config default if None)
            model: LLM model name (uses config default if None)
        """
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.model = model or settings.llm_model
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=temperature or settings.llm_temperature,
            openai_api_key=settings.openai_api_key
        )
        logger.info(f"Initialized {self.agent_name} with model {self.model}")

    def _create_suggestion(
        self,
        suggestion_type: str,
        severity: str,
        title: str,
        description: str,
        section: str,
        line_start: Optional[int] = None,
        line_end: Optional[int] = None,
        suggested_fix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized suggestion object.

        Args:
            suggestion_type: Type of suggestion (clarity, rigor, etc.)
            severity: Severity level (info, warning, error)
            title: Short title
            description: Detailed description
            section: Section name
            line_start: Starting line number
            line_end: Ending line number
            suggested_fix: Suggested improvement

        Returns:
            Standardized suggestion dictionary
        """
        return {
            "id": str(uuid.uuid4()),
            "type": suggestion_type,
            "severity": severity,
            "title": title,
            "description": description,
            "section": section,
            "line_start": line_start,
            "line_end": line_end,
            "suggested_fix": suggested_fix,
            "references": []
        }

    async def _invoke_llm(
        self,
        prompt: ChatPromptTemplate,
        **kwargs
    ) -> Optional[str]:
        """
        Invoke LLM with error handling.

        Args:
            prompt: ChatPromptTemplate to use
            **kwargs: Variables to format the prompt

        Returns:
            LLM response content or None on error
        """
        try:
            response = await self.llm.ainvoke(prompt.format_messages(**kwargs))
            return response.content
        except Exception as e:
            logger.error(f"{self.agent_name} LLM invocation error: {e}")
            return None

    async def _invoke_llm_structured(
        self,
        prompt: ChatPromptTemplate,
        response_model: Type[T],
        **kwargs
    ) -> Optional[T]:
        """
        Invoke LLM with structured output using Pydantic model.

        Args:
            prompt: ChatPromptTemplate to use
            response_model: Pydantic model class for structured output
            **kwargs: Variables to format the prompt

        Returns:
            Pydantic model instance or None on error
        """
        try:
            # Use with_structured_output for enforced schema
            structured_llm = self.llm.with_structured_output(response_model)
            response = await structured_llm.ainvoke(prompt.format_messages(**kwargs))
            return response
        except Exception as e:
            logger.error(f"{self.agent_name} Structured LLM invocation error: {e}")
            return None

    def _parse_json_response(
        self,
        response_content: str,
        fallback: Any = None
    ) -> Any:
        """
        Parse JSON response with fallback.

        Args:
            response_content: JSON string to parse
            fallback: Value to return on parse error

        Returns:
            Parsed JSON or fallback value
        """
        if not response_content:
            return fallback if fallback is not None else []

        try:
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            logger.warning(f"{self.agent_name} JSON parse error: {e}")
            return fallback if fallback is not None else []

    async def analyze(self, **kwargs) -> list:
        """
        Main analysis method - to be implemented by subclasses.

        Returns:
            List of suggestion dictionaries
        """
        raise NotImplementedError("Subclasses must implement analyze()")
