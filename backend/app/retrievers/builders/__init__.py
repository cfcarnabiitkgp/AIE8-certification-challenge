"""Auto-import all retriever builders to trigger registration."""
from app.retrievers.builders.naive_builder import NaiveRetrieverBuilder
from app.retrievers.builders.cohere_rerank_builder import CohereRerankRetrieverBuilder
from app.retrievers.builders.bm25_builder import BM25RetrieverBuilder

# Add new builders here as they're created
__all__ = [
    "NaiveRetrieverBuilder",
    "CohereRerankRetrieverBuilder",
    "BM25RetrieverBuilder",
]
