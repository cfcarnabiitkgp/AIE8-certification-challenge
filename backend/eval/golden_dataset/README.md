# Golden Dataset Generation with EvolInstruct

This directory contains the pipeline for generating high-quality golden evaluation datasets using **EvolInstruct**.

## Overview

The pipeline creates **10 golden evaluation examples** each for Clarity and Rigor agents through a 3-step process:

1. **Generate Seeds** - Create initial examples from guideline PDFs
2. **Evolve with EvolInstruct** - Apply evolution operators to create diverse variants
3. **Filter to Golden 10** - Use LLM-as-judge to select the best examples

## Directory Structure

```
golden_dataset/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── config.py                    # Configuration (operators, domains, criteria)
├── utils.py                     # Helper functions
│
├── step1_generate_seeds.py      # Step 1: Generate seeds from guidelines
├── step2_evolve_candidates.py   # Step 2: Apply EvolInstruct evolution
├── step3_filter_golden.py       # Step 3: LLM-as-judge filtering
│
└── run_full_pipeline.py         # Run all steps end-to-end
```

## Quick Start

### Run Full Pipeline

```bash
# From backend directory
cd backend

# Run the complete pipeline (takes 1-2 hours)
python eval/golden_dataset/run_full_pipeline.py
```

This will:
1. Generate ~20 seed examples per agent type
2. Evolve top 10 seeds into ~50 candidates
3. Filter to golden 10 per agent type
4. Save results in multiple formats (JSON + RAGAS)

### Run Individual Steps

```bash
# Step 1: Generate seeds (30-45 min)
python eval/golden_dataset/step1_generate_seeds.py

# Step 2: Evolve candidates (30-45 min)
python eval/golden_dataset/step2_evolve_candidates.py

# Step 3: Filter to golden 10 (20-30 min)
python eval/golden_dataset/step3_filter_golden.py
```

## Configuration

Edit `config.py` to customize:

### Domains
```python
DOMAINS = [
    "machine_learning",
    "biology",
    "physics",
    "chemistry",
    "social_science",
    "economics"
]
```

### Evolution Operators
- `increase_realism` - Make examples more realistic
- `increase_specificity` - Make reference answers more specific
- `add_distractor` - Add correct content around flaws
- `increase_subtlety` - Make issues more subtle
- `combine_issues` - Combine multiple issues
- `diversify_domain` - Translate to different domains
- `create_positive_example` - Create corrected versions

### Pipeline Settings
```python
PIPELINE_CONFIG = {
    "num_seed_guidelines": 10,  # Guideline chunks to use
    "seeds_per_guideline": 2,   # Seeds per guideline
    "num_seeds_to_evolve": 10,  # Seeds to evolve
    "evolutions_per_seed": 4,   # Evolutions per seed
    "final_golden_count": 10,   # Final golden examples
}
```

### LLM Models
```python
LLM_CONFIG = {
    "seed_generation": {"model": "gpt-4o", "temperature": 0.7},
    "evolution": {"model": "gpt-4o", "temperature": 0.8},
    "judging": {"model": "gpt-4o", "temperature": 0.0},
}
```

## Output Files

The pipeline generates:

```
backend/eval/data/
├── seeds/
│   ├── clarity_seeds.json           # ~20 clarity seeds
│   └── rigor_seeds.json             # ~20 rigor seeds
│
├── candidates/
│   ├── clarity_candidates.json      # ~50 clarity candidates
│   └── rigor_candidates.json        # ~50 rigor candidates
│
└── golden/
    ├── golden_clarity_10.json       # 10 golden clarity examples
    ├── golden_rigor_10.json         # 10 golden rigor examples
    ├── golden_clarity_ragas/        # RAGAS format (Hugging Face Dataset)
    └── golden_rigor_ragas/          # RAGAS format (Hugging Face Dataset)
```

## Golden Dataset Format

Each golden example contains:

```json
{
  "reference_question": "The flawed paper section (2-4 sentences)",
  "reference_context": "The relevant guideline from PDFs",
  "reference_answer": "Expected suggestion (specific and actionable)",
  "issue_type": "vague_language | undefined_term | ...",
  "domain": "machine_learning | biology | ...",
  "severity": "info | warning | error",
  "section_type": "abstract | methods | results | ...",

  "quality_scores": {
    "realism": 4.5,
    "clarity_of_issue": 4.8,
    "pedagogical_value": 4.6,
    "actionability": 4.9,
    "guideline_alignment": 5.0,
    "overall_quality": 4.7
  },
  "weighted_score": 4.68,
  "final_score": 5.18,

  "evolution_operator": "increase_realism",
  "parent_seed_id": "clarity_seed_003",
  "source": "evolved"
}
```

## RAGAS Format

The golden datasets are also saved in RAGAS format:

```python
{
  "question": str,      # The flawed section (reference_question)
  "contexts": [str],    # The guideline (reference_context as list)
  "ground_truth": str,  # Expected suggestion (reference_answer)
  "issue_type": str,    # Metadata
  "domain": str,        # Metadata
  "severity": str       # Metadata
}
```

## Evaluation with RAGAS

After generating the golden dataset:

```bash
# Run RAGAS evaluation
python backend/eval/evaluate_golden_with_ragas.py
```

This will:
1. Load golden datasets
2. Run Clarity and Rigor agents
3. Evaluate with RAGAS metrics:
   - Faithfulness
   - Answer Relevancy
   - Context Precision/Recall
   - Answer Correctness/Similarity
4. Save results to `backend/eval/results/`

## Quality Criteria

Examples are scored on (1-5 scale):

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Realism** | 20% | Sounds like real academic paper? |
| **Clarity of Issue** | 15% | Issue clearly identifiable? |
| **Pedagogical Value** | 20% | Teaches something valuable? |
| **Actionability** | 20% | Suggestion specific and actionable? |
| **Guideline Alignment** | 15% | Guideline matches the issue? |
| **Overall Quality** | 10% | Overall assessment |

## Diversity Selection

When filtering to golden 10, diversity bonuses are applied:
- **New issue type**: +0.5 to score
- **New domain**: +0.3 to score

This ensures the golden dataset covers multiple issue types and domains.

## Expected Timeline

| Step | Time | Output |
|------|------|--------|
| Step 1: Generate Seeds | 30-45 min | 20 seeds per agent |
| Step 2: Evolve Candidates | 30-45 min | 50 candidates per agent |
| Step 3: Filter to Golden 10 | 20-30 min | 10 golden per agent |
| **Total** | **1-2 hours** | **10 + 10 golden examples** |

## Cost Estimate

Using GPT-4o:
- **Seed generation**: ~40 LLM calls × $0.01 = **$0.40**
- **Evolution**: ~80 LLM calls × $0.01 = **$0.80**
- **Judging**: ~100 LLM calls × $0.01 = **$1.00**
- **Total**: ~**$2-3** for the full pipeline

## Troubleshooting

### Import Errors
Make sure you're running from the `backend` directory:
```bash
cd backend
python eval/golden_dataset/run_full_pipeline.py
```

### API Rate Limits
If you hit OpenAI rate limits, you can:
1. Add delays between API calls in `utils.py`
2. Reduce `num_seed_guidelines` or `evolutions_per_seed` in `config.py`
3. Run steps individually with breaks

### Low Quality Scores
If examples score low:
1. Check the prompts in `step1_generate_seeds.py`
2. Adjust quality criteria weights in `config.py`
3. Manually review and edit examples in JSON files

## Advanced Usage

### Custom Evolution Operators

Add new operators in `config.py`:

```python
GOLDEN_EVOLUTION_OPERATORS["my_operator"] = {
    "description": "My custom operator",
    "prompt_template": """
    Given: {reference_question}
    Create a variant that...
    """
}
```

Then use it in `step2_evolve_candidates.py`.

### Manual Curation

You can manually edit the JSON files at any stage:
1. Edit seeds after Step 1
2. Edit candidates after Step 2
3. Edit golden examples after Step 3

The pipeline will use your edited versions.

### Scaling Up

To generate more examples:
1. Increase `final_golden_count` in `config.py`
2. Increase `num_seeds_to_evolve` for more diversity
3. Run the pipeline multiple times and merge results

## Citation

This implementation is based on:
- **WizardLM**: EvolInstruct methodology ([Xu et al., 2023](https://arxiv.org/abs/2304.12244))
- **RAGAS**: Evaluation framework ([Es et al., 2023](https://arxiv.org/abs/2309.15217))

## Support

For issues or questions:
1. Check this README
2. Review the generated JSON files
3. Check logs for error messages
4. Adjust configuration in `config.py`
