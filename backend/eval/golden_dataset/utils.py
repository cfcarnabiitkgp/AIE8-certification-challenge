"""
Utility functions for golden dataset generation.
"""

import json
import random
import os
import sys
from typing import List, Dict, Any
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
import glob

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from app.config import settings


def load_guideline_chunks(clarity_docs_path: str, rigor_docs_path: str) -> tuple:
    """
    Load and chunk guideline PDFs.

    Args:
        clarity_docs_path: Path to clarity guideline PDFs (glob pattern)
        rigor_docs_path: Path to rigor guideline PDFs (glob pattern)

    Returns:
        Tuple of (clarity_chunks, rigor_chunks)
    """
    guideline_docs = []

    # Load clarity PDFs
    clarity_pdfs = glob.glob(clarity_docs_path)
    for pdf_path in clarity_pdfs:
        loader = PyMuPDFLoader(pdf_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(docs)

        for chunk in chunks:
            chunk.metadata['doc_type'] = 'clarity'
            chunk.metadata['source_file'] = pdf_path

        guideline_docs.extend(chunks)

    # Load rigor PDFs
    rigor_pdfs = glob.glob(rigor_docs_path)
    for pdf_path in rigor_pdfs:
        loader = PyMuPDFLoader(pdf_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(docs)

        for chunk in chunks:
            chunk.metadata['doc_type'] = 'rigor'
            chunk.metadata['source_file'] = pdf_path

        guideline_docs.extend(chunks)

    clarity_chunks = [d for d in guideline_docs if d.metadata['doc_type'] == 'clarity']
    rigor_chunks = [d for d in guideline_docs if d.metadata['doc_type'] == 'rigor']

    return clarity_chunks, rigor_chunks


def select_diverse_guideline_chunks(chunks: List, num_chunks: int = 10) -> List:
    """
    Select diverse guideline chunks for seed generation.

    Simple approach: Sample evenly across the chunks.
    More advanced: Could use clustering or keyword-based grouping.

    Args:
        chunks: List of guideline chunks
        num_chunks: Number of chunks to select

    Returns:
        List of selected chunks
    """
    if len(chunks) <= num_chunks:
        return chunks

    step = len(chunks) // num_chunks
    selected = [chunks[i * step] for i in range(num_chunks)]

    return selected


def create_llm(task_type: str, config: Dict[str, Any]) -> ChatOpenAI:
    """
    Create an LLM instance based on task type and config.

    Args:
        task_type: One of 'seed_generation', 'evolution', 'judging'
        config: LLM configuration from config.py

    Returns:
        ChatOpenAI instance
    """
    llm_config = config.get(task_type, config['seed_generation'])

    return ChatOpenAI(
        model=llm_config['model'],
        temperature=llm_config['temperature'],
        openai_api_key=settings.openai_api_key
    )


def parse_json_response(response_text: str) -> Dict:
    """
    Parse JSON from LLM response, handling markdown code blocks.

    Args:
        response_text: Raw response from LLM

    Returns:
        Parsed JSON dict
    """
    # Remove markdown code blocks if present
    text = response_text.strip()

    if text.startswith("```json"):
        text = text[7:]  # Remove ```json
    elif text.startswith("```"):
        text = text[3:]  # Remove ```

    if text.endswith("```"):
        text = text[:-3]  # Remove trailing ```

    text = text.strip()

    return json.loads(text)


def save_json(data: Any, filepath: str, indent: int = 2):
    """
    Save data to JSON file.

    Args:
        data: Data to save
        filepath: Path to save to
        indent: JSON indentation
    """
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=indent)

    print(f"✅ Saved to {filepath}")


def load_json(filepath: str) -> Any:
    """
    Load data from JSON file.

    Args:
        filepath: Path to load from

    Returns:
        Loaded data
    """
    with open(filepath, 'r') as f:
        data = json.load(f)

    print(f"✅ Loaded from {filepath}")
    return data


def print_example(example: Dict, index: int = None):
    """
    Pretty print an example.

    Args:
        example: Example dict
        index: Optional index number
    """
    prefix = f"{index}. " if index is not None else ""

    print(f"\n{prefix}[{example.get('issue_type', 'unknown')}] "
          f"({example.get('domain', 'unknown')}) "
          f"- Score: {example.get('final_score', example.get('weighted_score', 'N/A'))}")

    # Safely get question and answer with fallbacks
    question = example.get('reference_question', example.get('question', 'N/A'))
    answer = example.get('reference_answer', example.get('answer', 'N/A'))

    # Convert to string first, then slice
    question_str = str(question)
    answer_str = str(answer)

    question_preview = question_str[:100] + "..." if len(question_str) > 100 else question_str
    answer_preview = answer_str[:100] + "..." if len(answer_str) > 100 else answer_str

    print(f"   Question: {question_preview}")
    print(f"   Answer: {answer_preview}")


def print_summary_stats(examples: List[Dict], dataset_name: str = "Dataset"):
    """
    Print summary statistics for a dataset.

    Args:
        examples: List of examples
        dataset_name: Name of the dataset
    """
    print(f"\n{'='*80}")
    print(f"{dataset_name.upper()} - SUMMARY STATISTICS")
    print(f"{'='*80}")

    print(f"Total examples: {len(examples)}")

    # Count by issue type
    issue_types = {}
    for ex in examples:
        issue_type = ex.get('issue_type', 'unknown')
        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1

    print(f"\nIssue types:")
    for issue_type, count in sorted(issue_types.items()):
        print(f"  - {issue_type}: {count}")

    # Count by domain
    domains = {}
    for ex in examples:
        domain = ex.get('domain', 'unknown')
        domains[domain] = domains.get(domain, 0) + 1

    print(f"\nDomains:")
    for domain, count in sorted(domains.items()):
        print(f"  - {domain}: {count}")

    # Average scores if available
    if examples and 'weighted_score' in examples[0]:
        avg_score = sum(ex.get('weighted_score', 0) for ex in examples) / len(examples)
        print(f"\nAverage weighted score: {avg_score:.2f}")

    if examples and 'final_score' in examples[0]:
        avg_final_score = sum(ex.get('final_score', 0) for ex in examples) / len(examples)
        print(f"Average final score: {avg_final_score:.2f}")


def add_seed_ids(seeds: List[Dict], prefix: str = "seed") -> List[Dict]:
    """
    Add unique IDs to seed examples.

    Args:
        seeds: List of seed examples
        prefix: Prefix for IDs

    Returns:
        Seeds with IDs added
    """
    for i, seed in enumerate(seeds):
        seed['seed_id'] = f"{prefix}_{i:03d}"

    return seeds
