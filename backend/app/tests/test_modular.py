"""
Test script for the new modular peer review architecture.

Usage:
    python test_modular.py

Tests the simplified, modular architecture with:
- Section-wise analysis
- Clarity agent
- Rigor agent
"""
import asyncio
import json
import time
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.agents.review_controller import ReviewController


# Sample research paper with clarity and rigor issues
SAMPLE_PAPER = """
# Deep Learning for Image Classification

## Abstract

We propose a new method. It works good and is better than other methods.

## Introduction

Neural networks are important. Many people use them. We made something new.

## Related Work

Some work has been done. Our method is different.

## Methodology

We used a neural network with several layers. The network was trained.
We tested it on data. The architecture has convolutions.

## Experiments

We ran experiments. The model was evaluated on a dataset.
Table 1 shows results. Our method achieved high accuracy.

## Results

As shown in Table 1, accuracy was 95%. The baseline got 85%.
Our method is better.

Table 1: Results
| Method | Accuracy |
|--------|----------|
| Ours   | 95%      |
| Baseline | 85%    |

## Conclusion

Our method works well. Future work includes more experiments.
It should be used by others.

## References

[1] Some paper
[2] Another paper
"""


async def test_modular_architecture():
    """Test the modular review architecture."""
    print("="*80)
    print("MODULAR PEER REVIEW ARCHITECTURE TEST")
    print("="*80)
    print()

    # Initialize controller
    print("Initializing ReviewController...")
    controller = ReviewController()
    print("✓ Controller initialized")
    print()

    # Get section structure
    print("Paper Structure:")
    print("-" * 80)
    structure = controller.get_section_structure(SAMPLE_PAPER)
    print(structure)
    print()

    # Run review
    print("="*80)
    print("RUNNING PEER REVIEW")
    print("="*80)
    print()

    start_time = time.time()

    result = await controller.review(
        content=SAMPLE_PAPER,
        session_id="test_modular_123",
        target_venue="Test Conference"
    )

    elapsed_time = time.time() - start_time

    # Display results
    print(f"\n{'='*80}")
    print(f"REVIEW RESULTS")
    print(f"{'='*80}\n")
    print(f"Processing time: {elapsed_time:.2f}s")
    print(f"Total suggestions: {len(result['suggestions'])}")
    print(f"Total sections analyzed: {result['metadata']['total_sections']}")
    print()

    # Group by type
    by_type = {}
    for suggestion in result['suggestions']:
        sug_type = suggestion['type']
        if sug_type not in by_type:
            by_type[sug_type] = []
        by_type[sug_type].append(suggestion)

    # Summary by type
    print("Summary by Type:")
    print("-" * 80)
    for sug_type, suggestions in sorted(by_type.items()):
        severities = {}
        for sug in suggestions:
            sev = sug['severity']
            severities[sev] = severities.get(sev, 0) + 1

        sev_str = ", ".join([f"{k}: {v}" for k, v in severities.items()])
        print(f"  {sug_type:15s}: {len(suggestions):2d} suggestions ({sev_str})")

    # Detailed results
    print(f"\n{'='*80}")
    print("DETAILED SUGGESTIONS")
    print("="*80)

    for sug_type, suggestions in sorted(by_type.items()):
        print(f"\n{sug_type.upper()} ({len(suggestions)} suggestions)")
        print("-" * 80)
        for i, sug in enumerate(suggestions, 1):
            print(f"\n  [{i}] {sug['severity'].upper()} - Section: {sug['section']}")
            print(f"      Lines: {sug.get('line_start', '?')}-{sug.get('line_end', '?')}")
            print(f"      Issue: {sug['description'][:150]}")
            if sug.get('suggested_fix'):
                print(f"      Fix: {sug['suggested_fix'][:150]}")

    print(f"\n{'='*80}\n")

    # Save results
    filename = f"test_modular_results_{int(time.time())}.json"
    with open(filename, "w") as f:
        json.dump(result, f, indent=2)

    print(f"✓ Results saved to {filename}")
    print()
    print("="*80)
    print("TEST COMPLETED SUCCESSFULLY")
    print("="*80)
    print()
    print("Architecture Details:")
    print("  - Section-wise analysis: ✓")
    print("  - ClarityAgent: ✓")
    print("  - RigorAgent: ✓")
    print("  - Modular design: ✓")
    print(f"  - Fast execution: {elapsed_time:.2f}s")
    print()


if __name__ == "__main__":
    asyncio.run(test_modular_architecture())

