"""
Convert golden dataset JSON files to CSV format.

This script reads the golden_clarity_10.json and golden_rigor_10.json files
and converts them to CSV format for easier analysis and use in evaluations.
"""

import json
import csv
from pathlib import Path


def flatten_quality_scores(example):
    """Flatten the nested quality_scores dictionary."""
    flat = {}
    if 'quality_scores' in example:
        for key, value in example['quality_scores'].items():
            flat[f'quality_{key}'] = value
    return flat


def convert_json_to_csv(json_path, csv_path):
    """
    Convert a JSON golden dataset to CSV format.

    Args:
        json_path: Path to input JSON file
        csv_path: Path to output CSV file
    """
    # Read JSON data
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not data:
        print(f"No data found in {json_path}")
        return

    # Prepare rows for CSV
    rows = []
    for example in data:
        row = {}

        # Add main fields
        for key, value in example.items():
            if key == 'quality_scores':
                # Flatten nested quality_scores
                quality_flat = flatten_quality_scores(example)
                row.update(quality_flat)
            else:
                # Convert lists/dicts to string representation
                if isinstance(value, (dict, list)):
                    row[key] = json.dumps(value)
                else:
                    row[key] = value

        rows.append(row)

    # Get all unique fieldnames across all rows
    fieldnames = set()
    for row in rows:
        fieldnames.update(row.keys())

    # Sort fieldnames for consistent column order
    # Put main fields first, then quality scores
    main_fields = ['reference_question', 'reference_context', 'reference_answer',
                   'question', 'context', 'answer',
                   'issue_type', 'severity', 'domain', 'section_type',
                   'evolution_operator', 'parent_seed_id', 'seed_id', 'source',
                   'guideline_source_file', 'weighted_score', 'final_score']

    ordered_fields = [f for f in main_fields if f in fieldnames]
    quality_fields = sorted([f for f in fieldnames if f.startswith('quality_')])
    other_fields = sorted([f for f in fieldnames if f not in ordered_fields and not f.startswith('quality_')])

    fieldnames = ordered_fields + quality_fields + other_fields

    # Write to CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Converted {json_path} -> {csv_path}")
    print(f"  Rows: {len(rows)}, Columns: {len(fieldnames)}")


def main():
    """Convert all golden dataset JSON files to CSV."""
    base_dir = Path(__file__).parent.parent / 'data' / 'golden'

    # Convert clarity dataset
    clarity_json = base_dir / 'golden_clarity_10.json'
    clarity_csv = base_dir / 'golden_clarity_10.csv'

    if clarity_json.exists():
        convert_json_to_csv(clarity_json, clarity_csv)
    else:
        print(f"File not found: {clarity_json}")

    # Convert rigor dataset
    rigor_json = base_dir / 'golden_rigor_10.json'
    rigor_csv = base_dir / 'golden_rigor_10.csv'

    if rigor_json.exists():
        convert_json_to_csv(rigor_json, rigor_csv)
    else:
        print(f"File not found: {rigor_json}")

    print("\nConversion complete!")


if __name__ == "__main__":
    main()
