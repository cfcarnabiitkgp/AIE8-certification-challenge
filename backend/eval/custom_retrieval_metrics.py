"""
Custom retrieval metrics that directly compare retrieved_contexts with reference_contexts.

RAGAS 0.3+ context_precision and context_recall use the reference answer to infer
which contexts are relevant, which doesn't work when the agent output format differs
from the reference answer format.

These custom metrics directly compare the retrieved contexts with ground truth contexts
using text similarity.
"""

from typing import List, Dict
import numpy as np


def compute_context_overlap(retrieved: str, reference: str) -> float:
    """
    Compute word-level overlap between two context strings.

    Returns a score between 0 and 1 indicating the proportion of
    reference words found in the retrieved context.
    """
    if not reference or not retrieved:
        return 0.0

    # Normalize and tokenize
    ref_words = set(reference.lower().split())
    ret_words = set(retrieved.lower().split())

    if not ref_words:
        return 0.0

    # Calculate overlap
    overlap = len(ref_words & ret_words)
    return overlap / len(ref_words)


def is_context_match(retrieved: str, reference: str, threshold: float = 0.5) -> bool:
    """
    Check if a retrieved context matches a reference context.

    Args:
        retrieved: Retrieved context string
        reference: Reference context string
        threshold: Minimum overlap score to consider a match (default: 0.5)

    Returns:
        True if overlap score >= threshold
    """
    # Check for exact substring match first (fast path)
    if reference in retrieved or retrieved in reference:
        return True

    # Fall back to word overlap
    overlap_score = compute_context_overlap(retrieved, reference)
    return overlap_score >= threshold


def compute_custom_context_precision(
    retrieved_contexts: List[str],
    reference_contexts: List[str],
    threshold: float = 0.5
) -> float:
    """
    Compute precision: proportion of retrieved contexts that match reference contexts.

    Precision = (# of retrieved contexts that match any reference) / (# of retrieved contexts)

    Args:
        retrieved_contexts: List of retrieved context strings
        reference_contexts: List of ground truth context strings
        threshold: Minimum overlap score for a match

    Returns:
        Precision score between 0 and 1
    """
    if not retrieved_contexts:
        return 0.0

    if not reference_contexts:
        return 0.0

    # Count how many retrieved contexts match at least one reference context
    matches = 0
    for retrieved in retrieved_contexts:
        for reference in reference_contexts:
            if is_context_match(retrieved, reference, threshold):
                matches += 1
                break  # Count each retrieved context only once

    return matches / len(retrieved_contexts)


def compute_custom_context_recall(
    retrieved_contexts: List[str],
    reference_contexts: List[str],
    threshold: float = 0.5
) -> float:
    """
    Compute recall: proportion of reference contexts found in retrieved contexts.

    Recall = (# of reference contexts found in retrieved) / (# of reference contexts)

    Args:
        retrieved_contexts: List of retrieved context strings
        reference_contexts: List of ground truth context strings
        threshold: Minimum overlap score for a match

    Returns:
        Recall score between 0 and 1
    """
    if not reference_contexts:
        return 1.0  # Perfect recall if no references to find

    if not retrieved_contexts:
        return 0.0

    # Count how many reference contexts are found in retrieved contexts
    matches = 0
    for reference in reference_contexts:
        for retrieved in retrieved_contexts:
            if is_context_match(retrieved, reference, threshold):
                matches += 1
                break  # Count each reference context only once

    return matches / len(reference_contexts)


def compute_custom_retrieval_metrics(
    retrieved_contexts: List[str],
    reference_contexts: List[str],
    threshold: float = 0.5
) -> Dict[str, float]:
    """
    Compute all custom retrieval metrics.

    Returns:
        Dictionary with keys: custom_context_precision, custom_context_recall, custom_context_f1
    """
    precision = compute_custom_context_precision(retrieved_contexts, reference_contexts, threshold)
    recall = compute_custom_context_recall(retrieved_contexts, reference_contexts, threshold)

    # F1 score
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    return {
        "custom_context_precision": precision,
        "custom_context_recall": recall,
        "custom_context_f1": f1
    }


def evaluate_retrieval_batch(
    retrieved_contexts_list: List[List[str]],
    reference_contexts_list: List[List[str]],
    threshold: float = 0.5
) -> Dict[str, float]:
    """
    Evaluate retrieval metrics across a batch of samples.

    Args:
        retrieved_contexts_list: List of retrieved context lists (one per sample)
        reference_contexts_list: List of reference context lists (one per sample)
        threshold: Overlap threshold for matches

    Returns:
        Dictionary with averaged metrics
    """
    precisions = []
    recalls = []
    f1s = []

    for retrieved, reference in zip(retrieved_contexts_list, reference_contexts_list):
        metrics = compute_custom_retrieval_metrics(retrieved, reference, threshold)
        precisions.append(metrics["custom_context_precision"])
        recalls.append(metrics["custom_context_recall"])
        f1s.append(metrics["custom_context_f1"])

    return {
        "custom_context_precision": float(np.mean(precisions)),
        "custom_context_recall": float(np.mean(recalls)),
        "custom_context_f1": float(np.mean(f1s))
    }
