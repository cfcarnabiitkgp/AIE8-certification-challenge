"""
Configuration for golden dataset generation using EvolInstruct.

This module defines:
- Evolution operators for EvolInstruct
- Domains to cover
- Quality criteria for filtering
- LLM models for generation and judging
"""

# Domains to generate examples across
DOMAINS = [
    "machine_learning",
    "statistics",
    "operations_research",
]

# Evolution operators for EvolInstruct
GOLDEN_EVOLUTION_OPERATORS = {
    "increase_realism": {
        "description": "Make the example even more realistic and natural",
        "prompt_template": """
Given this synthetic example:
Question: {reference_question}
Context: {reference_context}
Answer: {reference_answer}

Create a MORE REALISTIC variant:
- Make it sound even more like a real paper section
- Add natural transitions and connecting phrases
- Include realistic details (dataset names, specific numbers, etc.)
- Make the flaw more subtle and natural (not artificially obvious)

Keep the same issue type and guideline, but increase realism.

Return evolved example in same JSON format:
{{
    "reference_question": "...",
    "reference_context": "...",
    "reference_answer": "...",
    "issue_type": "...",
    "severity": "...",
    "domain": "...",
    "section_type": "..."
}}
"""
    },

    "increase_specificity": {
        "description": "Make reference answer more specific and actionable",
        "prompt_template": """
Given this example:
Question: {reference_question}
Answer: {reference_answer}

Create a variant with MORE SPECIFIC reference answer:
- Include exact wording suggestions (show before/after)
- Provide concrete examples of fixes
- Reference specific metrics, methods, terminology
- Make it highly pedagogical (teaches good writing/rigor)

Example of improvement:
❌ Before: "Be more specific about the results."
✅ After: "Replace 'good results' with specific metrics. For example: 'Our model achieved 94.2% accuracy (±0.3%) and 91.7% F1-score on the test set.'"

Return evolved example in same JSON format with the improved reference_answer.
"""
    },

    "add_distractor": {
        "description": "Add correct content around the flaw to test precision",
        "prompt_template": """
Given this flawed excerpt:
Question: {reference_question}
Issue: {issue_type}

Create a variant with DISTRACTORS:
- Add 1-2 sentences of CORRECT, clear content before/after the flaw
- The flaw should still be present but embedded in mostly-good text
- Tests if the agent can identify the specific issue amid good content
- Makes it more realistic (real papers mix good and bad)

Return evolved example with the flaw still clearly identifiable in same JSON format.
"""
    },

    "increase_subtlety": {
        "description": "Make the issue more subtle and borderline",
        "prompt_template": """
Given this example:
Question: {reference_question}
Issue: {issue_type}

Create a MORE SUBTLE variant:
- Make the violation borderline (not obvious)
- Use context-dependent ambiguity
- Example: "It improved performance" where "It" is somewhat inferrable but still unclear
- Tests if agent catches subtle issues vs only obvious ones

The issue should still exist, but be harder to detect.

Return evolved example in same JSON format.
"""
    },

    "combine_issues": {
        "description": "Combine multiple clarity/rigor issues into one section",
        "prompt_template": """
Given this example with one issue:
Question: {reference_question}
Issue: {issue_type}

Create a variant with MULTIPLE issues:
- Keep the original issue
- Add 1-2 MORE related issues (for clarity: vague language + undefined term, for rigor: missing baseline + no statistical test)
- Make it realistic (issues often co-occur in real papers)
- The agent should ideally identify ALL issues

Return evolved example with:
- reference_question: Section with multiple issues
- reference_answer: Suggestions addressing ALL issues (can be a combined text)
- issue_type: Keep the primary issue type (metadata only)
"""
    },

    "diversify_domain": {
        "description": "Translate to a different academic domain",
        "prompt_template": """
Given this example from {current_domain}:
Question: {reference_question}
Issue: {issue_type}

Create a variant in a DIFFERENT domain:
- Choose from: [machine learning, biology, physics, chemistry, social science, economics, psychology, linguistics]
- Keep the same clarity/rigor issue type
- Use appropriate terminology and writing style for that domain
- Ensure the issue and fix remain valid in the new domain

Return evolved example in the new domain in same JSON format.
Update the "domain" field to the new domain.
"""
    },

    "create_positive_example": {
        "description": "Create a corrected version (no issues)",
        "prompt_template": """
Given this flawed example:
Question (flawed): {reference_question}
Issue: {issue_type}
Fix: {reference_answer}

Create a CORRECTED version (positive example):
- Apply the suggested fix completely
- Make it a model of good clarity/rigor
- This tests if agent has false positives (flags good content)

Return in JSON format:
{{
    "reference_question": "The CORRECTED, high-quality text",
    "reference_context": "{reference_context}",
    "reference_answer": "No issues found. This section demonstrates good [clarity/rigor practice].",
    "issue_type": "positive_example",
    "severity": "none",
    "domain": "{current_domain}",
    "section_type": "..."
}}
"""
    }
}

# Quality criteria for LLM-as-judge filtering
QUALITY_CRITERIA = {
    "realism": {
        "weight": 0.20,
        "description": "Is this realistic? Would you find this in a real academic paper?",
        "scale": "1=Artificially constructed, unrealistic; 5=Indistinguishable from real paper"
    },
    "clarity_of_issue": {
        "weight": 0.15,
        "description": "Is the issue clearly identifiable by a reviewer?",
        "scale": "1=Unclear what the problem is; 5=Issue is clear and well-defined"
    },
    "pedagogical_value": {
        "weight": 0.20,
        "description": "Does this teach something valuable?",
        "scale": "1=Trivial or obvious; 5=Highly instructive, reveals subtle issues"
    },
    "actionability": {
        "weight": 0.20,
        "description": "Is the reference answer specific and actionable?",
        "scale": "1=Vague, unhelpful; 5=Specific, concrete, immediately usable"
    },
    "guideline_alignment": {
        "weight": 0.15,
        "description": "Does the reference context match the issue?",
        "scale": "1=Guideline doesn't match; 5=Perfect alignment"
    },
    "overall_quality": {
        "weight": 0.10,
        "description": "Overall assessment",
        "scale": "1=Poor quality, don't include; 5=Excellent, must include"
    }
}

# LLM models for different tasks
LLM_CONFIG = {
    "seed_generation": {
        "model": "gpt-4o",  # High quality for seed generation
        "temperature": 0.7,  # Some creativity
    },
    "evolution": {
        "model": "gpt-4o",  # High quality for evolution
        "temperature": 0.8,  # More creativity for diversity
    },
    "judging": {
        "model": "gpt-4o",  # Consistent judging
        "temperature": 0.0,  # Deterministic for scoring
    }
}

# Pipeline configuration
PIPELINE_CONFIG = {
    "num_seed_guidelines": 10,  # Number of guideline chunks to use for seeds
    "seeds_per_guideline": 2,   # Number of seeds to generate per guideline
    "num_seeds_to_evolve": 10,  # Number of top seeds to evolve
    "evolutions_per_seed": 4,   # Number of evolved variants per seed
    "final_golden_count": 10,   # Final number of golden examples to select
}

# Diversity bonus for selection
DIVERSITY_CONFIG = {
    "issue_type_bonus": 0.5,  # Bonus for new issue type
    "domain_bonus": 0.3,      # Bonus for new domain
}
