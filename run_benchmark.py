#!/usr/bin/env python3
"""Run benchmark evaluation for the research agent."""

import argparse
import json
import os

from benchmark.runner import BenchmarkRunConfig, run_benchmark_sync


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research Agent Benchmark Runner")
    parser.add_argument(
        "--dataset",
        default="benchmark_datasets/research_questions_zh_v1.jsonl",
        help="Path to benchmark dataset in JSONL format",
    )
    parser.add_argument(
        "--output-dir",
        default="benchmark_results",
        help="Directory to store benchmark outputs",
    )
    parser.add_argument("--limit", type=int, default=None, help="Evaluate only first N cases")
    parser.add_argument("--model", default=None, help="LLM model name")
    parser.add_argument("--base-url", default=None, help="LLM API base URL")
    parser.add_argument("--api-key", default=None, help="LLM API key")
    parser.add_argument("--temperature", type=float, default=None, help="LLM temperature")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use mock outputs to validate benchmark pipeline without calling model APIs",
    )
    parser.add_argument(
        "--llm-judge-mode",
        default="off",
        choices=["off", "sample", "low_score", "all"],
        help="LLM judge strategy. Default off for cost control",
    )
    parser.add_argument("--llm-judge-max-cases", type=int, default=3, help="Max cases to invoke LLM judge")
    parser.add_argument(
        "--llm-judge-threshold",
        type=float,
        default=0.65,
        help="Heuristic score threshold for low_score mode",
    )
    parser.add_argument(
        "--llm-judge-weight",
        type=float,
        default=0.2,
        help="Weight of llm judge score in final score (0-0.5 recommended)",
    )
    parser.add_argument("--llm-judge-model", default=None, help="Judge model name (can be cheaper model)")
    parser.add_argument("--llm-judge-base-url", default=None, help="Judge model base URL")
    parser.add_argument("--llm-judge-api-key", default=None, help="Judge model API key")
    parser.add_argument(
        "--llm-judge-report-char-limit",
        type=int,
        default=2500,
        help="Max report chars sent to judge model",
    )
    parser.add_argument(
        "--disable-human-review",
        action="store_true",
        help="Disable automatic human review queue generation",
    )
    parser.add_argument("--human-review-max-cases", type=int, default=5, help="Max manual review cases")
    parser.add_argument(
        "--human-review-threshold",
        type=float,
        default=0.7,
        help="Final score threshold for prioritized human review",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = BenchmarkRunConfig(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        limit=args.limit,
        model=args.model,
        base_url=args.base_url,
        api_key=args.api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY"),
        temperature=args.temperature,
        dry_run=args.dry_run,
        llm_judge_mode=args.llm_judge_mode,
        llm_judge_max_cases=args.llm_judge_max_cases,
        llm_judge_threshold=args.llm_judge_threshold,
        llm_judge_weight=args.llm_judge_weight,
        llm_judge_model=args.llm_judge_model,
        llm_judge_base_url=args.llm_judge_base_url,
        llm_judge_api_key=(
            args.llm_judge_api_key or args.api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        ),
        llm_judge_report_char_limit=args.llm_judge_report_char_limit,
        enable_human_review=not args.disable_human_review,
        human_review_max_cases=args.human_review_max_cases,
        human_review_threshold=args.human_review_threshold,
    )

    result = run_benchmark_sync(config)
    print("\nBenchmark finished")
    print(f"Run directory: {result['run_dir']}")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
