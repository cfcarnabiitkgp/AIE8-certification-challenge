"""
Step 3: Filter candidates to golden 10 using LLM-as-judge.

This script:
1. Loads candidate examples from Step 2
2. Scores each candidate on multiple quality dimensions
3. Selects top 10 with diversity considerations
4. Saves golden datasets to JSON files
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from eval.golden_dataset.config import (
    QUALITY_CRITERIA,
    LLM_CONFIG,
    PIPELINE_CONFIG,
    DIVERSITY_CONFIG
)
from eval.golden_dataset.utils import (
    load_json,
    save_json,
    create_llm,
    parse_json_response,
    print_example,
    print_summary_stats
)


def score_candidate(candidate: dict, llm) -> dict:
    """
    Score a candidate example on multiple quality dimensions.

    Args:
        candidate: Candidate example dict
        llm: LLM instance for judging

    Returns:
        Quality scores dict
    """
    # Build criteria descriptions
    criteria_text = "\n".join([
        f"{i+1}. **{name.replace('_', ' ').title()}** (1-5): {info['description']}\n"
        f"   Scale: {info['scale']}"
        for i, (name, info) in enumerate(QUALITY_CRITERIA.items())
    ])

    prompt = f"""
You are evaluating a candidate example for a GOLDEN evaluation dataset.

Example:
- Question: {candidate.get('reference_question', 'N/A')}
- Context: {candidate.get('reference_context', 'N/A')}
- Answer: {candidate.get('reference_answer', 'N/A')}
- Issue: {candidate.get('issue_type', 'N/A')}
- Domain: {candidate.get('domain', 'N/A')}

Rate on 1-5 scale:

{criteria_text}

Return JSON:
{{
    "realism": 1-5,
    "clarity_of_issue": 1-5,
    "pedagogical_value": 1-5,
    "actionability": 1-5,
    "guideline_alignment": 1-5,
    "overall_quality": 1-5,
    "justification": "brief explanation of scores"
}}
"""

    try:
        response = llm.invoke(prompt)
        scores = parse_json_response(response.content)
        return scores

    except Exception as e:
        print(f"    ❌ Scoring failed: {e}")
        # Return default low scores
        return {
            "realism": 1,
            "clarity_of_issue": 1,
            "pedagogical_value": 1,
            "actionability": 1,
            "guideline_alignment": 1,
            "overall_quality": 1,
            "justification": f"Scoring failed: {str(e)}"
        }


def compute_weighted_score(scores: dict) -> float:
    """
    Compute weighted score from quality criteria scores.

    Args:
        scores: Quality scores dict

    Returns:
        Weighted score (0-5)
    """
    weighted = 0.0

    for criterion, info in QUALITY_CRITERIA.items():
        score = scores.get(criterion, 1)
        weight = info['weight']
        weighted += score * weight

    return weighted


def select_diverse_top_n(scored_candidates: list, n: int = 10) -> list:
    """
    Select top N candidates ensuring diversity in issue types and domains.

    Args:
        scored_candidates: List of scored candidates (sorted by score)
        n: Number to select

    Returns:
        List of top N diverse candidates
    """
    selected = []
    issue_types_seen = set()
    domains_seen = set()

    for candidate in scored_candidates:
        if len(selected) >= n:
            break

        issue_type = candidate.get('issue_type', 'unknown')
        domain = candidate.get('domain', 'general')

        # Compute diversity bonus
        diversity_bonus = 0.0
        if issue_type not in issue_types_seen:
            diversity_bonus += DIVERSITY_CONFIG['issue_type_bonus']
        if domain not in domains_seen:
            diversity_bonus += DIVERSITY_CONFIG['domain_bonus']

        # Adjust final score
        candidate['final_score'] = candidate['weighted_score'] + diversity_bonus

        # Add to selected
        selected.append(candidate)
        issue_types_seen.add(issue_type)
        domains_seen.add(domain)

    # Re-sort by final score
    selected.sort(key=lambda x: x['final_score'], reverse=True)

    return selected[:n]


def filter_to_golden_n(candidates: list, llm, n: int = 10) -> list:
    """
    Score all candidates and select top N with diversity.

    Args:
        candidates: List of candidate examples
        llm: LLM instance for judging
        n: Number of golden examples to select

    Returns:
        List of top N golden examples
    """
    print(f"\nScoring {len(candidates)} candidates...")

    scored_candidates = []

    for i, candidate in enumerate(candidates, 1):
        print(f"  Scoring {i}/{len(candidates)}: [{candidate.get('issue_type', 'unknown')}]")

        # Score the candidate
        scores = score_candidate(candidate, llm)

        # Compute weighted score
        weighted = compute_weighted_score(scores)

        # Add scores to candidate
        candidate['quality_scores'] = scores
        candidate['weighted_score'] = weighted

        scored_candidates.append(candidate)

        print(f"    Score: {weighted:.2f} - {scores.get('justification', 'N/A')[:80]}...")

    # Sort by weighted score
    scored_candidates.sort(key=lambda x: x['weighted_score'], reverse=True)

    print(f"\n✅ Scored all candidates. Top score: {scored_candidates[0]['weighted_score']:.2f}")

    # Select diverse top N
    print(f"\nSelecting diverse top {n}...")
    golden = select_diverse_top_n(scored_candidates, n=n)

    print(f"✅ Selected {len(golden)} golden examples")

    return golden


def main():
    """Main function to filter candidates to golden 10."""
    print("\n" + "="*80)
    print("STEP 3: FILTER TO GOLDEN 10 USING LLM-AS-JUDGE")
    print("="*80)

    # Get the backend directory (works whether run from backend/ or project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, '..', '..')

    # Load configuration
    final_golden_count = PIPELINE_CONFIG['final_golden_count']

    # Create LLM for judging
    print("\nInitializing LLM for judging...")
    llm = create_llm('judging', LLM_CONFIG)
    print(f"✅ Using {LLM_CONFIG['judging']['model']} "
          f"(temperature={LLM_CONFIG['judging']['temperature']})")

    # Load candidates
    print("\nLoading candidates...")
    clarity_candidates_path = os.path.join(backend_dir, "eval/data/candidates/clarity_candidates.json")
    rigor_candidates_path = os.path.join(backend_dir, "eval/data/candidates/rigor_candidates.json")

    clarity_candidates = load_json(clarity_candidates_path)
    rigor_candidates = load_json(rigor_candidates_path)

    print(f"Loaded {len(clarity_candidates)} clarity candidates")
    print(f"Loaded {len(rigor_candidates)} rigor candidates")

    # Filter clarity candidates
    print("\n" + "="*80)
    print("FILTERING CLARITY CANDIDATES")
    print("="*80)

    golden_clarity = filter_to_golden_n(
        candidates=clarity_candidates,
        llm=llm,
        n=final_golden_count
    )

    # Filter rigor candidates
    print("\n" + "="*80)
    print("FILTERING RIGOR CANDIDATES")
    print("="*80)

    golden_rigor = filter_to_golden_n(
        candidates=rigor_candidates,
        llm=llm,
        n=final_golden_count
    )

    # Print results
    print("\n" + "="*80)
    print("GOLDEN CLARITY DATASET")
    print("="*80)
    for i, ex in enumerate(golden_clarity, 1):
        print_example(ex, index=i)

    print("\n" + "="*80)
    print("GOLDEN RIGOR DATASET")
    print("="*80)
    for i, ex in enumerate(golden_rigor, 1):
        print_example(ex, index=i)

    # Print summary stats
    print_summary_stats(golden_clarity, "Golden Clarity")
    print_summary_stats(golden_rigor, "Golden Rigor")

    # Save golden datasets
    print("\n" + "="*80)
    print("SAVING GOLDEN DATASETS")
    print("="*80)

    golden_clarity_path = os.path.join(backend_dir, "eval/data/golden/golden_clarity_10.json")
    golden_rigor_path = os.path.join(backend_dir, "eval/data/golden/golden_rigor_10.json")

    save_json(golden_clarity, golden_clarity_path)
    save_json(golden_rigor, golden_rigor_path)

    # Also save in RAGAS format
    print("\nConverting to RAGAS format...")
    from datasets import Dataset

    clarity_ragas = Dataset.from_list([
        {
            "question": ex.get('reference_question', ex.get('question', '')),
            "contexts": [ex.get('reference_context', ex.get('context', ''))],
            "ground_truth": ex.get('reference_answer', ex.get('answer', '')),
            "issue_type": ex.get('issue_type'),
            "domain": ex.get('domain'),
            "severity": ex.get('severity'),
        }
        for ex in golden_clarity
    ])

    rigor_ragas = Dataset.from_list([
        {
            "question": ex.get('reference_question', ex.get('question', '')),
            "contexts": [ex.get('reference_context', ex.get('context', ''))],
            "ground_truth": ex.get('reference_answer', ex.get('answer', '')),
            "issue_type": ex.get('issue_type'),
            "domain": ex.get('domain'),
            "severity": ex.get('severity'),
        }
        for ex in golden_rigor
    ])

    clarity_ragas_path = os.path.join(backend_dir, "eval/data/golden/golden_clarity_ragas")
    rigor_ragas_path = os.path.join(backend_dir, "eval/data/golden/golden_rigor_ragas")

    clarity_ragas.save_to_disk(clarity_ragas_path)
    rigor_ragas.save_to_disk(rigor_ragas_path)

    print("✅ Saved RAGAS format datasets")

    print("\n✅ Step 3 complete!")
    print(f"   Golden clarity examples: {len(golden_clarity)}")
    print(f"   Golden rigor examples: {len(golden_rigor)}")
    print(f"   Average clarity score: {sum(ex['final_score'] for ex in golden_clarity) / len(golden_clarity):.2f}")
    print(f"   Average rigor score: {sum(ex['final_score'] for ex in golden_rigor) / len(golden_rigor):.2f}")


if __name__ == "__main__":
    main()
