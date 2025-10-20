"""Test script to compare different retriever types."""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.vector_store import VectorStoreService
from app.retrievers.registry import RetrieverRegistry
from app.retrievers.config_helper import RetrieverConfigHelper
from app.retrievers.builders import *  # Auto-register all builders
from app.models.schemas import DocType
from app.config import settings


async def test_naive_retriever():
    """Test naive retriever (direct similarity search)."""
    print("=" * 80)
    print("TESTING NAIVE RETRIEVER")
    print("=" * 80)

    vector_store = VectorStoreService()

    # Get config using helper
    config = RetrieverConfigHelper.get_agent_retriever_config("clarity", DocType.CLARITY)

    # Create retriever
    retriever = RetrieverRegistry.create(
        retriever_type="naive",
        vector_store=vector_store,
        config=config
    )

    # Test query
    test_query = "What are the guidelines for clear and concise writing?"

    print(f"\nQuery: {test_query}")
    print(f"Config: {config}\n")

    try:
        docs = await retriever.ainvoke(test_query)

        print(f"Retrieved {len(docs)} documents:")
        for i, doc in enumerate(docs, 1):
            print(f"\n[{i}] Score: {doc.metadata.get('score', 'N/A'):.4f}")
            print(f"    Text: {doc.page_content[:200]}...")
            print(f"    Metadata: {doc.metadata.get('source', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 80 + "\n")


async def test_cohere_rerank_retriever():
    """Test Cohere rerank retriever (two-stage retrieval)."""
    print("=" * 80)
    print("TESTING COHERE RERANK RETRIEVER")
    print("=" * 80)

    # Check if API key is set
    if not settings.cohere_api_key:
        print("\nSkipping Cohere rerank test - COHERE_API_KEY not set")
        print("Set COHERE_API_KEY in .env to test rerank retriever")
        print("\n" + "=" * 80 + "\n")
        return

    vector_store = VectorStoreService()

    # Create custom config for rerank
    config = {
        "k": 3,
        "initial_k": 10,
        "model": settings.cohere_rerank_model,
        "cohere_api_key": settings.cohere_api_key,
        "doc_type": DocType.CLARITY
    }

    # Create retriever
    try:
        retriever = RetrieverRegistry.create(
            retriever_type="cohere_rerank",
            vector_store=vector_store,
            config=config
        )

        # Test query
        test_query = "What are the guidelines for clear and concise writing?"

        print(f"\nQuery: {test_query}")
        print(f"Config: k={config['k']}, initial_k={config['initial_k']}, model={config['model']}\n")

        docs = await retriever.ainvoke(test_query)

        print(f"Retrieved {len(docs)} reranked documents:")
        for i, doc in enumerate(docs, 1):
            print(f"\n[{i}] Relevance Score: {doc.metadata.get('relevance_score', 'N/A')}")
            print(f"    Text: {doc.page_content[:200]}...")
            print(f"    Metadata: {doc.metadata.get('source', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80 + "\n")


async def test_registry_info():
    """Display registry information."""
    print("=" * 80)
    print("RETRIEVER REGISTRY INFORMATION")
    print("=" * 80)

    available = RetrieverRegistry.list_available()
    print(f"\nRegistered retriever types: {available}")

    print("\nPer-agent configuration from settings:")
    for agent in ["clarity", "rigor", "integrity"]:
        retriever_type = RetrieverConfigHelper.get_agent_retriever_type(agent)
        print(f"  - {agent.capitalize()} Agent: {retriever_type}")

    print("\n" + "=" * 80 + "\n")


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "RETRIEVER SYSTEM TEST" + " " * 37 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Test registry info
    await test_registry_info()

    # Test naive retriever
    await test_naive_retriever()

    # Test Cohere rerank retriever
    await test_cohere_rerank_retriever()

    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
