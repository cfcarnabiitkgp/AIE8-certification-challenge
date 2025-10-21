"""
Test script for LangGraph-based Review Controller.

This script tests the new LangGraph implementation with Pydantic state models.
"""
import asyncio
import json
import time
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.agents.review_controller_langgraph import LangGraphReviewController

# Sample research paper for testing
SAMPLE_PAPER = """# Quantum Computing Breakthrough: Novel Error Correction

## Abstract

This paper presents a groundbreaking approach to quantum error correction using topological codes. We demonstrate improved fidelity rates and reduced computational overhead compared to existing methods.

## Introduction

Quantum computing has emerged as a transformative technology with the potential to revolutionize computational capabilities across various domains. However, quantum systems are inherently susceptible to environmental noise and decoherence, which limit their practical utility. Error correction mechanisms are therefore crucial for the development of fault-tolerant quantum computers.

In this work, we introduce a novel error correction scheme that leverages topological properties of quantum states to achieve superior performance metrics. Our approach builds upon recent advances in surface codes while addressing key limitations in scalability and resource requirements.

## Methods

### Experimental Setup

We conducted our experiments using a 53-qubit quantum processor with superconducting qubits. The system operates at a temperature of 15 millikelvin to minimize thermal noise. Qubit connectivity follows a hexagonal lattice structure, optimized for topological code implementation.

### Error Correction Protocol

Our protocol consists of three main stages:

1. **Syndrome Measurement**: We perform stabilizer measurements every 100 nanoseconds using ancilla qubits positioned at lattice plaquettes.

2. **Error Detection**: Classical post-processing algorithms analyze measurement outcomes to identify error locations with 99.2% accuracy.

3. **Correction Application**: Pauli operators are applied to affected qubits based on the decoded syndrome information.

The entire cycle completes in approximately 500 nanoseconds, representing a 3x improvement over previous implementations.

## Results

Our experimental results demonstrate significant improvements across multiple performance metrics:

- **Logical Error Rate**: Reduced to 0.1% per cycle (previous best: 0.3%)
- **Resource Overhead**: 30% reduction in required ancilla qubits
- **Scalability**: Successful demonstration on systems up to 100 qubits

Figure 1 illustrates the relationship between physical error rate and logical error rate across different code distances. We observe exponential suppression of logical errors, consistent with theoretical predictions.

### Comparative Analysis

Table 1 compares our approach with three baseline methods:

| Method | Error Rate | Overhead | Scalability |
|--------|------------|----------|-------------|
| Surface Code | 0.3% | High | Limited |
| Color Code | 0.25% | Very High | Poor |
| Our Method | 0.1% | Medium | Good |

The data clearly show that our method outperforms existing approaches while maintaining reasonable resource requirements.

## Discussion

The observed improvements in error correction performance can be attributed to several factors:

1. **Optimized Lattice Geometry**: The hexagonal structure reduces the number of syndrome measurements required.

2. **Adaptive Decoding**: Our machine learning-enhanced decoder adjusts thresholds based on observed error patterns.

3. **Parallel Processing**: Syndrome extraction and error correction occur simultaneously, reducing cycle time.

However, our approach is not without limitations. The current implementation requires specialized qubit connectivity that may not be available on all quantum hardware platforms. Additionally, the classical processing overhead increases with system size, potentially limiting scalability beyond 200 qubits.

Future work should focus on adapting the protocol for different qubit topologies and developing more efficient decoding algorithms. Integration with other error mitigation techniques could further enhance performance.

## Conclusion

We have presented a novel quantum error correction scheme that achieves state-of-the-art performance on current quantum hardware. The combination of topological codes with adaptive decoding represents a significant step toward fault-tolerant quantum computation. Our results suggest that practical quantum computers with thousands of logical qubits may be achievable within the next decade.

## References

1. Fowler, A. et al. "Surface codes: Towards practical large-scale quantum computation." Physical Review A, 2012.
2. Bombín, H. "Topological Order with a Twist: Ising Anyons from an Abelian Model." Physical Review Letters, 2010.
3. Dennis, E. et al. "Topological quantum memory." Journal of Mathematical Physics, 2002.
"""


async def test_langgraph_review():
    """Test the LangGraph review controller."""
    print("=" * 80)
    print("TESTING LANGGRAPH REVIEW CONTROLLER")
    print("=" * 80)
    print()

    # Initialize controller
    print("Initializing LangGraph ReviewController...")
    controller = LangGraphReviewController()
    print("✓ Controller initialized")
    print()

    # Get section structure
    print("Analyzing document structure...")
    structure = controller.get_section_structure(SAMPLE_PAPER)
    print("Document Sections:")
    print(structure)
    print()

    # Run review
    print("Starting LangGraph review workflow...")
    print("-" * 80)
    start_time = time.time()

    result = await controller.review(
        content=SAMPLE_PAPER,
        session_id="test-session-langgraph",
        target_venue="Nature Quantum Information"
    )

    elapsed_time = time.time() - start_time
    print("-" * 80)
    print(f"✓ Review completed in {elapsed_time:.2f}s")
    print()

    # Display results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    suggestions = result["suggestions"]
    metadata = result["metadata"]

    print(f"Total Suggestions: {len(suggestions)}")
    print(f"  - Clarity: {metadata['clarity_suggestions']}")
    print(f"  - Rigor: {metadata['rigor_suggestions']}")
    print(f"  - Final (after orchestrator): {metadata['final_suggestions']}")
    print(f"Total Sections Analyzed: {metadata['total_sections']}")
    print(f"Processing Time: {elapsed_time:.2f}s")
    print()

    # Group by severity
    by_severity = {}
    for s in suggestions:
        severity = s["severity"]
        by_severity[severity] = by_severity.get(severity, 0) + 1

    print("Suggestions by Severity:")
    for severity, count in sorted(by_severity.items()):
        print(f"  - {severity}: {count}")
    print()

    # Show top 5 suggestions
    print("=" * 80)
    print("TOP 5 SUGGESTIONS")
    print("=" * 80)
    print()

    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"{i}. [{suggestion['type'].upper()}] {suggestion['title']}")
        print(f"   Section: {suggestion['section']}")
        print(f"   Severity: {suggestion['severity']}")
        print(f"   Description: {suggestion['description'][:150]}...")
        if suggestion.get('suggested_fix'):
            print(f"   Fix: {suggestion['suggested_fix'][:100]}...")
        print()

    # Save to file
    output_file = "langgraph_review_results.json"
    with open(output_file, "w") as f:
        json.dump({
            "result": result,
            "processing_time": elapsed_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }, f, indent=2)

    print(f"✓ Full results saved to {output_file}")
    print()

    # Cost estimation (approximate)
    input_tokens = len(SAMPLE_PAPER.split()) * 1.3  # rough estimate
    output_tokens = len(json.dumps(suggestions)) / 4  # rough estimate
    total_tokens = input_tokens + output_tokens

    # Pricing for gpt-4o-mini (rough estimate)
    cost_per_1k_input = 0.00015
    cost_per_1k_output = 0.0006
    estimated_cost = (input_tokens / 1000 * cost_per_1k_input +
                      output_tokens / 1000 * cost_per_1k_output)

    print("=" * 80)
    print("PERFORMANCE METRICS")
    print("=" * 80)
    print(f"Estimated Tokens: ~{int(total_tokens)}")
    print(f"Estimated Cost: ${estimated_cost:.4f}")
    print(f"Time per Section: {elapsed_time / metadata['total_sections']:.2f}s")
    print(f"Suggestions per Second: {len(suggestions) / elapsed_time:.2f}")
    print()

    print("=" * 80)
    print("TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_langgraph_review())

