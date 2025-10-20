"""
Generate RAGAS datasets from existing golden JSON files.

This script:
1. Loads golden clarity and rigor JSON files
2. Converts them to RAGAS format (ensuring all fields are strings)
3. Saves as HuggingFace datasets format

Usage:
    python eval/golden_dataset/generate_ragas_datasets.py
"""

import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from datasets import Dataset


def convert_to_string(value):
    """
    Convert any value to string safely.

    Args:
        value: Any value (str, dict, list, etc.)

    Returns:
        String representation
    """
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


def load_golden_file(filepath: str) -> list:
    """
    Load golden dataset from JSON file.

    Args:
        filepath: Path to golden JSON file

    Returns:
        List of golden examples
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    print(f"✅ Loaded {len(data)} examples from {filepath}")
    return data


def convert_to_ragas_format(golden_examples: list) -> list:
    """
    Convert golden examples to RAGAS format.

    Args:
        golden_examples: List of golden example dicts

    Returns:
        List of RAGAS-formatted dicts
    """
    ragas_examples = []

    for ex in golden_examples:
        # Get values with fallbacks
        question = ex.get('reference_question', ex.get('question', ''))
        context = ex.get('reference_context', ex.get('context', ''))
        answer = ex.get('reference_answer', ex.get('answer', ''))

        # Convert everything to strings
        ragas_examples.append({
            "question": convert_to_string(question),
            "contexts": [convert_to_string(context)],
            "ground_truth": convert_to_string(answer),
            "issue_type": convert_to_string(ex.get('issue_type', 'unknown')),
            "domain": convert_to_string(ex.get('domain', 'general')),
            "severity": convert_to_string(ex.get('severity', 'info')),
        })

    return ragas_examples


def main():
    """Main function to generate RAGAS datasets."""
    print("\n" + "="*80)
    print("GENERATE RAGAS DATASETS FROM GOLDEN JSON FILES")
    print("="*80)

    # Get backend directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, '..', '..')

    # Define paths
    clarity_golden_path = os.path.join(backend_dir, "eval/data/golden/golden_clarity_10.json")
    rigor_golden_path = os.path.join(backend_dir, "eval/data/golden/golden_rigor_10.json")

    clarity_ragas_path = os.path.join(backend_dir, "eval/data/golden/golden_clarity_ragas")
    rigor_ragas_path = os.path.join(backend_dir, "eval/data/golden/golden_rigor_ragas")

    # Check if golden files exist
    if not os.path.exists(clarity_golden_path):
        print(f"❌ Error: Golden clarity file not found: {clarity_golden_path}")
        print("\nRun step 3 first:")
        print("  python eval/golden_dataset/step3_filter_golden.py")
        return

    if not os.path.exists(rigor_golden_path):
        print(f"❌ Error: Golden rigor file not found: {rigor_golden_path}")
        print("\nRun step 3 first:")
        print("  python eval/golden_dataset/step3_filter_golden.py")
        return

    # Step 1: Load golden files
    print("\nStep 1: Loading golden JSON files...")
    clarity_golden = load_golden_file(clarity_golden_path)
    rigor_golden = load_golden_file(rigor_golden_path)

    # Step 2: Convert to RAGAS format
    print("\nStep 2: Converting to RAGAS format...")
    clarity_ragas_list = convert_to_ragas_format(clarity_golden)
    rigor_ragas_list = convert_to_ragas_format(rigor_golden)

    print(f"✅ Converted {len(clarity_ragas_list)} clarity examples")
    print(f"✅ Converted {len(rigor_ragas_list)} rigor examples")

    # Step 3: Verify data quality
    print("\nStep 3: Verifying data quality...")

    def verify_ragas_example(example, index):
        """Verify a single RAGAS example."""
        issues = []

        if not example.get('question'):
            issues.append(f"  Example {index}: Missing question")
        if not example.get('contexts') or not example['contexts'][0]:
            issues.append(f"  Example {index}: Missing context")
        if not example.get('ground_truth'):
            issues.append(f"  Example {index}: Missing ground_truth")

        # Check that all values are strings
        if not isinstance(example.get('question'), str):
            issues.append(f"  Example {index}: question is not a string")
        if not isinstance(example.get('ground_truth'), str):
            issues.append(f"  Example {index}: ground_truth is not a string")
        if not isinstance(example.get('contexts'), list) or not all(isinstance(c, str) for c in example.get('contexts', [])):
            issues.append(f"  Example {index}: contexts is not a list of strings")

        return issues

    all_issues = []
    for i, ex in enumerate(clarity_ragas_list, 1):
        all_issues.extend(verify_ragas_example(ex, f"clarity-{i}"))

    for i, ex in enumerate(rigor_ragas_list, 1):
        all_issues.extend(verify_ragas_example(ex, f"rigor-{i}"))

    if all_issues:
        print("⚠️  Found data quality issues:")
        for issue in all_issues:
            print(issue)
    else:
        print("✅ All examples passed validation")

    # Step 4: Create HuggingFace datasets
    print("\nStep 4: Creating HuggingFace datasets...")

    try:
        clarity_ragas_dataset = Dataset.from_list(clarity_ragas_list)
        rigor_ragas_dataset = Dataset.from_list(rigor_ragas_list)
        print("✅ Created datasets successfully")
    except Exception as e:
        print(f"❌ Error creating datasets: {e}")
        print("\nDebugging first example:")
        if clarity_ragas_list:
            print("Clarity example 1:")
            for key, value in clarity_ragas_list[0].items():
                print(f"  {key}: {type(value).__name__} = {str(value)[:100]}")
        return

    # Step 5: Save to disk
    print("\nStep 5: Saving datasets to disk...")

    clarity_ragas_dataset.save_to_disk(clarity_ragas_path)
    rigor_ragas_dataset.save_to_disk(rigor_ragas_path)

    print(f"✅ Saved clarity RAGAS dataset to: {clarity_ragas_path}")
    print(f"✅ Saved rigor RAGAS dataset to: {rigor_ragas_path}")

    # Step 6: Summary
    print("\n" + "="*80)
    print("RAGAS DATASETS GENERATED SUCCESSFULLY!")
    print("="*80)

    print(f"\nClarity dataset:")
    print(f"  - Examples: {len(clarity_ragas_dataset)}")
    print(f"  - Columns: {clarity_ragas_dataset.column_names}")
    print(f"  - Location: {clarity_ragas_path}")

    print(f"\nRigor dataset:")
    print(f"  - Examples: {len(rigor_ragas_dataset)}")
    print(f"  - Columns: {rigor_ragas_dataset.column_names}")
    print(f"  - Location: {rigor_ragas_path}")

    print("\nSample from clarity dataset:")
    print("-" * 40)
    sample = clarity_ragas_dataset[0]
    print(f"Question: {sample['question'][:100]}...")
    print(f"Context: {sample['contexts'][0][:100]}...")
    print(f"Ground truth: {sample['ground_truth'][:100]}...")
    print(f"Issue type: {sample['issue_type']}")
    print(f"Domain: {sample['domain']}")

    print("\nNext steps:")
    print("  1. Review the datasets to ensure quality")
    print("  2. Run evaluation:")
    print("     python eval/evaluate_golden_with_ragas.py")


if __name__ == "__main__":
    main()
