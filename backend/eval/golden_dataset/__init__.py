"""
Golden Dataset Generation using EvolInstruct.

This package implements a 3-step pipeline to create high-quality
evaluation datasets for the Clarity and Rigor agents:

1. Generate seeds from guideline PDFs
2. Evolve seeds using EvolInstruct operators
3. Filter to golden 10 using LLM-as-judge

Usage:
    # Run full pipeline
    python backend/eval/golden_dataset/run_full_pipeline.py

    # Or run individual steps
    python backend/eval/golden_dataset/step1_generate_seeds.py
    python backend/eval/golden_dataset/step2_evolve_candidates.py
    python backend/eval/golden_dataset/step3_filter_golden.py

    # Evaluate with RAGAS
    python backend/eval/evaluate_golden_with_ragas.py
"""

__version__ = "1.0.0"
