"""
Clear vector DB collections and re-upload guidelines with semantic chunking.

This script:
1. Deletes existing Qdrant collection
2. Re-uploads all PDFs using semantic chunking (configured in config.py)
3. Shows chunk statistics

Usage:
    python app/scripts/clear_and_reupload_with_semantic.py
"""
import asyncio
import logging
from pathlib import Path

from app.services.vector_store import VectorStoreService
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def clear_collection():
    """Delete the existing Qdrant collection."""
    vector_store = VectorStoreService()

    try:
        logger.info(f"Attempting to delete collection: {settings.qdrant_collection_name}")
        vector_store.client.delete_collection(collection_name=settings.qdrant_collection_name)
        logger.info(f"✓ Deleted collection: {settings.qdrant_collection_name}")
    except Exception as e:
        logger.warning(f"Could not delete collection (might not exist): {e}")

    # Recreate collection
    logger.info(f"Creating fresh collection: {settings.qdrant_collection_name}")
    vector_store._ensure_collection()
    logger.info(f"✓ Collection created successfully")


async def main():
    """Main workflow."""
    logger.info("="*70)
    logger.info("CLEAR AND RE-UPLOAD WITH SEMANTIC CHUNKING")
    logger.info("="*70)

    logger.info(f"\nChunking strategy: {settings.chunking_strategy}")

    if settings.chunking_strategy != "semantic":
        logger.warning("\n⚠️  WARNING: chunking_strategy is not set to 'semantic' in config.py!")
        logger.warning("Current strategy: %s", settings.chunking_strategy)
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            logger.info("Aborted.")
            return

    # Step 1: Clear existing collection
    logger.info("\n" + "="*70)
    logger.info("STEP 1: Clear Existing Collection")
    logger.info("="*70)
    await clear_collection()

    # Step 2: Re-upload with semantic chunking
    logger.info("\n" + "="*70)
    logger.info("STEP 2: Re-upload Guidelines with Semantic Chunking")
    logger.info("="*70)

    # Import and run the upload script
    from app.scripts.upload_guidelines import upload_all_guidelines
    stats = await upload_all_guidelines()

    # Summary
    logger.info("\n" + "="*70)
    logger.info("✅ COMPLETE!")
    logger.info("="*70)
    logger.info(f"Total chunks uploaded: {stats['total']}")
    logger.info(f"Chunking strategy: {settings.chunking_strategy}")

    if settings.chunking_strategy == "semantic":
        logger.info(f"Semantic config:")
        logger.info(f"  - Breakpoint type: {settings.semantic_breakpoint_threshold_type}")
        logger.info(f"  - Threshold: {settings.semantic_breakpoint_threshold_amount}")
        logger.info(f"  - Min chunk size: {settings.semantic_min_chunk_size}")
        logger.info(f"  - Max chunk size: {settings.semantic_max_chunk_size}")

    logger.info("\n" + "="*70)
    logger.info("NEXT STEPS:")
    logger.info("="*70)
    logger.info("1. Recreate golden datasets:")
    logger.info("   python eval/update_golden_with_real_contexts.py --evaluator both")
    logger.info("")
    logger.info("2. Run evaluation:")
    logger.info("   python eval/evaluate_rag_performance.py --evaluator both")
    logger.info("")
    logger.info("3. Compare with previous results to see if context precision improved!")


if __name__ == "__main__":
    asyncio.run(main())
