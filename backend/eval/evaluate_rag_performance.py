"""
RAG Performance Evaluation using RAGAS

This script evaluates the RAG performance of clarity and rigor agents using RAGAS metrics.
It's designed to be simple, flexible, and easy to run for different evaluators.

Usage:
    python eval/evaluate_rag_performance.py --evaluator clarity
    python eval/evaluate_rag_performance.py --evaluator rigor
    python eval/evaluate_rag_performance.py --evaluator both
"""

import argparse
import asyncio
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.agents.clarity.clarity_agent import ClarityAgent
from app.agents.rigor.rigor_agent import RigorAgent
from app.services.vector_store import VectorStoreService
from app.retrievers.registry import RetrieverRegistry
from app.retrievers.config_helper import RetrieverConfigHelper
from app.retrievers.builders import *  # Auto-register all builders  # noqa: F403, F401
from app.models.schemas import DocType

# Import custom retrieval metrics
sys.path.insert(0, str(Path(__file__).parent))
from custom_retrieval_metrics import evaluate_retrieval_batch


def load_golden_dataset(evaluator: str) -> pd.DataFrame:
    """Load golden dataset CSV for the specified evaluator."""
    csv_path = Path(__file__).parent / "data" / "golden" / f"golden_{evaluator}_10.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Golden dataset not found at {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} samples from {csv_path}")
    return df


async def run_agent_on_sample(agent, sample: Dict[str, Any], sample_num: int) -> Dict[str, Any]:
    """
    Run agent on a single sample and return outputs + contexts.

    Returns:
        dict with keys: answer (generated output), contexts (retrieved docs)
    """
    print(f"\n{'─'*60}")
    print(f"Sample {sample_num} Debug Info")
    print(f"{'─'*60}")

    # Prepare section dictionary for agent
    section = {
        "title": "Sample Section",  # Could parse from data if needed
        "content": sample["reference_question"],  # The section text
        "line_start": 1,
        "line_end": 10
    }

    print(f"📝 Section content (first 100 chars): {section['content'][:100]}...")
    print(f"🤖 Agent type: {type(agent).__name__}")
    print(f"🔍 Has retriever: {agent.retriever is not None}")

    # Run agent analysis
    suggestions = await agent.analyze(section)

    print(f"💡 Suggestions generated: {len(suggestions)}")
    if suggestions:
        print(f"   First suggestion: {suggestions[0].get('description', 'N/A')[:80]}...")

    # Extract generated answer (combine all suggestions)
    answer = "\n".join([
        f"{s['description']}\nSuggested fix: {s.get('suggested_fix', 'N/A')}"
        for s in suggestions
    ]) if suggestions else "No issues found"

    print(f"📄 Generated answer length: {len(answer)} chars")

    # Get contexts from retriever if available
    contexts = []
    if agent.retriever:
        try:
            query_text = sample["reference_question"][:500]
            print(f"🔎 Querying retriever with {len(query_text)} chars...")
            docs = await agent.retriever.ainvoke(query_text)
            contexts = [doc.page_content for doc in docs]
            print(f"📚 Retrieved {len(contexts)} contexts")
            if contexts:
                print(f"   First context (100 chars): {contexts[0][:100]}...")
            else:
                print(f"   ⚠️  WARNING: No contexts retrieved from vector DB!")
        except Exception as e:
            print(f"❌ ERROR retrieving contexts: {e}")
            contexts = []
    else:
        print(f"⚠️  WARNING: Agent has no retriever configured!")

    result = {
        "answer": answer,
        "contexts": contexts if contexts else ["No contexts retrieved"]
    }

    print(f"✅ Sample {sample_num} processing complete")
    print(f"{'─'*60}\n")

    return result


def create_retriever_for_agent(agent_name: str, doc_type: DocType, k_override: int = None):
    """
    Create retriever for a specific agent using the registry pattern.

    Args:
        agent_name: Name of the agent (e.g., "clarity", "rigor")
        doc_type: Document type to filter
        k_override: Optional override for top_k parameter (for testing)

    Returns:
        LangChain BaseRetriever instance
    """
    # Initialize vector store
    vector_store = VectorStoreService()

    # Get retriever type and config for this agent
    retriever_type = RetrieverConfigHelper.get_agent_retriever_type(agent_name)
    retriever_config = RetrieverConfigHelper.get_agent_retriever_config(agent_name)
    retriever_config["doc_type"] = doc_type

    # Override k if specified
    if k_override is not None:
        retriever_config["k"] = k_override
        print(f"⚙️  Overriding k={k_override} for {agent_name} agent")

    # Create retriever using registry
    retriever = RetrieverRegistry.create(
        retriever_type=retriever_type,
        vector_store=vector_store,
        config=retriever_config
    )

    print(f"Created {retriever_type} retriever for {agent_name} agent (k={retriever_config['k']}, doc_type={doc_type.value})")
    return retriever


async def evaluate_agent(evaluator: str) -> Dict[str, Any]:
    """
    Evaluate a specific agent (clarity or rigor) on its golden dataset.

    Args:
        evaluator: "clarity" or "rigor"

    Returns:
        Dictionary with evaluation results and metadata
    """
    print(f"\n{'='*60}")
    print(f"Evaluating {evaluator.upper()} Agent")
    print(f"{'='*60}\n")

    # Load golden dataset
    df = load_golden_dataset(evaluator)

    # Limit to num_samples if specified (for testing/debugging)
    num_samples = globals().get('_num_samples_override', None)
    if num_samples is not None and num_samples < len(df):
        print(f"⚠️  Limiting evaluation to first {num_samples} samples (out of {len(df)})")
        df = df.head(num_samples)

    # Get k override if specified
    k_override = globals().get('_retriever_k_override', None)

    # Initialize agent with retriever
    if evaluator == "clarity":
        doc_type = DocType.CLARITY
        retriever = create_retriever_for_agent("clarity", doc_type, k_override)
        agent = ClarityAgent(retriever=retriever)
    elif evaluator == "rigor":
        doc_type = DocType.RIGOR
        retriever = create_retriever_for_agent("rigor", doc_type, k_override)
        agent = RigorAgent(retriever=retriever)
    else:
        raise ValueError(f"Unknown evaluator: {evaluator}")

    # Process each sample
    results = []
    for idx, row in df.iterrows():
        sample_num = int(idx) + 1 if isinstance(idx, int) else len(results) + 1
        print(f"\n{'='*60}")
        print(f"Processing sample {sample_num}/{len(df)}")
        print(f"{'='*60}")

        sample = {
            "reference_question": row["reference_question"],
            "reference_context": row["reference_context"],
            "reference_answer": row["reference_answer"]
        }

        # Run agent
        output = await run_agent_on_sample(agent, sample, sample_num)

        # Build RAGAS-compatible record
        # RAGAS 0.3+ expects: user_input, response, retrieved_contexts, reference, reference_contexts
        record = {
            "user_input": sample["reference_question"],  # section text (the query)
            "response": output["answer"],  # generated output (the answer)
            "retrieved_contexts": output["contexts"],  # retrieved contexts from RAG
            "reference": sample["reference_answer"],  # ground truth answer
            "reference_contexts": [sample["reference_context"]]  # ground truth contexts (for precision/recall)
        }

        results.append(record)

    return {
        "evaluator": evaluator,
        "results": results,
        "timestamp": datetime.now().isoformat(),
        "num_samples": len(results)
    }


def prepare_ragas_dataset(results: List[Dict[str, Any]]) -> Any:
    """
    Prepare dataset in RAGAS format.

    RAGAS 0.3+ expects: user_input, response, retrieved_contexts, reference, reference_contexts
    """
    from datasets import Dataset

    print(f"\n{'='*60}")
    print(f"Preparing RAGAS Dataset")
    print(f"{'='*60}")

    # Convert to RAGAS 0.3+ format
    data = {
        "user_input": [r["user_input"] for r in results],
        "response": [r["response"] for r in results],
        "retrieved_contexts": [r["retrieved_contexts"] for r in results],
        "reference": [r["reference"] for r in results],
        "reference_contexts": [r["reference_contexts"] for r in results]
    }

    print(f"📊 Dataset statistics:")
    print(f"   Total samples: {len(results)}")
    print(f"   Avg response length: {sum(len(a) for a in data['response']) / len(data['response']):.0f} chars")
    print(f"   Avg retrieved_contexts per sample: {sum(len(c) for c in data['retrieved_contexts']) / len(data['retrieved_contexts']):.1f}")
    print(f"   Avg reference_contexts per sample: {sum(len(c) for c in data['reference_contexts']) / len(data['reference_contexts']):.1f}")

    # Check for empty contexts
    empty_contexts = sum(1 for c in data['retrieved_contexts'] if not c or c == ["No contexts retrieved"])
    if empty_contexts > 0:
        print(f"   ⚠️  WARNING: {empty_contexts}/{len(results)} samples have no retrieved contexts!")
        print(f"      This will cause RAGAS metrics to be 0 or undefined!")

    dataset = Dataset.from_dict(data)
    print(f"✅ RAGAS dataset created with {len(dataset)} samples")
    print(f"{'='*60}\n")

    return dataset


def compute_ragas_metrics(dataset: Any) -> Dict[str, float]:
    """
    Compute RAGAS metrics on the dataset.

    Metrics:
    - faithfulness: Whether answer is grounded in contexts
    - answer_relevancy: Whether answer addresses the question
    - context_precision: Precision of retrieved contexts
    - context_recall: Recall of retrieved contexts (needs ground_truth contexts)
    """
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall
    )

    print("\nComputing RAGAS metrics...")

    # Run evaluation
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        ]
    )

    # Convert result to dict
    # RAGAS returns an EvaluationResult object
    print(f"\nDEBUG: Result type: {type(result)}")

    # Method 1: Try to convert to pandas DataFrame and get mean scores
    try:
        df = result.to_pandas()
        print(f"DEBUG: Successfully converted to DataFrame")
        print(f"DEBUG: DataFrame shape: {df.shape}")
        print(f"DEBUG: DataFrame columns: {df.columns.tolist()}")

        metrics_dict = {}
        for metric_name in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            if metric_name in df.columns:
                # Get mean score for this metric across all samples
                score = df[metric_name].mean()
                metrics_dict[metric_name] = float(score)
                print(f"  ✓ {metric_name}: {score:.4f}")
            else:
                print(f"  ✗ {metric_name} not found in columns")
                metrics_dict[metric_name] = 0.0

        return metrics_dict

    except AttributeError as e:
        print(f"WARNING: to_pandas() not available: {e}")
    except Exception as e:
        print(f"ERROR: Failed to convert to DataFrame: {e}")

    # Method 2: Try accessing internal score dictionary
    try:
        if hasattr(result, '_scores_dict'):
            scores = result._scores_dict
            print(f"DEBUG: Found _scores_dict: {scores}")
            return {
                "faithfulness": float(scores.get("faithfulness", 0.0)),
                "answer_relevancy": float(scores.get("answer_relevancy", 0.0)),
                "context_precision": float(scores.get("context_precision", 0.0)),
                "context_recall": float(scores.get("context_recall", 0.0))
            }
    except Exception as e:
        print(f"WARNING: Could not access _scores_dict: {e}")

    # Method 3: Try accessing as dict-like object
    try:
        # Some RAGAS versions allow dict-like access to aggregated scores
        metrics_dict = {}
        for metric_name in ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]:
            try:
                score = result[metric_name]
                metrics_dict[metric_name] = float(score)
                print(f"  ✓ {metric_name}: {score:.4f}")
            except (KeyError, TypeError):
                print(f"  ✗ {metric_name} not accessible via []")
                metrics_dict[metric_name] = 0.0

        # If we got any non-zero values, return this
        if any(v != 0.0 for v in metrics_dict.values()):
            return metrics_dict
    except Exception as e:
        print(f"WARNING: Dict-like access failed: {e}")

    # Method 4: Debug - print everything and raise error
    print(f"\nERROR: Could not extract metrics from result")
    print(f"Result type: {type(result)}")
    print(f"Result dir: {[attr for attr in dir(result) if not attr.startswith('_')]}")
    if hasattr(result, '__dict__'):
        print(f"Result __dict__: {result.__dict__}")
    print(f"Result repr: {result}")

    raise RuntimeError(
        f"Failed to extract metrics from RAGAS result. "
        f"Result type: {type(result)}. "
        f"This might be a RAGAS version compatibility issue."
    )


def get_retriever_config_name(evaluator: str) -> str:
    """
    Get a unique name for the current retriever configuration.

    Returns:
        String like "clarity_naive_k6" or "rigor_cohere_rerank_k6_initial20"
    """
    retriever_type = RetrieverConfigHelper.get_agent_retriever_type(evaluator)
    retriever_config = RetrieverConfigHelper.get_agent_retriever_config(evaluator)

    # Get k (with potential override)
    k_override = globals().get('_retriever_k_override', None)
    k = k_override if k_override is not None else retriever_config.get('k', 6)

    # Build config name with agent prefix
    if retriever_type == "cohere_rerank":
        initial_k = retriever_config.get('initial_k', 20)
        config_name = f"{evaluator}_{retriever_type}_k{k}_initial{initial_k}"
    else:
        config_name = f"{evaluator}_{retriever_type}_k{k}"

    return config_name


def save_results(evaluator: str, eval_data: Dict[str, Any], metrics: Dict[str, float],
                retriever_config_name: str = None):
    """
    Save evaluation results to disk in retriever-specific subdirectory.

    Args:
        evaluator: "clarity" or "rigor"
        eval_data: Evaluation data dictionary
        metrics: Metrics dictionary
        retriever_config_name: Optional name for retriever config (auto-detected if None)
    """
    # Get retriever config name
    if retriever_config_name is None:
        retriever_config_name = get_retriever_config_name(evaluator)

    # Create results directory for this retriever config
    results_base_dir = Path(__file__).parent / "results"
    results_dir = results_base_dir / retriever_config_name
    results_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Saving to: results/{retriever_config_name}/")

    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = results_dir / f"{evaluator}_results_{timestamp}.json"

    output = {
        "evaluator": evaluator,
        "retriever_config": retriever_config_name,
        "timestamp": eval_data["timestamp"],
        "num_samples": eval_data["num_samples"],
        "metrics": metrics,
        "detailed_results": eval_data["results"]
    }

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"  ✓ Detailed results: {results_file.name}")

    # Also save metrics summary
    metrics_file = results_dir / f"{evaluator}_metrics.json"

    # Include retriever config in metrics
    metrics_with_config = {
        "retriever_config": retriever_config_name,
        **metrics
    }

    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(metrics_with_config, f, indent=2)

    print(f"  ✓ Metrics summary: {metrics_file.name}")

    return results_file, metrics_file


def load_all_metrics() -> pd.DataFrame:
    """Load all saved metrics from all retriever config subdirectories."""
    results_base_dir = Path(__file__).parent / "results"

    if not results_base_dir.exists():
        return pd.DataFrame()

    all_metrics = []

    # Search in subdirectories for metrics files
    for metrics_file in results_base_dir.glob("**/*_metrics.json"):
        # Skip if in base directory (old format)
        if metrics_file.parent == results_base_dir:
            continue

        evaluator = metrics_file.stem.replace("_metrics", "")
        retriever_config = metrics_file.parent.name

        with open(metrics_file, encoding="utf-8") as f:
            metrics = json.load(f)

            # Add metadata if not present
            if "evaluator" not in metrics:
                metrics["evaluator"] = evaluator
            if "retriever_config" not in metrics:
                metrics["retriever_config"] = retriever_config

            all_metrics.append(metrics)

    if not all_metrics:
        return pd.DataFrame()

    return pd.DataFrame(all_metrics)


def create_comparison_table(metrics_df: pd.DataFrame):
    """Create and display comparison table."""
    if metrics_df.empty:
        print("\nNo metrics available for comparison.")
        return

    print("\n" + "="*80)
    print("RAG PERFORMANCE COMPARISON TABLE")
    print("="*80 + "\n")

    # Reorder columns for better display
    metric_cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]

    # Include retriever_config in display
    display_cols = ["evaluator", "retriever_config"] + [col for col in metric_cols if col in metrics_df.columns]
    display_df = metrics_df[display_cols]

    # Format for display
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.float_format', '{:.4f}'.format)

    print(display_df.to_string(index=False))
    print("\n" + "="*80 + "\n")

    # Save to CSV
    output_file = Path(__file__).parent / "results" / "comparison_table.csv"
    display_df.to_csv(output_file, index=False)
    print(f"Comparison table saved to: {output_file}\n")


def create_comparison_plots(metrics_df: pd.DataFrame):
    """Create separate comparison plots for each agent."""
    if metrics_df.empty:
        print("No metrics available for plotting.")
        return

    import matplotlib.pyplot as plt
    import seaborn as sns

    # Set style
    sns.set_style("whitegrid")

    # Prepare data for plotting
    metric_cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    available_metrics = [col for col in metric_cols if col in metrics_df.columns]

    # Get unique agents
    agents = metrics_df['evaluator'].unique()

    # Create separate plot for each agent
    for agent in agents:
        # Filter data for this agent
        agent_df = metrics_df[metrics_df['evaluator'] == agent].copy()

        if agent_df.empty:
            continue

        # Create figure
        plt.figure(figsize=(12, 6))

        # Reshape data for grouped bar plot
        plot_data = agent_df.melt(
            id_vars=["retriever_config"],
            value_vars=available_metrics,
            var_name="metric",
            value_name="score"
        )

        # Create grouped bar plot
        ax = sns.barplot(
            data=plot_data,
            x="metric",
            y="score",
            hue="retriever_config",
            palette="Set2"
        )

        plt.title(f"{agent.upper()} Agent: Retriever Comparison", fontsize=14, fontweight="bold")
        plt.xlabel("RAGAS Metric", fontsize=12)
        plt.ylabel("Score", fontsize=12)
        plt.ylim(0, 1)
        plt.legend(title="Retriever Config", fontsize=10, loc='best')
        plt.xticks(rotation=15, ha="right")

        # Add value labels on bars
        for container in ax.containers:
            ax.bar_label(container, fmt='%.3f', padding=3)

        plt.tight_layout()

        # Save plot for this agent
        output_file = Path(__file__).parent / "results" / f"{agent}_retriever_comparison.png"
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"  ✓ {agent.capitalize()} comparison plot: {output_file.name}")

        plt.close()

    print()


async def main():
    """Main evaluation workflow."""
    parser = argparse.ArgumentParser(description="Evaluate RAG performance using RAGAS")
    parser.add_argument(
        "--evaluator",
        type=str,
        choices=["clarity", "rigor", "all"],
        default="all",
        help="Which agent to evaluate"
    )
    parser.add_argument(
        "--skip-eval",
        action="store_true",
        help="Skip evaluation and only generate plots from existing results"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=None,
        help="Number of samples to evaluate (default: all samples in dataset)"
    )
    parser.add_argument(
        "--retriever-k",
        type=int,
        default=None,
        help="Override retriever top_k parameter (default: from config)"
    )

    args = parser.parse_args()

    # Set global overrides if specified
    if args.num_samples:
        globals()['_num_samples_override'] = args.num_samples
        print(f"\n⚠️  Running on {args.num_samples} samples only (for testing)")

    if args.retriever_k:
        globals()['_retriever_k_override'] = args.retriever_k
        print(f"\n⚙️  Overriding retriever k={args.retriever_k}")

    if not args.skip_eval:
        # Run evaluation(s)
        evaluators = ["clarity", "rigor"] if args.evaluator == "all" else [args.evaluator]

        for evaluator in evaluators:
            # Run agent evaluation
            eval_data = await evaluate_agent(evaluator)

            # Prepare RAGAS dataset
            dataset = prepare_ragas_dataset(eval_data["results"])

            # Compute RAGAS metrics
            ragas_metrics = compute_ragas_metrics(dataset)

            # Compute custom retrieval metrics
            print("\nComputing custom retrieval metrics...")
            retrieved_contexts_list = [r["retrieved_contexts"] for r in eval_data["results"]]
            reference_contexts_list = [r["reference_contexts"] for r in eval_data["results"]]

            custom_metrics = evaluate_retrieval_batch(
                retrieved_contexts_list,
                reference_contexts_list,
                threshold=0.5  # 50% word overlap for a match
            )

            # Filter and combine metrics - only keep meaningful ones
            metrics = {
                "faithfulness": ragas_metrics.get("faithfulness", 0.0),
                "answer_relevancy": ragas_metrics.get("answer_relevancy", 0.0),
                "context_precision": custom_metrics["custom_context_precision"],
                "context_recall": custom_metrics["custom_context_recall"],
                "context_f1": custom_metrics["custom_context_f1"]
            }

            print(f"\n{evaluator.upper()} Metrics:")
            print("  faithfulness: {:.4f}".format(metrics["faithfulness"]))
            print("  answer_relevancy: {:.4f}".format(metrics["answer_relevancy"]))
            print("  context_precision: {:.4f}".format(metrics["context_precision"]))
            print("  context_recall: {:.4f}".format(metrics["context_recall"]))
            print("  context_f1: {:.4f}".format(metrics["context_f1"]))

            # Save results
            save_results(evaluator, eval_data, metrics)

    print("\n" + "="*60)
    print("Evaluation Complete!")
    print("="*60)
    print("\nResults saved to eval/results/")
    print("\nTo generate comparison tables and plots later, run:")
    print("  python eval/plot_retriever_comparison.py")


if __name__ == "__main__":
    asyncio.run(main())
