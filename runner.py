from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List, Optional

from .dataset import BenchmarkCase, load_benchmark_dataset
from .human_review import select_human_review_cases, write_human_review_artifacts
from .judge import disabled_judge_result, run_llm_judge
from .scoring import CaseScore, evaluate_single_case


@dataclass
class BenchmarkRunConfig:
    dataset_path: str
    output_dir: str = "benchmark_results"
    limit: Optional[int] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    dry_run: bool = False
    llm_judge_mode: str = "off"
    llm_judge_max_cases: int = 3
    llm_judge_threshold: float = 0.65
    llm_judge_weight: float = 0.2
    llm_judge_model: Optional[str] = None
    llm_judge_base_url: Optional[str] = None
    llm_judge_api_key: Optional[str] = None
    llm_judge_temperature: float = 0.0
    llm_judge_report_char_limit: int = 2500
    enable_human_review: bool = True
    human_review_max_cases: int = 5
    human_review_threshold: float = 0.7


class BenchmarkRunner:
    def __init__(self, config: BenchmarkRunConfig):
        self.config = config

    def _should_apply_llm_judge(
        self,
        *,
        index: int,
        heuristic_score: float,
        judged_count: int,
    ) -> bool:
        mode = (self.config.llm_judge_mode or "off").lower()
        if mode == "off":
            return False
        if judged_count >= max(0, self.config.llm_judge_max_cases):
            return False
        if mode == "all":
            return True
        if mode == "sample":
            return index % 2 == 0
        if mode == "low_score":
            return heuristic_score < self.config.llm_judge_threshold
        return False

    def _build_dry_run_output(self, case: BenchmarkCase) -> Dict:
        report = (
            f"# {case.topic}\n\n"
            "## 引言\n"
            "这是 dry-run 生成的报告，用于验证 benchmark 流程。\n\n"
            "## 主体\n"
            + " ".join(case.expected_keywords)
            + "\n\n## 结论\n"
            "该案例用于管道联调，不代表真实研究质量。"
        )
        citations = [
            {
                "source_id": f"{case.case_id}-mock-{i}",
                "title": f"Mock Source {i}",
                "url": f"https://example.com/{case.case_id}/{i}",
                "snippet": "mock snippet",
                "accessed_date": datetime.now().strftime("%Y-%m-%d"),
                "reliability_score": 0.8,
            }
            for i in range(1, max(case.min_citations, 3) + 1)
        ]
        research_plan = [
            {
                "task_id": f"T{i}",
                "question": f"{case.topic} 子任务 {i}",
                "priority": 5 - i,
                "status": "completed",
                "findings": "mock findings",
                "citations": [],
            }
            for i in range(1, max(case.min_plan_tasks, 3) + 1)
        ]
        return {
            "report": report,
            "citations": citations,
            "research_plan": research_plan,
            "messages": ["dry-run mode"],
        }

    async def _run_case(self, case: BenchmarkCase) -> tuple[CaseScore, dict]:
        start = datetime.now()
        error = ""
        output: Dict = {
            "report": "",
            "citations": [],
            "research_plan": [],
            "messages": [],
        }

        try:
            if self.config.dry_run:
                output = self._build_dry_run_output(case)
            else:
                from research_agent import run_research

                output = await run_research(
                    topic=case.topic,
                    model=self.config.model,
                    base_url=self.config.base_url,
                    api_key=self.config.api_key,
                    temperature=self.config.temperature,
                )
        except Exception as exc:
            error = str(exc)

        elapsed = (datetime.now() - start).total_seconds()

        # First pass: heuristic score only (low-cost baseline).
        base_score = evaluate_single_case(
            case=case,
            report=output.get("report", ""),
            citations=output.get("citations", []),
            research_plan=output.get("research_plan", []),
            latency_seconds=elapsed,
            llm_judge_score=0.0,
            llm_judge_weight=0.0,
            llm_judge_payload=None,
            error=error,
        )

        return base_score, output

    async def _run_case_with_optional_judge(
        self,
        *,
        case: BenchmarkCase,
        index: int,
        judged_count: int,
    ) -> tuple[CaseScore, dict, bool]:
        base_score, output = await self._run_case(case)
        should_judge = self._should_apply_llm_judge(
            index=index,
            heuristic_score=base_score.heuristic_score,
            judged_count=judged_count,
        )

        judge_result = disabled_judge_result()
        if should_judge and base_score.success and not self.config.dry_run:
            judge_result = await run_llm_judge(
                topic=case.topic,
                report=output.get("report", ""),
                citations=output.get("citations", []),
                heuristic_score=base_score.heuristic_score,
                judge_model=self.config.llm_judge_model or self.config.model,
                judge_base_url=self.config.llm_judge_base_url or self.config.base_url,
                judge_api_key=self.config.llm_judge_api_key or self.config.api_key,
                judge_temperature=self.config.llm_judge_temperature,
                report_char_limit=self.config.llm_judge_report_char_limit,
            )

        score = evaluate_single_case(
            case=case,
            report=output.get("report", ""),
            citations=output.get("citations", []),
            research_plan=output.get("research_plan", []),
            latency_seconds=base_score.latency_seconds,
            llm_judge_score=judge_result.overall if judge_result.judged else 0.0,
            llm_judge_weight=self.config.llm_judge_weight if judge_result.judged else 0.0,
            llm_judge_payload=asdict(judge_result),
            error=base_score.error,
        )

        return score, output, judge_result.judged

    def _aggregate(self, case_scores: List[CaseScore]) -> Dict:
        total = len(case_scores)
        success = sum(1 for c in case_scores if c.success)
        avg_heuristic = mean(c.heuristic_score for c in case_scores) if case_scores else 0.0
        avg_final = mean(c.final_score for c in case_scores) if case_scores else 0.0
        avg_latency = mean(c.latency_seconds for c in case_scores) if case_scores else 0.0
        judge_invocations = sum(1 for c in case_scores if (c.llm_judge or {}).get("judged"))

        by_category: Dict[str, List[CaseScore]] = {}
        for score in case_scores:
            by_category.setdefault(score.category, []).append(score)

        category_summary = {}
        for category, items in by_category.items():
            category_summary[category] = {
                "cases": len(items),
                "success_rate": round(sum(1 for x in items if x.success) / len(items), 4),
                "avg_heuristic_score": round(mean(x.heuristic_score for x in items), 4),
                "avg_final_score": round(mean(x.final_score for x in items), 4),
                "avg_latency_seconds": round(mean(x.latency_seconds for x in items), 3),
            }

        return {
            "total_cases": total,
            "success_cases": success,
            "success_rate": round(success / total, 4) if total else 0.0,
            "avg_heuristic_score": round(avg_heuristic, 4),
            "avg_final_score": round(avg_final, 4),
            "avg_latency_seconds": round(avg_latency, 3),
            "llm_judge_invocations": judge_invocations,
            "category_summary": category_summary,
        }

    async def run(self) -> Dict:
        cases = load_benchmark_dataset(self.config.dataset_path)
        if self.config.limit is not None:
            cases = cases[: self.config.limit]

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = Path(self.config.output_dir) / timestamp
        run_dir.mkdir(parents=True, exist_ok=True)

        case_scores: List[CaseScore] = []
        raw_outputs: List[Dict] = []
        judged_count = 0

        for idx, case in enumerate(cases, start=1):
            print(f"[{idx}/{len(cases)}] Running case {case.case_id}: {case.topic}")
            score, output, judged = await self._run_case_with_optional_judge(
                case=case,
                index=idx,
                judged_count=judged_count,
            )
            if judged:
                judged_count += 1
            case_scores.append(score)
            raw_outputs.append(
                {
                    "case_id": case.case_id,
                    "topic": case.topic,
                    "output": output,
                    "error": score.error,
                }
            )

        summary = self._aggregate(case_scores)

        summary_path = run_dir / "summary.json"
        case_scores_path = run_dir / "case_scores.jsonl"
        raw_outputs_path = run_dir / "raw_outputs.jsonl"

        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)

        with case_scores_path.open("w", encoding="utf-8") as f:
            for score in case_scores:
                f.write(json.dumps(asdict(score), ensure_ascii=False) + "\n")

        with raw_outputs_path.open("w", encoding="utf-8") as f:
            for item in raw_outputs:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        human_review_artifacts = {}
        if self.config.enable_human_review:
            case_records = [
                {
                    "case_id": score.case_id,
                    "topic": score.topic,
                    "heuristic_score": score.heuristic_score,
                    "llm_judge_score": score.llm_judge_score,
                    "final_score": score.final_score,
                    "error": score.error,
                }
                for score in case_scores
            ]
            selected = select_human_review_cases(
                case_records,
                max_cases=self.config.human_review_max_cases,
                low_score_threshold=self.config.human_review_threshold,
            )
            human_review_artifacts = write_human_review_artifacts(
                run_dir=str(run_dir),
                selected_cases=selected,
            )

        return {
            "run_dir": str(run_dir),
            "summary": summary,
            "summary_path": str(summary_path),
            "case_scores_path": str(case_scores_path),
            "raw_outputs_path": str(raw_outputs_path),
            **human_review_artifacts,
        }


def run_benchmark_sync(config: BenchmarkRunConfig) -> Dict:
    return asyncio.run(BenchmarkRunner(config).run())
