"""Test script for BM25 retriever implementation."""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.vector_store import VectorStoreService
from app.retrievers.registry import RetrieverRegistry
from app.models.schemas import DocType
import app.retrievers.builders  # Import to trigger registration


async def test_bm25_retriever():
    """Test BM25 retriever with sample queries."""

    print("=" * 80)
    print("Testing BM25 Retriever Implementation")
    print("=" * 80)

    # Initialize vector store
    print("\n1. Initializing VectorStoreService...")
    try:
        vector_store = VectorStoreService()
        print("   ✓ VectorStoreService initialized successfully")
    except Exception as e:
        print(f"   ✗ Failed to initialize VectorStoreService: {e}")
        return

    # Check available retriever types
    print("\n2. Checking registered retriever types...")
    available_types = RetrieverRegistry.list_available()
    print(f"   Available types: {available_types}")

    if "bm25" not in available_types:
        print("   ✗ BM25 retriever not registered!")
        return
    else:
        print("   ✓ BM25 retriever is registered")

    # Create BM25 retriever
    print("\n3. Creating BM25 retriever...")
    try:
        config = {
            "k": 5,
            "doc_type": DocType.CLARITY  # Test with CLARITY type
        }
        bm25_retriever = RetrieverRegistry.create(
            "bm25",
            vector_store,
            config
        )
        print("   ✓ BM25 retriever created successfully")
    except Exception as e:
        print(f"   ✗ Failed to create BM25 retriever: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test retrieval with sample queries
    print("\n4. Testing retrieval with sample queries...")

    test_queries = [
        "What are the guidelines for writing clear research questions?",
        "How should statistical methods be reported?",
        "sample size calculation",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n   Query {i}: '{query}'")
        try:
            # Use ainvoke for async retrieval
            results = await bm25_retriever.ainvoke(query)
            print(f"   Retrieved {len(results)} documents")

            # Display first result
            if results:
                first_result = results[0]
                preview = first_result.page_content[:150].replace("\n", " ")
                print(f"   Top result preview: {preview}...")
                print(f"   Metadata: {first_result.metadata}")
            else:
                print("   No results found")
        except Exception as e:
            print(f"   ✗ Error during retrieval: {e}")
            import traceback
            traceback.print_exc()

    # Test with different doc_type
    print("\n5. Testing BM25 retriever with RIGOR doc_type...")
    try:
        config_rigor = {
            "k": 3,
            "doc_type": DocType.RIGOR
        }
        bm25_retriever_rigor = RetrieverRegistry.create(
            "bm25",
            vector_store,
            config_rigor
        )
        print("   ✓ BM25 retriever (RIGOR) created successfully")

        query = "methodology validation"
        results = await bm25_retriever_rigor.ainvoke(query)
        print(f"   Retrieved {len(results)} documents for query: '{query}'")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()

    # Test with no doc_type filter
    print("\n6. Testing BM25 retriever without doc_type filter...")
    try:
        config_all = {
            "k": 5,
            "doc_type": None
        }
        bm25_retriever_all = RetrieverRegistry.create(
            "bm25",
            vector_store,
            config_all
        )
        print("   ✓ BM25 retriever (no filter) created successfully")

        query = "research guidelines"
        results = await bm25_retriever_all.ainvoke(query)
        print(f"   Retrieved {len(results)} documents for query: '{query}'")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 80)
    print("BM25 Retriever Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_bm25_retriever())

