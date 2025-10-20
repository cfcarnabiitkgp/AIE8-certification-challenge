"""
Run the full golden dataset generation pipeline.

This script orchestrates all three steps:
1. Generate seeds from guidelines
2. Evolve seeds using EvolInstruct
3. Filter to golden 10 using LLM-as-judge

Usage:
    python backend/eval/golden_dataset/run_full_pipeline.py

Or run individual steps:
    python backend/eval/golden_dataset/step1_generate_seeds.py
    python backend/eval/golden_dataset/step2_evolve_candidates.py
    python backend/eval/golden_dataset/step3_filter_golden.py
"""

import sys
import os
import time

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))


def run_step(step_number: int, step_name: str, step_module: str):
    """
    Run a pipeline step.

    Args:
        step_number: Step number (1, 2, or 3)
        step_name: Human-readable step name
        step_module: Module name to import and run
    """
    print("\n" + "="*80)
    print(f"RUNNING STEP {step_number}: {step_name}")
    print("="*80)

    start_time = time.time()

    try:
        # Import and run the step's main function
        module = __import__(step_module, fromlist=['main'])
        module.main()

        elapsed = time.time() - start_time
        print(f"\n✅ Step {step_number} completed in {elapsed:.1f} seconds")

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Step {step_number} failed after {elapsed:.1f} seconds")
        print(f"Error: {e}")
        raise


def main():
    """Run the full pipeline."""
    print("\n" + "="*80)
    print("GOLDEN DATASET GENERATION PIPELINE")
    print("="*80)
    print("\nThis pipeline will:")
    print("  1. Generate seed examples from guideline PDFs")
    print("  2. Evolve seeds using EvolInstruct operators")
    print("  3. Filter to golden 10 using LLM-as-judge")
    print("\nExpected time: 1-2 hours (depending on LLM API speed)")
    print("="*80)

    pipeline_start = time.time()

    # Step 1: Generate seeds
    run_step(
        step_number=1,
        step_name="Generate Seeds from Guidelines",
        step_module="eval.golden_dataset.step1_generate_seeds"
    )

    # Step 2: Evolve candidates
    run_step(
        step_number=2,
        step_name="Evolve Seeds with EvolInstruct",
        step_module="eval.golden_dataset.step2_evolve_candidates"
    )

    # Step 3: Filter to golden 10
    run_step(
        step_number=3,
        step_name="Filter to Golden 10",
        step_module="eval.golden_dataset.step3_filter_golden"
    )

    # Pipeline complete
    pipeline_elapsed = time.time() - pipeline_start

    print("\n" + "="*80)
    print("PIPELINE COMPLETE!")
    print("="*80)
    print(f"\nTotal time: {pipeline_elapsed / 60:.1f} minutes")

    print("\nGenerated files:")
    print("  📁 backend/eval/data/seeds/")
    print("     - clarity_seeds.json")
    print("     - rigor_seeds.json")
    print("  📁 backend/eval/data/candidates/")
    print("     - clarity_candidates.json")
    print("     - rigor_candidates.json")
    print("  📁 backend/eval/data/golden/")
    print("     - golden_clarity_10.json")
    print("     - golden_rigor_10.json")
    print("     - golden_clarity_ragas/")
    print("     - golden_rigor_ragas/")

    print("\nNext steps:")
    print("  1. Review the golden datasets manually")
    print("  2. Run evaluation with RAGAS:")
    print("     python backend/eval/evaluate_golden_with_ragas.py")


if __name__ == "__main__":
    main()
