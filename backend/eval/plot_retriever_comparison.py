"""
Plot retriever comparison for RAG evaluation results.

This script creates separate comparison plots for each agent,
comparing different retriever configurations.

Usage:
    # Plot for all agents
    python eval/plot_retriever_comparison.py

    # Plot for specific agent only
    python eval/plot_retriever_comparison.py --agent clarity

    # Custom figure size
    python eval/plot_retriever_comparison.py --width 14 --height 7
"""

import argparse
import json
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns


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


def plot_agent_comparison(agent: str, agent_df: pd.DataFrame, figsize=(12, 6), output_dir: Path = None):
    """
    Create comparison plot for a specific agent.

    Args:
        agent: Agent name (e.g., "clarity", "rigor")
        agent_df: DataFrame with metrics for this agent
        figsize: Figure size (width, height)
        output_dir: Output directory for plots (default: eval/results/)
    """
    if agent_df.empty:
        print(f"⚠️  No data for {agent} agent")
        return None

    # Set style
    sns.set_style("whitegrid")

    # Prepare data for plotting
    # Skip faithfulness for now
    metric_cols = ["answer_relevancy", "context_precision", "context_recall"]
    available_metrics = [col for col in metric_cols if col in agent_df.columns]

    # Create figure
    plt.figure(figsize=figsize)

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

    plt.title(f"{agent.upper()} Agent: Retriever Configuration Comparison",
              fontsize=14, fontweight="bold")
    plt.xlabel("RAGAS Metric", fontsize=12)
    plt.ylabel("Score", fontsize=12)
    plt.ylim(0, 1.05)  # Slightly above 1 to accommodate labels
    plt.legend(title="Retriever Config", fontsize=9, loc='upper left', bbox_to_anchor=(1, 1))
    plt.xticks(rotation=15, ha="right")

    # Add value labels on bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.3f', padding=3, fontsize=8)

    # Add grid for better readability
    ax.yaxis.grid(True, alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()

    # Save plot
    if output_dir is None:
        output_dir = Path(__file__).parent / "results"

    output_file = output_dir / f"{agent}_retriever_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"✓ {agent.capitalize()} plot: {output_file}")

    plt.close()

    return output_file


def create_summary_table(agent: str, agent_df: pd.DataFrame, output_dir: Path = None):
    """
    Create a summary table showing metric improvements for an agent.

    Args:
        agent: Agent name
        agent_df: DataFrame with metrics for this agent
        output_dir: Output directory (default: eval/results/)
    """
    if len(agent_df) < 2:
        return  # Need at least 2 configs to compare

    # Sort by retriever_config to get consistent ordering
    agent_df = agent_df.sort_values('retriever_config').reset_index(drop=True)

    print(f"\n{'='*70}")
    print(f"{agent.upper()} Agent: Metric Comparison")
    print(f"{'='*70}")

    # Skip faithfulness for now
    metric_cols = ["answer_relevancy", "context_precision", "context_recall"]
    available_metrics = [col for col in metric_cols if col in agent_df.columns]

    # Display table
    display_df = agent_df[['retriever_config'] + available_metrics]
    pd.set_option('display.float_format', '{:.4f}'.format)
    print(display_df.to_string(index=False))

    # Calculate improvements (compare each config to first one as baseline)
    if len(agent_df) >= 2:
        baseline = agent_df.iloc[0]
        print(f"\n{'-'*70}")
        print(f"Improvements vs Baseline ({baseline['retriever_config']}):")
        print(f"{'-'*70}")

        for idx in range(1, len(agent_df)):
            config = agent_df.iloc[idx]
            print(f"\n{config['retriever_config']}:")

            for metric in available_metrics:
                baseline_val = baseline[metric]
                config_val = config[metric]

                if baseline_val > 0:
                    improvement = ((config_val - baseline_val) / baseline_val) * 100
                    symbol = "📈" if improvement > 0 else "📉" if improvement < 0 else "➡️"
                    print(f"  {symbol} {metric:20s}: {improvement:+6.1f}%  ({baseline_val:.4f} → {config_val:.4f})")
                else:
                    diff = config_val - baseline_val
                    symbol = "📈" if diff > 0 else "📉" if diff < 0 else "➡️"
                    print(f"  {symbol} {metric:20s}: {baseline_val:.4f} → {config_val:.4f}")

    print()


def main():
    """Main plotting workflow."""
    parser = argparse.ArgumentParser(
        description="Plot retriever comparison for RAG evaluation"
    )
    parser.add_argument(
        "--agent",
        type=str,
        choices=["clarity", "rigor", "all"],
        default="all",
        help="Which agent to plot (default: all)"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=12,
        help="Figure width in inches (default: 12)"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=6,
        help="Figure height in inches (default: 6)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for plots (default: eval/results/)"
    )

    args = parser.parse_args()

    print("="*70)
    print("RAG Retriever Comparison Plots")
    print("="*70)

    # Load all metrics
    metrics_df = load_all_metrics()

    if metrics_df.empty:
        print("\n❌ No evaluation results found!")
        print("\nPlease run evaluations first:")
        print("  python eval/evaluate_rag_performance.py --evaluator both")
        return

    print(f"\n✓ Loaded metrics from {len(metrics_df)} configurations\n")

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else Path(__file__).parent / "results"

    # Get agents to plot
    if args.agent == "all":
        agents = metrics_df['evaluator'].unique()
    else:
        agents = [args.agent]

    # Create plots for each agent
    print("Creating comparison plots...\n")
    figsize = (args.width, args.height)

    for agent in agents:
        # Filter data for this agent
        agent_df = metrics_df[metrics_df['evaluator'] == agent].copy()

        if agent_df.empty:
            print(f"⚠️  No data for {agent} agent")
            continue

        # Create plot
        plot_agent_comparison(agent, agent_df, figsize, output_dir)

        # Create summary table
        create_summary_table(agent, agent_df, output_dir)

    print(f"\n{'='*70}")
    print("✅ Plotting Complete!")
    print(f"{'='*70}")
    print(f"\nPlots saved to: {output_dir}/")
    print("\nGenerated files:")
    for agent in agents:
        plot_file = output_dir / f"{agent}_retriever_comparison.png"
        if plot_file.exists():
            print(f"  - {plot_file.name}")


if __name__ == "__main__":
    main()
