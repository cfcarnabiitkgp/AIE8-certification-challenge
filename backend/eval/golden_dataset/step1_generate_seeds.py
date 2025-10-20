"""
Step 1: Generate high-quality seed examples from guideline PDFs.

This script:
1. Loads guideline PDFs (e.g. for clarity and rigor)
2. Selects diverse guideline chunks
3. Generates high-quality seed examples using LLM
4. Saves seeds to JSON files
"""

import sys
import os
import random

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from eval.golden_dataset.config import (
    DOMAINS,
    LLM_CONFIG,
    PIPELINE_CONFIG
)

from eval.golden_dataset.utils import (
    load_guideline_chunks,
    select_diverse_guideline_chunks,
    create_llm,
    parse_json_response,
    save_json,
    print_summary_stats,
    add_seed_ids
)


def generate_high_quality_clarity_seed(guideline_chunk, domain: str, llm) -> dict:
    """
    Generate a HIGH-QUALITY synthetic seed example for clarity issues.

    Args:
        guideline_chunk: A guideline document chunk
        domain: Academic domain for the example
        llm: LLM instance for generation

    Returns:
        Seed example dict
    """
    prompt = f"""
You are an expert peer reviewer creating a HIGH-QUALITY synthetic evaluation example.

**Guideline to test:**
{guideline_chunk.page_content}

**Your task:**
Generate a realistic paper section that violates this guideline. This will be used to evaluate an AI peer review agent.

**Requirements for high quality**:
1. **Realism**: Write as if from a real academic paper in {domain}
2. **Context**: Provide 2-4 sentences (not just one isolated sentence)
3. **Natural flaw**: The clarity issue should be subtle and realistic, not artificially obvious
4. **Domain-specific**: Use actual terminology from {domain}
5. **Pedagogical**: The example should teach something valuable about good writing

**Output format** (JSON):
{{
    "reference_question": "The flawed paper section (2-4 sentences with realistic context)",
    "reference_context": "The exact guideline text that applies (quote from the guideline above)",
    "reference_answer": "Specific, actionable suggestion to fix the issue (include example wording)",
    "issue_type": "vague_language | undefined_term | complex_sentence | ambiguous_reference | missing_definition | passive_voice | ...",
    "severity": "info | warning | error",
    "domain": "{domain}",
    "section_type": "abstract | introduction | methods | results | discussion | conclusion"
}}

**Example of HIGH quality vs LOW quality**:

❌ LOW quality (too obvious, artificial):
{{
    "reference_question": "The thing works good and has high accuracy.",
    "reference_answer": "Be more specific."
}}

✅ HIGH quality (realistic, pedagogical):
{{
    "reference_question": "Our novel deep learning architecture demonstrates superior performance on the benchmark dataset. The model achieves good results across multiple metrics, significantly outperforming existing approaches in most scenarios.",
    "reference_answer": "Replace vague qualitative terms with specific quantitative metrics. For example: 'The model achieves 94.2% accuracy (±0.3%), 91.7% F1-score, and 89.3% recall on the CIFAR-10 test set, outperforming the previous state-of-the-art by 2.1 percentage points in accuracy.'",
    "issue_type": "vague_language",
    "severity": "warning"
}}

Now generate your high-quality example:
"""

    try:
        response = llm.invoke(prompt)
        seed = parse_json_response(response.content)

        # Add metadata
        seed['source'] = 'guideline_generated'
        seed['guideline_source_file'] = guideline_chunk.metadata.get('source_file', 'unknown')

        return seed

    except Exception as e:
        print(f"❌ Error generating clarity seed: {e}")
        return None


def generate_high_quality_rigor_seed(guideline_chunk, domain: str, llm) -> dict:
    """
    Generate a HIGH-QUALITY synthetic seed example for rigor issues.

    Args:
        guideline_chunk: A guideline document chunk
        domain: Academic domain for the example
        llm: LLM instance for generation

    Returns:
        Seed example dict
    """
    prompt = f"""
You are an expert peer reviewer creating a HIGH-QUALITY synthetic evaluation example.

**Guideline to test:**
{guideline_chunk.page_content}

**Your task:**
Generate a realistic paper section (methods, experiments, or results) that violates this rigor guideline.

**Requirements for high quality**:
1. **Realism**: Write as if from a real {domain} paper
2. **Context**: Provide 2-4 sentences describing an experiment or method
3. **Subtle flaw**: The rigor issue should be realistic (what you'd actually see in papers)
4. **Domain-specific**: Use actual experimental/methodological terminology from {domain}
5. **Pedagogical**: Should teach reviewers what to look for

**Output format** (JSON):
{{
    "reference_question": "The flawed experimental/methods section (2-4 sentences)",
    "reference_context": "The exact guideline text that applies",
    "reference_answer": "Specific suggestion to improve rigor (mention what's missing and how to add it)",
    "issue_type": "missing_baseline | no_statistical_test | insufficient_sample_size | missing_control | unreported_hyperparameters | missing_error_bars | ...",
    "severity": "info | warning | error",
    "domain": "{domain}",
    "section_type": "methods | experiments | results | analysis"
}}

**Example of HIGH quality**:

✅ HIGH quality (realistic experimental flaw):
{{
    "reference_question": "We trained our neural network on the ImageNet dataset and evaluated it on the test set. Our model achieved 76.3% top-1 accuracy, demonstrating the effectiveness of our proposed architecture. The training process converged after 100 epochs using the Adam optimizer.",
    "reference_answer": "Add statistical significance testing and error estimates. Specifically: (1) Report mean and standard deviation over multiple runs (e.g., 5 random seeds), (2) Conduct a paired t-test or Wilcoxon signed-rank test comparing to baseline models, (3) Report confidence intervals for the accuracy metric (e.g., '76.3% ± 0.4% at 95% CI'). Example: 'Our model achieved 76.3% ± 0.4% top-1 accuracy (mean ± std over 5 runs), significantly outperforming the ResNet-50 baseline (74.1% ± 0.3%, p < 0.01, paired t-test).'",
    "issue_type": "no_statistical_test",
    "severity": "error"
}}

Now generate your high-quality example:
"""

    try:
        response = llm.invoke(prompt)
        seed = parse_json_response(response.content)

        # Add metadata
        seed['source'] = 'guideline_generated'
        seed['guideline_source_file'] = guideline_chunk.metadata.get('source_file', 'unknown')

        return seed

    except Exception as e:
        print(f"❌ Error generating rigor seed: {e}")
        return None


def generate_diverse_seeds(
    guideline_chunks,
    agent_type: str,
    llm,
    num_chunks: int,
    seeds_per_guideline: int
) -> list:
    """
    Generate diverse seeds across multiple guidelines and domains.

    Args:
        guideline_chunks: List of guideline chunks
        agent_type: 'clarity' or 'rigor'
        llm: LLM instance for generation
        num_chunks: Number of guideline chunks to use
        seeds_per_guideline: Number of seeds per guideline

    Returns:
        List of seed examples
    """
    print(f"\n{'='*80}")
    print(f"Generating {agent_type.upper()} seeds")
    print(f"{'='*80}")

    # Select diverse chunks
    selected_chunks = select_diverse_guideline_chunks(guideline_chunks, num_chunks)
    print(f"Selected {len(selected_chunks)} diverse guideline chunks")

    all_seeds = []

    for i, chunk in enumerate(selected_chunks, 1):
        print(f"\nProcessing chunk {i}/{len(selected_chunks)}...")

        # Generate seeds in different domains
        domains_to_use = random.sample(DOMAINS, k=min(seeds_per_guideline, len(DOMAINS)))

        for domain in domains_to_use:
            print(f"  Generating {domain} example...")

            if agent_type == "clarity":
                seed = generate_high_quality_clarity_seed(chunk, domain, llm)
            else:  # rigor
                seed = generate_high_quality_rigor_seed(chunk, domain, llm)

            if seed:
                all_seeds.append(seed)
                print(f"✅ Generated: [{seed.get('issue_type', 'unknown')}]")
            else:
                print(f"❌ Failed to generate seed")

    return all_seeds


def main():
    """Main function to generate seed examples."""
    print("\n" + "="*80)
    print("STEP 1: GENERATE SEED EXAMPLES FROM GUIDELINES")
    print("="*80)

    # Load configuration
    num_seed_guidelines = PIPELINE_CONFIG['num_seed_guidelines']
    seeds_per_guideline = PIPELINE_CONFIG['seeds_per_guideline']

    # Create LLM for seed generation
    print("\nInitializing LLM for seed generation...")
    llm = create_llm('seed_generation', LLM_CONFIG)
    print(f"✅ Using {LLM_CONFIG['seed_generation']['model']} "
          f"(temperature={LLM_CONFIG['seed_generation']['temperature']})")

    # Load guideline chunks
    print("\nLoading guideline PDFs...")
    # Get the backend directory (works whether run from backend/ or project root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(script_dir, '..', '..')
    clarity_path = os.path.join(backend_dir, "app/resources/clarity_docs/*.pdf")
    rigor_path = os.path.join(backend_dir, "app/resources/rigor_docs/*.pdf")

    clarity_chunks, rigor_chunks = load_guideline_chunks(
        clarity_docs_path=clarity_path,
        rigor_docs_path=rigor_path
    )

    print(f"✅ Loaded {len(clarity_chunks)} clarity guideline chunks")
    print(f"✅ Loaded {len(rigor_chunks)} rigor guideline chunks")

    # Generate clarity seeds
    clarity_seeds = generate_diverse_seeds(
        guideline_chunks=clarity_chunks,
        agent_type="clarity",
        llm=llm,
        num_chunks=num_seed_guidelines,
        seeds_per_guideline=seeds_per_guideline
    )

    # Generate rigor seeds
    rigor_seeds = generate_diverse_seeds(
        guideline_chunks=rigor_chunks,
        agent_type="rigor",
        llm=llm,
        num_chunks=num_seed_guidelines,
        seeds_per_guideline=seeds_per_guideline
    )

    # Add seed IDs
    clarity_seeds = add_seed_ids(clarity_seeds, prefix="clarity_seed")
    rigor_seeds = add_seed_ids(rigor_seeds, prefix="rigor_seed")

    # Print summary statistics
    print_summary_stats(clarity_seeds, "Clarity Seeds")
    print_summary_stats(rigor_seeds, "Rigor Seeds")

    # Save seeds
    print("\n" + "="*80)
    print("SAVING SEEDS")
    print("="*80)

    # Use absolute paths for saving
    clarity_seeds_path = os.path.join(backend_dir, "eval/data/seeds/clarity_seeds.json")
    rigor_seeds_path = os.path.join(backend_dir, "eval/data/seeds/rigor_seeds.json")

    save_json(clarity_seeds, clarity_seeds_path)
    save_json(rigor_seeds, rigor_seeds_path)

    print("\n✅ Step 1 complete!")
    print(f"   Generated {len(clarity_seeds)} clarity seeds")
    print(f"   Generated {len(rigor_seeds)} rigor seeds")


if __name__ == "__main__":
    main()
