"""Custom Qdrant retriever extending LangChain's BaseRetriever."""
from typing import List, Optional
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from langchain_core.callbacks import (
    CallbackManagerForRetrieverRun,
    AsyncCallbackManagerForRetrieverRun,
)
from pydantic import Field
import logging

from app.services.vector_store import VectorStoreService
from app.models.schemas import DocType

logger = logging.getLogger(__name__)


class QdrantRetriever(BaseRetriever):
    """
    Custom retriever that wraps VectorStoreService for LangChain compatibility.

    This retriever extends LangChain's BaseRetriever to provide seamless integration
    with the LangChain ecosystem while using our existing Qdrant vector store.

    Attributes:
        vector_store: VectorStoreService instance for accessing Qdrant
        k: Number of documents to retrieve
        doc_type: Optional document type filter (CLARITY, RIGOR, INTEGRITY, GENERAL)
    """

    vector_store: VectorStoreService = Field(...)
    k: int = Field(default=5, description="Number of documents to retrieve")
    doc_type: Optional[DocType] = Field(default=None, description="Filter by document type")

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        """
        Sync implementation (calls async version).

        Args:
            query: Query text
            run_manager: Callback manager for retriever run

        Returns:
            List of LangChain Document objects
        """
        import asyncio

        # Run the async implementation
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, this shouldn't happen
            # but we handle it gracefully
            raise RuntimeError(
                "Sync retrieval called from async context. "
                "Use ainvoke() instead of invoke()."
            )
        return asyncio.run(self._aget_relevant_documents(query, run_manager=run_manager))

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: AsyncCallbackManagerForRetrieverRun,
    ) -> List[Document]:
        """
        Async implementation - retrieve documents from Qdrant.

        This is the main implementation that performs the actual retrieval
        from the Qdrant vector store.

        Args:
            query: Query text
            run_manager: Async callback manager for retriever run

        Returns:
            List of LangChain Document objects
        """
        try:
            # Retrieve from Qdrant using VectorStoreService
            results = await self.vector_store.similarity_search(
                query=query,
                k=self.k,
                doc_type=self.doc_type
            )

            # Convert to LangChain Document format
            documents = []
            for result in results:
                doc = Document(
                    page_content=result["text"],
                    metadata={
                        "score": result["score"],
                        **result["metadata"]
                    }
                )
                documents.append(doc)

            logger.info(
                f"QdrantRetriever: Retrieved {len(documents)} documents "
                f"(k={self.k}, doc_type={self.doc_type})"
            )

            return documents

        except Exception as e:
            logger.error(f"QdrantRetriever: Error retrieving documents: {e}")
            return []
