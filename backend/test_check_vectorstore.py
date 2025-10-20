"""
Script to check the contents of the Qdrant vector store.

This script verifies:
- Total number of vectors in the collection
- Number of documents per doc_type (clarity, rigor, integrity, general)
- Sample documents from each category
"""
import asyncio
from app.services.vector_store import VectorStoreService
from app.models.schemas import DocType


async def check_vectorstore():
    """Check the vector store contents and display statistics."""
    vs = VectorStoreService()

    # Get collection info
    try:
        collection_info = vs.client.get_collection(vs.collection_name)
        print(f"\n{'='*60}")
        print(f"VECTOR STORE STATUS")
        print(f"{'='*60}")
        print(f"Collection name:   {vs.collection_name}")
        print(f"Total vectors:     {collection_info.points_count}")
        print(f"Vector dimension:  {collection_info.config.params.vectors.size}")
        print(f"Distance metric:   {collection_info.config.params.vectors.distance}")
        print(f"{'='*60}\n")
    except Exception as e:
        print(f"Error accessing collection: {e}")
        print("Make sure Qdrant is running and the collection exists.")
        return

    # Test search for each doc type
    print("DOCUMENTS BY TYPE:")
    print("-" * 60)

    total_found = 0
    for doc_type in [DocType.CLARITY, DocType.RIGOR, DocType.INTEGRITY, DocType.GENERAL]:
        results = await vs.similarity_search(
            query="guidelines and requirements",
            k=5,
            doc_type=doc_type
        )
        count = len(results)
        total_found += count

        print(f"\n{doc_type.value.upper():12} {count} documents")

        if results:
            # Show sample document info
            sample = results[0]
            filename = sample['metadata'].get('filename', 'unknown')
            source = sample['metadata'].get('source', 'unknown')
            print(f"  Sample file: {filename}")
            print(f"  Source:      {source}")
            print(f"  Score:       {sample['score']:.3f}")
            print(f"  Preview:     {sample['text'][:100]}...")
        else:
            print(f"  No documents found for {doc_type.value}")

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total searchable documents: {total_found}")

    if total_found == 0:
        print("\nNo documents found!")
        print("Run 'python -m app.scripts.upload_guidelines' to upload PDFs.")
    else:
        print(f"\nVector store is ready with {total_found} documents!")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(check_vectorstore())
