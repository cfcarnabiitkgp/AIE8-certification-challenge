"""
Step 2: Evolve seed examples using EvolInstruct.

This script:
1. Loads seed examples from Step 1
2. Applies evolution operators to create diverse variants
3. Saves evolved candidates to JSON files
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from eval.golden_dataset.config import (
    GOLDEN_EVOLUTION_OPERATORS,
    LLM_CONFIG,
    PIPELINE_CONFIG
)
from eval.golden_dataset.utils import (
    load_json,
    save_json,
    create_llm,
    parse_json_response,
    print_summary_stats,
    print_example
)


def apply_evolution_operator(seed: dict, operator_name: str, llm) -> dict:
    """
    Apply evolution operator to create variant.

    Args:
        seed: Seed example dict
        operator_name: Name of evolution operator
        llm: LLM instance for evolution

    Returns:
        Evolved example dict (or None if failed)
    """
    operator = GOLDEN_EVOLUTION_OPERATORS[operator_name]

    # Format the prompt
    prompt = operator['prompt_template'].format(
        reference_question=seed.get('reference_question', ''),
        reference_context=seed.get('reference_context', ''),
        reference_answer=seed.get('reference_answer', ''),
        issue_type=seed.get('issue_type', 'unknown'),
        current_domain=seed.get('domain', 'general')
    )

    try:
        response = llm.invoke(prompt)
        evolved = parse_json_response(response.content)

        # Ensure critical fields exist - if LLM didn't return them, preserve from seed
        if 'reference_question' not in evolved:
            evolved['reference_question'] = seed.get('reference_question', '')
        if 'reference_context' not in evolved:
            evolved['reference_context'] = seed.get('reference_context', '')
        if 'reference_answer' not in evolved:
            evolved['reference_answer'] = seed.get('reference_answer', '')
        if 'issue_type' not in evolved:
            evolved['issue_type'] = seed.get('issue_type', 'unknown')
        if 'domain' not in evolved:
            evolved['domain'] = seed.get('domain', 'general')
        if 'severity' not in evolved:
            evolved['severity'] = seed.get('severity', 'info')

        # Preserve metadata and add evolution info
        evolved['evolution_operator'] = operator_name
        evolved['parent_seed_id'] = seed.get('seed_id', 'unknown')
        evolved['source'] = 'evolved'

        # Preserve guideline source if not in response
        if 'guideline_source_file' not in evolved:
            evolved['guideline_source_file'] = seed.get('guideline_source_file', 'unknown')

        return evolved

    except Exception as e:
        print(f"    ❌ Evolution failed for {operator_name}: {e}")
        return None


def evolve_seeds_to_candidates(
    seeds: list,
    llm,
    num_seeds_to_evolve: int,
    evolutions_per_seed: int
) -> list:
    """
    Evolve each seed into multiple candidates.

    Strategy:
    - Take top N seeds
    - Evolve each into M variants
    - Total: N seeds × (1 original + M evolved) candidates

    Args:
        seeds: List of seed examples
        llm: LLM instance for evolution
        num_seeds_to_evolve: Number of top seeds to evolve
        evolutions_per_seed: Number of evolved variants per seed

    Returns:
        List of all candidates (original seeds + evolved variants)
    """
    all_candidates = []

    # Select top seeds (for now, just take first N)
    selected_seeds = seeds[:num_seeds_to_evolve]
    print(f"Selected {len(selected_seeds)} seeds to evolve")

    # Define which operators to apply
    operators_to_apply = [
        "increase_realism",
        "increase_specificity",
        "add_distractor",
        "increase_subtlety",
    ]

    for i, seed in enumerate(selected_seeds, 1):
        print(f"\nEvolving seed {i}/{len(selected_seeds)}: [{seed.get('issue_type', 'unknown')}]")

        # Keep original seed
        seed_copy = seed.copy()
        seed_copy['evolution_operator'] = 'original'
        all_candidates.append(seed_copy)
        print(f"  ✅ Original seed added")

        # Apply evolution operators
        for j, operator in enumerate(operators_to_apply[:evolutions_per_seed], 1):
            print(f"  Applying {operator} ({j}/{evolutions_per_seed})...")

            evolved = apply_evolution_operator(seed, operator, llm)

            if evolved:
                all_candidates.append(evolved)
                print(f"    ✅ Evolved variant created")
            else:
                print(f"    ❌ Evolution failed, skipping")

    return all_candidates


def main():
    """Main function to evolve seed examples."""
    print("\n" + "="*80)
    print("STEP 2: EVOLVE SEEDS WITH EVOLINSTRUCT")
    print("="*80)

    # Get the backend directory (works whether run from backend/ or project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, '..', '..')

    # Load configuration
    num_seeds_to_evolve = PIPELINE_CONFIG['num_seeds_to_evolve']
    evolutions_per_seed = PIPELINE_CONFIG['evolutions_per_seed']

    # Create LLM for evolution
    print("\nInitializing LLM for evolution...")
    llm = create_llm('evolution', LLM_CONFIG)
    print(f"✅ Using {LLM_CONFIG['evolution']['model']} "
          f"(temperature={LLM_CONFIG['evolution']['temperature']})")

    # Load seeds
    print("\nLoading seeds...")
    clarity_seeds_path = os.path.join(backend_dir, "eval/data/seeds/clarity_seeds.json")
    rigor_seeds_path = os.path.join(backend_dir, "eval/data/seeds/rigor_seeds.json")

    clarity_seeds = load_json(clarity_seeds_path)
    rigor_seeds = load_json(rigor_seeds_path)

    print(f"Loaded {len(clarity_seeds)} clarity seeds")
    print(f"Loaded {len(rigor_seeds)} rigor seeds")

    # Evolve clarity seeds
    print("\n" + "="*80)
    print("EVOLVING CLARITY SEEDS")
    print("="*80)

    clarity_candidates = evolve_seeds_to_candidates(
        seeds=clarity_seeds,
        llm=llm,
        num_seeds_to_evolve=num_seeds_to_evolve,
        evolutions_per_seed=evolutions_per_seed
    )

    # Evolve rigor seeds
    print("\n" + "="*80)
    print("EVOLVING RIGOR SEEDS")
    print("="*80)

    rigor_candidates = evolve_seeds_to_candidates(
        seeds=rigor_seeds,
        llm=llm,
        num_seeds_to_evolve=num_seeds_to_evolve,
        evolutions_per_seed=evolutions_per_seed
    )

    # Print summary
    print_summary_stats(clarity_candidates, "Clarity Candidates")
    print_summary_stats(rigor_candidates, "Rigor Candidates")

    # Save candidates
    print("\n" + "="*80)
    print("SAVING CANDIDATES")
    print("="*80)

    # Create candidates directory if needed
    candidates_dir = os.path.join(backend_dir, "eval/data/candidates")
    os.makedirs(candidates_dir, exist_ok=True)

    clarity_candidates_path = os.path.join(backend_dir, "eval/data/candidates/clarity_candidates.json")
    rigor_candidates_path = os.path.join(backend_dir, "eval/data/candidates/rigor_candidates.json")

    save_json(clarity_candidates, clarity_candidates_path)
    save_json(rigor_candidates, rigor_candidates_path)

    print("\n✅ Step 2 complete!")
    print(f"   Clarity: {len(clarity_seeds[:num_seeds_to_evolve])} seeds → "
          f"{len(clarity_candidates)} candidates")
    print(f"   Rigor: {len(rigor_seeds[:num_seeds_to_evolve])} seeds → "
          f"{len(rigor_candidates)} candidates")


if __name__ == "__main__":
    main()
