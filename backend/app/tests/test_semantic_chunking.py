"""
Quick test to verify semantic chunking is working.

This script tests semantic chunking on a sample text without uploading to vector DB.
"""
import logging
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample text with distinct semantic sections
SAMPLE_TEXT = """
Introduction to Writing Clarity

Writing clarity is essential for effective scientific communication. Clear writing ensures that readers can easily understand and replicate research findings. This section provides guidelines for improving clarity in research papers.

Defining Technical Terms

All technical terms and acronyms must be defined upon first use. For example, when introducing "Machine Learning (ML)", always spell out the full term before using the abbreviation. This helps readers who may be unfamiliar with specialized terminology.

Consistency is also important. Once you've defined a term, use it consistently throughout the paper. Avoid switching between synonyms as this can confuse readers.

Sentence Structure

Use clear, concise sentences. Avoid overly complex sentence structures with multiple nested clauses. Each sentence should convey one main idea.

Active voice is generally preferred over passive voice. For example, write "We conducted experiments" rather than "Experiments were conducted." Active voice makes it clear who performed the action.

Paragraph Organization

Each paragraph should have a clear topic sentence. Supporting sentences should develop that topic. Avoid paragraph-long walls of text.

Use transition words to connect ideas between paragraphs. Words like "however," "moreover," and "in contrast" help guide readers through your argument.

Tables and Figures

Tables and figures should be self-contained and clearly labeled. Captions should provide enough information that readers can understand the content without referring to the main text.

Always reference tables and figures in the text before they appear. For example, "As shown in Table 1, the results indicate..."

Conclusion

Following these clarity guidelines will significantly improve the readability and impact of your research paper. Clear communication benefits both you and your readers.
"""


def test_fixed_chunking():
    """Test fixed-size chunking."""
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    logger.info("\n" + "="*70)
    logger.info("FIXED-SIZE CHUNKING TEST")
    logger.info("="*70)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )

    chunks = splitter.split_text(SAMPLE_TEXT)

    logger.info(f"\nTotal chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks, 1):
        logger.info(f"\n--- Chunk {i} ({len(chunk)} chars) ---")
        logger.info(chunk[:150] + "..." if len(chunk) > 150 else chunk)


def test_semantic_chunking():
    """Test semantic chunking."""
    logger.info("\n" + "="*70)
    logger.info("SEMANTIC CHUNKING TEST")
    logger.info("="*70)

    logger.info(f"Breakpoint type: {settings.semantic_breakpoint_threshold_type}")
    logger.info(f"Threshold: {settings.semantic_breakpoint_threshold_amount}")

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openai_api_key
    )

    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type=settings.semantic_breakpoint_threshold_type,
        breakpoint_threshold_amount=settings.semantic_breakpoint_threshold_amount,
    )

    chunks = splitter.split_text(SAMPLE_TEXT)

    logger.info(f"\nTotal chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks, 1):
        logger.info(f"\n--- Chunk {i} ({len(chunk)} chars) ---")
        # Show full chunk for semantic (they should be meaningful units)
        logger.info(chunk)


def main():
    logger.info("="*70)
    logger.info("SEMANTIC CHUNKING COMPARISON TEST")
    logger.info("="*70)
    logger.info(f"\nSample text length: {len(SAMPLE_TEXT)} chars")
    logger.info(f"Sample has 6 semantic sections (Introduction, Defining Terms, Sentence Structure, Paragraph Org, Tables/Figures, Conclusion)")

    # Test both strategies
    test_fixed_chunking()
    test_semantic_chunking()

    logger.info("\n" + "="*70)
    logger.info("ANALYSIS")
    logger.info("="*70)
    logger.info("Compare the outputs above:")
    logger.info("- Fixed chunking: Breaks at arbitrary character limits, may split mid-section")
    logger.info("- Semantic chunking: Breaks at semantic boundaries, keeps related content together")
    logger.info("")
    logger.info("For RAG, semantic chunks should improve context precision because:")
    logger.info("- Each chunk represents a complete concept/guideline")
    logger.info("- Retrieval returns coherent, actionable guidelines")
    logger.info("- Less noise from partial or mixed guidelines")


if __name__ == "__main__":
    main()

