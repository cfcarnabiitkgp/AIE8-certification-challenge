"""
Script to upload guideline PDFs from resources folder to vector database.

This script processes all PDFs in the resources folder and uploads them
to the Qdrant vector database with appropriate metadata based on folder structure.
"""
import asyncio
import logging
import os
from pathlib import Path

from app.services.vector_store import VectorStoreService
from app.models.schemas import DocType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def upload_all_guidelines():
    """
    Upload all PDFs from resources folder with appropriate metadata.

    Folder structure determines doc_type:
    - resources/clarity_docs/ -> DocType.CLARITY
    - resources/rigor_docs/ -> DocType.RIGOR
    - resources/integrity_docs/ -> DocType.INTEGRITY
    - resources/*.pdf -> DocType.GENERAL

    Returns:
        Dictionary with upload statistics
    """
    # Initialize vector store
    vector_store = VectorStoreService()
    logger.info("Initialized VectorStoreService")

    # Define base resources path
    base_path = Path(__file__).parent.parent / "resources"

    if not base_path.exists():
        logger.error(f"Resources folder not found at {base_path}")
        return {"error": "Resources folder not found"}

    stats = {
        "clarity": 0,
        "rigor": 0,
        "integrity": 0,
        "general": 0,
        "total": 0,
        "files_processed": []
    }

    # Upload clarity docs
    clarity_path = base_path / "clarity_docs"
    if clarity_path.exists():
        logger.info(f"Processing clarity docs from {clarity_path}")
        for pdf_file in clarity_path.glob("*.pdf"):
            try:
                logger.info(f"Uploading {pdf_file.name}...")
                count = await vector_store.process_pdf(
                    pdf_path=str(pdf_file),
                    metadata={
                        "doc_type": DocType.CLARITY.value,
                        "source": pdf_file.stem,
                        "category": "clarity_guidelines",
                        "filename": pdf_file.name
                    }
                )
                stats["clarity"] += count
                stats["total"] += count
                stats["files_processed"].append(pdf_file.name)
                logger.info(f"✓ Uploaded {count} chunks from {pdf_file.name}")
            except Exception as e:
                logger.error(f"✗ Error uploading {pdf_file.name}: {e}")

    # Upload rigor docs
    rigor_path = base_path / "rigor_docs"
    if rigor_path.exists():
        logger.info(f"Processing rigor docs from {rigor_path}")
        for pdf_file in rigor_path.glob("*.pdf"):
            try:
                logger.info(f"Uploading {pdf_file.name}...")
                count = await vector_store.process_pdf(
                    pdf_path=str(pdf_file),
                    metadata={
                        "doc_type": DocType.RIGOR.value,
                        "source": pdf_file.stem,
                        "category": "rigor_guidelines",
                        "filename": pdf_file.name
                    }
                )
                stats["rigor"] += count
                stats["total"] += count
                stats["files_processed"].append(pdf_file.name)
                logger.info(f"✓ Uploaded {count} chunks from {pdf_file.name}")
            except Exception as e:
                logger.error(f"✗ Error uploading {pdf_file.name}: {e}")

    # Upload integrity docs
    integrity_path = base_path / "integrity_docs"
    if integrity_path.exists():
        logger.info(f"Processing integrity docs from {integrity_path}")
        for pdf_file in integrity_path.glob("*.pdf"):
            try:
                logger.info(f"Uploading {pdf_file.name}...")
                count = await vector_store.process_pdf(
                    pdf_path=str(pdf_file),
                    metadata={
                        "doc_type": DocType.INTEGRITY.value,
                        "source": pdf_file.stem,
                        "category": "integrity_guidelines",
                        "filename": pdf_file.name
                    }
                )
                stats["integrity"] += count
                stats["total"] += count
                stats["files_processed"].append(pdf_file.name)
                logger.info(f"✓ Uploaded {count} chunks from {pdf_file.name}")
            except Exception as e:
                logger.error(f"✗ Error uploading {pdf_file.name}: {e}")

    # Upload general docs (PDFs directly in resources folder)
    logger.info(f"Processing general docs from {base_path}")
    for pdf_file in base_path.glob("*.pdf"):
        try:
            logger.info(f"Uploading {pdf_file.name}...")
            count = await vector_store.process_pdf(
                pdf_path=str(pdf_file),
                metadata={
                    "doc_type": DocType.GENERAL.value,
                    "source": pdf_file.stem,
                    "category": "general_guidelines",
                    "filename": pdf_file.name
                }
            )
            stats["general"] += count
            stats["total"] += count
            stats["files_processed"].append(pdf_file.name)
            logger.info(f"✓ Uploaded {count} chunks from {pdf_file.name}")
        except Exception as e:
            logger.error(f"✗ Error uploading {pdf_file.name}: {e}")

    # Print summary
    logger.info("\n" + "="*50)
    logger.info("UPLOAD SUMMARY")
    logger.info("="*50)
    logger.info(f"Clarity chunks:    {stats['clarity']}")
    logger.info(f"Rigor chunks:      {stats['rigor']}")
    logger.info(f"Integrity chunks:  {stats['integrity']}")
    logger.info(f"General chunks:    {stats['general']}")
    logger.info(f"Total chunks:      {stats['total']}")
    logger.info(f"Files processed:   {len(stats['files_processed'])}")
    logger.info("="*50)

    return stats


async def test_retrieval():
    """
    Test retrieval from vector database to verify upload worked.
    """
    vector_store = VectorStoreService()

    logger.info("\n" + "="*50)
    logger.info("TESTING RETRIEVAL")
    logger.info("="*50)

    # Test clarity retrieval
    logger.info("\nTesting CLARITY retrieval...")
    clarity_results = await vector_store.similarity_search(
        query="How should I define acronyms and abbreviations?",
        k=2,
        doc_type=DocType.CLARITY
    )
    logger.info(f"Found {len(clarity_results)} clarity results:")
    for i, result in enumerate(clarity_results, 1):
        logger.info(f"\n  {i}. Score: {result['score']:.3f}")
        logger.info(f"     Source: {result['metadata'].get('source', 'unknown')}")
        logger.info(f"     Text: {result['text'][:150]}...")

    # Test rigor retrieval
    logger.info("\nTesting RIGOR retrieval...")
    rigor_results = await vector_store.similarity_search(
        query="What statistical measures should I report in experiments?",
        k=2,
        doc_type=DocType.RIGOR
    )
    logger.info(f"Found {len(rigor_results)} rigor results:")
    for i, result in enumerate(rigor_results, 1):
        logger.info(f"\n  {i}. Score: {result['score']:.3f}")
        logger.info(f"     Source: {result['metadata'].get('source', 'unknown')}")
        logger.info(f"     Text: {result['text'][:150]}...")

    logger.info("\n" + "="*50)


async def main():
    """Main function to upload and test."""
    logger.info("Starting guideline upload process...\n")

    # Upload all guidelines
    stats = await upload_all_guidelines()

    if "error" not in stats and stats["total"] > 0:
        # Test retrieval if upload was successful
        await test_retrieval()
    elif stats["total"] == 0:
        logger.warning("No documents were uploaded. Check if PDF files exist in resources folder.")

    logger.info("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
