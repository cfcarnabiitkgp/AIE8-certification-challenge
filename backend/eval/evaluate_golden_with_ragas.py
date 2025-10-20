"""
Evaluate agents using golden dataset with RAGAS metrics.

This script:
1. Loads golden datasets (in RAGAS format)
2. Runs Clarity and Rigor agents on each example
3. Collects agent outputs as 'answer' field
4. Evaluates with RAGAS metrics
5. Saves results and analysis
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datasets import Dataset, load_from_disk
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
    answer_similarity
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
import pandas as pd

from app.agents.clarity.clarity_agent import ClarityAgent
from app.agents.rigor.rigor_agent import RigorAgent
from app.services.vector_store import VectorStoreService


async def run_agent_on_dataset(agent, dataset, agent_name: str) -> list:
    """
    Run agent on each example in the dataset.

    Args:
        agent: Agent instance (ClarityAgent or RigorAgent)
        dataset: RAGAS dataset
        agent_name: Name of agent for logging

    Returns:
        List of results with agent answers added
    """
    print(f"\n{'='*80}")
    print(f"Running {agent_name} on {len(dataset)} examples")
    print(f"{'='*80}")

    results = []

    for i, example in enumerate(dataset, 1):
        print(f"\nExample {i}/{len(dataset)}: [{example.get('issue_type', 'unknown')}]")

        # Format as section for agent
        section = {
            "title": "Test Section",
            "content": example["question"],  # The flawed section
            "line_start": 1,
            "line_end": 10
        }

        try:
            # Run agent
            suggestions = await agent.analyze(section)

            # Format agent's output as answer
            if suggestions and len(suggestions) > 0:
                # Combine all suggestions into one answer
                answer_parts = []
                for s in suggestions:
                    desc = s.get('description', s.get('suggestion', 'No description'))
                    answer_parts.append(f"- {desc}")
                answer = "\n".join(answer_parts)
            else:
                answer = "No issues found."

            print(f"  Agent response: {answer[:100]}...")

        except Exception as e:
            print(f"  ❌ Error running agent: {e}")
            answer = f"Error: {str(e)}"

        # Add answer to the example
        results.append({
            "question": example["question"],
            "contexts": example["contexts"],
            "ground_truth": example["ground_truth"],
            "answer": answer,  # ← Agent's actual output

            # Metadata
            "issue_type": example.get("issue_type"),
            "domain": example.get("domain"),
            "severity": example.get("severity"),
        })

    return results


async def main():
    """Main evaluation function."""
    print("\n" + "="*80)
    print("EVALUATE GOLDEN DATASET WITH RAGAS")
    print("="*80)

    # Get the backend directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(script_dir)

    # Step 1: Load golden datasets
    print("\nStep 1: Loading golden datasets...")

    try:
        clarity_dataset_path = os.path.join(backend_dir, "eval/data/golden/golden_clarity_ragas")
        rigor_dataset_path = os.path.join(backend_dir, "eval/data/golden/golden_rigor_ragas")

        clarity_dataset = load_from_disk(clarity_dataset_path)
        rigor_dataset = load_from_disk(rigor_dataset_path)
        print(f"✅ Loaded {len(clarity_dataset)} clarity examples")
        print(f"✅ Loaded {len(rigor_dataset)} rigor examples")
    except Exception as e:
        print(f"❌ Error loading datasets: {e}")
        print("\nMake sure you've run the golden dataset generation pipeline first:")
        print("  python eval/golden_dataset/run_full_pipeline.py")
        return

    # Step 2: Initialize agents
    print("\nStep 2: Initializing agents...")

    try:
        vector_store = VectorStoreService()
        clarity_agent = ClarityAgent(vector_store=vector_store)
        rigor_agent = RigorAgent(vector_store=vector_store)
        print("✅ Agents initialized")
    except Exception as e:
        print(f"❌ Error initializing agents: {e}")
        return

    # Step 3: Run agents and collect answers
    print("\nStep 3: Running agents on golden datasets...")

    clarity_results = await run_agent_on_dataset(
        agent=clarity_agent,
        dataset=clarity_dataset,
        agent_name="ClarityAgent"
    )

    rigor_results = await run_agent_on_dataset(
        agent=rigor_agent,
        dataset=rigor_dataset,
        agent_name="RigorAgent"
    )

    # Convert to Dataset
    clarity_results_ds = Dataset.from_list(clarity_results)
    rigor_results_ds = Dataset.from_list(rigor_results)

    print(f"\n✅ Collected {len(clarity_results_ds)} clarity results")
    print(f"✅ Collected {len(rigor_results_ds)} rigor results")

    # Step 4: Evaluate with RAGAS
    print("\n" + "="*80)
    print("Step 4: Evaluating with RAGAS metrics")
    print("="*80)

    # Define metrics
    metrics = [
        faithfulness,           # Are suggestions grounded in guidelines?
        answer_relevancy,       # Are suggestions relevant to the flawed section?
        context_precision,      # Did agent retrieve the right guideline?
        context_recall,         # Did agent retrieve all relevant guidelines?
        answer_correctness,     # How correct vs ground_truth?
        answer_similarity       # Semantic similarity to ground_truth
    ]

    print("\nMetrics to evaluate:")
    for metric in metrics:
        print(f"  - {metric.name}")

    # Initialize LLM and embeddings for RAGAS
    print("\nInitializing LLM and embeddings for RAGAS...")
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    embeddings = OpenAIEmbeddings()

    # Evaluate Clarity Agent
    print("\n" + "="*80)
    print("EVALUATING CLARITY AGENT")
    print("="*80)

    try:
        clarity_eval = evaluate(
            clarity_results_ds,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings
        )
        print("\n✅ Clarity evaluation complete")
        print("\nClarity Agent RAGAS Scores:")
        print(clarity_eval)
    except Exception as e:
        print(f"\n❌ Clarity evaluation failed: {e}")
        clarity_eval = None

    # Evaluate Rigor Agent
    print("\n" + "="*80)
    print("EVALUATING RIGOR AGENT")
    print("="*80)

    try:
        rigor_eval = evaluate(
            rigor_results_ds,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings
        )
        print("\n✅ Rigor evaluation complete")
        print("\nRigor Agent RAGAS Scores:")
        print(rigor_eval)
    except Exception as e:
        print(f"\n❌ Rigor evaluation failed: {e}")
        rigor_eval = None

    # Step 5: Analyze and save results
    print("\n" + "="*80)
    print("Step 5: Analyzing and saving results")
    print("="*80)

    if clarity_eval:
        # Convert to DataFrame
        clarity_df = clarity_eval.to_pandas()

        # Overall scores
        print("\nCLARITY AGENT - OVERALL SCORES:")
        print("-" * 40)
        metric_cols = ['faithfulness', 'answer_relevancy', 'context_precision',
                       'context_recall', 'answer_correctness', 'answer_similarity']
        for col in metric_cols:
            if col in clarity_df.columns:
                print(f"{col:.<30} {clarity_df[col].mean():.3f}")

        # By issue type
        if 'issue_type' in clarity_df.columns:
            print("\nCLARITY AGENT - SCORES BY ISSUE TYPE:")
            print("-" * 40)
            issue_scores = clarity_df.groupby('issue_type')[['answer_correctness', 'answer_similarity']].mean()
            print(issue_scores)

        # Save results
        results_dir = os.path.join(backend_dir, "eval/results")
        os.makedirs(results_dir, exist_ok=True)
        clarity_csv_path = os.path.join(backend_dir, "eval/results/clarity_ragas_golden.csv")
        clarity_df.to_csv(clarity_csv_path, index=False)
        print(f"\n✅ Saved: {clarity_csv_path}")

    if rigor_eval:
        # Convert to DataFrame
        rigor_df = rigor_eval.to_pandas()

        # Overall scores
        print("\nRIGOR AGENT - OVERALL SCORES:")
        print("-" * 40)
        metric_cols = ['faithfulness', 'answer_relevancy', 'context_precision',
                       'context_recall', 'answer_correctness', 'answer_similarity']
        for col in metric_cols:
            if col in rigor_df.columns:
                print(f"{col:.<30} {rigor_df[col].mean():.3f}")

        # By issue type
        if 'issue_type' in rigor_df.columns:
            print("\nRIGOR AGENT - SCORES BY ISSUE TYPE:")
            print("-" * 40)
            issue_scores = rigor_df.groupby('issue_type')[['answer_correctness', 'answer_similarity']].mean()
            print(issue_scores)

        # Save results
        rigor_csv_path = os.path.join(backend_dir, "eval/results/rigor_ragas_golden.csv")
        rigor_df.to_csv(rigor_csv_path, index=False)
        print(f"\n✅ Saved: {rigor_csv_path}")

    # Summary
    print("\n" + "="*80)
    print("EVALUATION COMPLETE!")
    print("="*80)
    print("\nResults saved to:")
    print("  📄 backend/eval/results/clarity_ragas_golden.csv")
    print("  📄 backend/eval/results/rigor_ragas_golden.csv")

    if clarity_eval and rigor_eval:
        print("\nKey Findings:")
        clarity_df = clarity_eval.to_pandas()
        rigor_df = rigor_eval.to_pandas()

        print(f"  • Clarity Agent:")
        if 'answer_correctness' in clarity_df.columns:
            print(f"    - Answer Correctness: {clarity_df['answer_correctness'].mean():.3f}")
        if 'faithfulness' in clarity_df.columns:
            print(f"    - Faithfulness: {clarity_df['faithfulness'].mean():.3f}")

        print(f"  • Rigor Agent:")
        if 'answer_correctness' in rigor_df.columns:
            print(f"    - Answer Correctness: {rigor_df['answer_correctness'].mean():.3f}")
        if 'faithfulness' in rigor_df.columns:
            print(f"    - Faithfulness: {rigor_df['faithfulness'].mean():.3f}")


if __name__ == "__main__":
    asyncio.run(main())
