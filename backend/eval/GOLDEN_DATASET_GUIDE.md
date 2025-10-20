# Golden Dataset Generation with EvolInstruct - Quick Start Guide

This guide shows you how to create 10 high-quality golden evaluation examples for both Clarity and Rigor agents using EvolInstruct.

## What You'll Get

- **10 golden Clarity examples** - High-quality test cases for clarity issues
- **10 golden Rigor examples** - High-quality test cases for rigor issues
- **RAGAS-compatible format** - Ready for evaluation with RAGAS metrics
- **Diverse coverage** - Multiple domains, issue types, and difficulty levels

## Prerequisites

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -e .
   ```

   This will install `ragas` and `datasets` packages automatically.

2. **Set up environment variables**:
   Make sure your `.env` file has:
   ```
   OPENAI_API_KEY=your_key_here
   ```

3. **Ensure guideline PDFs are available**:
   - `backend/app/resources/clarity_docs/*.pdf`
   - `backend/app/resources/rigor_docs/*.pdf`

## Quick Start (3 Steps)

### Option 1: Run Full Pipeline (Recommended)

```bash
cd backend
python eval/golden_dataset/run_full_pipeline.py
```

This runs all 3 steps automatically:
1. Generate seeds from guidelines (~30-45 min)
2. Evolve seeds with EvolInstruct (~30-45 min)
3. Filter to golden 10 with LLM-as-judge (~20-30 min)

**Total time**: 1-2 hours
**Total cost**: ~$2-3 (using GPT-4o)

### Option 2: Run Steps Individually

If you want more control, run each step separately:

```bash
cd backend

# Step 1: Generate seeds
python eval/golden_dataset/step1_generate_seeds.py

# Step 2: Evolve candidates
python eval/golden_dataset/step2_evolve_candidates.py

# Step 3: Filter to golden 10
python eval/golden_dataset/step3_filter_golden.py
```

You can review and manually edit the JSON files between steps.

## What Gets Generated

After running the pipeline, you'll have:

```
backend/eval/data/
├── seeds/
│   ├── clarity_seeds.json           # ~20 initial clarity seeds
│   └── rigor_seeds.json             # ~20 initial rigor seeds
│
├── candidates/
│   ├── clarity_candidates.json      # ~50 evolved clarity candidates
│   └── rigor_candidates.json        # ~50 evolved rigor candidates
│
└── golden/
    ├── golden_clarity_10.json       # ⭐ 10 golden clarity examples
    ├── golden_rigor_10.json         # ⭐ 10 golden rigor examples
    ├── golden_clarity_ragas/        # ⭐ RAGAS format (for evaluation)
    └── golden_rigor_ragas/          # ⭐ RAGAS format (for evaluation)
```

## Evaluate with RAGAS

After generating the golden dataset:

```bash
cd backend
python eval/evaluate_golden_with_ragas.py
```

This will:
1. Run your Clarity and Rigor agents on the golden examples
2. Evaluate with 6 RAGAS metrics:
   - Faithfulness
   - Answer Relevancy
   - Context Precision
   - Context Recall
   - Answer Correctness
   - Answer Similarity
3. Save results to `backend/eval/results/`:
   - `clarity_ragas_golden.csv`
   - `rigor_ragas_golden.csv`

## Understanding the Output

### Example Golden Dataset Entry

```json
{
  "reference_question": "Our novel deep learning architecture demonstrates superior performance on the benchmark dataset. The model achieves good results across multiple metrics, significantly outperforming existing approaches in most scenarios.",

  "reference_context": "Avoid vague qualitative terms like 'good', 'high', 'significant' without quantitative backing. Always provide specific metrics with numerical values.",

  "reference_answer": "Replace vague qualitative terms with specific quantitative metrics. For example: 'The model achieves 94.2% accuracy (±0.3%), 91.7% F1-score, and 89.3% recall on the CIFAR-10 test set, outperforming the previous state-of-the-art by 2.1 percentage points in accuracy.'",

  "issue_type": "vague_language",
  "domain": "machine_learning",
  "severity": "warning",

  "quality_scores": {
    "realism": 4.8,
    "clarity_of_issue": 4.9,
    "pedagogical_value": 4.7,
    "actionability": 5.0,
    "guideline_alignment": 5.0,
    "overall_quality": 4.8
  },
  "weighted_score": 4.82,
  "final_score": 5.12
}
```

### RAGAS Format (for evaluation)

```python
{
  "question": "The flawed section...",         # What agent analyzes
  "contexts": ["The guideline..."],           # What should be retrieved
  "ground_truth": "Expected suggestion...",   # What agent should output
  "issue_type": "vague_language",             # Metadata
  "domain": "machine_learning"                # Metadata
}
```

## Customization

### Change Number of Examples

Edit `backend/eval/golden_dataset/config.py`:

```python
PIPELINE_CONFIG = {
    "final_golden_count": 20,  # Generate 20 instead of 10
    # ... other settings
}
```

### Add More Domains

Edit `backend/eval/golden_dataset/config.py`:

```python
DOMAINS = [
     "machine_learning",
    "statistics",
    "operations_research",
    "psychology",      # Add new domain
    "linguistics",     # Add new domain
]
```

### Adjust Evolution Operators

Enable/disable operators in `backend/eval/golden_dataset/step2_evolve_candidates.py`:

```python
operators_to_apply = [
    "increase_realism",
    "increase_specificity",
    "add_distractor",
    "increase_subtlety",
    # "combine_issues",           # Uncomment to enable
    # "diversify_domain",         # Uncomment to enable
    # "create_positive_example",  # Uncomment to enable
]
```

### Use Different LLM Models

Edit `backend/eval/golden_dataset/config.py`:

```python
LLM_CONFIG = {
    "seed_generation": {
        "model": "gpt-4o-mini",    # Cheaper option
        "temperature": 0.7,
    },
    # ...
}
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'ragas'"

Install dependencies:
```bash
cd backend
pip install ragas datasets
```

Or reinstall the project:
```bash
cd backend
pip install -e .
```

### "No such file or directory: backend/app/resources/clarity_docs"

Make sure your guideline PDFs are in the correct location:
- `backend/app/resources/clarity_docs/*.pdf`
- `backend/app/resources/rigor_docs/*.pdf`

### OpenAI Rate Limits

If you hit rate limits:
1. Add delays between API calls
2. Reduce the number of seeds/evolutions in `config.py`
3. Run steps individually with breaks between them

### Low Quality Scores

If examples score below 4.0:
1. Check your guideline PDFs for quality
2. Review the prompts in `step1_generate_seeds.py`
3. Manually edit low-scoring examples in the JSON files
4. Re-run Step 3 to filter again

## Manual Review

You can manually review and edit examples at any stage:

1. **After Step 1**: Edit `backend/eval/data/seeds/*.json`
2. **After Step 2**: Edit `backend/eval/data/candidates/*.json`
3. **After Step 3**: Edit `backend/eval/data/golden/*.json`

The pipeline will use your edited versions.


## Support

For detailed documentation:
- See `backend/eval/golden_dataset/README.md`
- Review configuration in `backend/eval/golden_dataset/config.py`
- Check individual step scripts for implementation details

## Summary

**To get started right now**:

```bash
cd backend
python eval/golden_dataset/run_full_pipeline.py
```

Wait 1-2 hours, and you'll have:
- 10 golden Clarity examples
- 10 golden Rigor examples
- Ready for RAGAS evaluation

**That's it!** 🎉
