from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .dataset import BenchmarkCase


@dataclass
class CaseScore:
    case_id: str
    topic: str
    category: str
    difficulty: str
    success: bool
    heuristic_score: float
    llm_judge_score: float
    final_score: float
    metric_breakdown: Dict[str, float]
    citation_count: int
    plan_task_count: int
    report_chars: int
    latency_seconds: float
    llm_judge: Optional[Dict] = None
    error: str = ""


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return max(0.0, min(1.0, numerator / denominator))


def evaluate_single_case(
    case: BenchmarkCase,
    report: str,
    citations: List[dict],
    research_plan: List[dict],
    latency_seconds: float,
    llm_judge_score: float = 0.0,
    llm_judge_weight: float = 0.0,
    llm_judge_payload: Optional[Dict] = None,
    error: str = "",
) -> CaseScore:
    report_lower = (report or "").lower()
    success = bool(report) and not error

    keyword_hits = sum(1 for kw in case.expected_keywords if kw.lower() in report_lower)
    keyword_coverage = _safe_ratio(keyword_hits, len(case.expected_keywords))

    section_hits = sum(1 for sec in case.required_sections if sec.lower() in report_lower)
    section_coverage = _safe_ratio(section_hits, len(case.required_sections))

    citation_count = len(citations)
    plan_task_count = len(research_plan)
    report_chars = len(report)

    citation_score = _safe_ratio(citation_count, case.min_citations)
    plan_score = _safe_ratio(plan_task_count, case.min_plan_tasks)
    length_score = 1.0 if report_chars >= case.min_report_chars else _safe_ratio(report_chars, case.min_report_chars)

    heuristic_score = (
        0.35 * keyword_coverage
        + 0.25 * citation_score
        + 0.20 * section_coverage
        + 0.10 * plan_score
        + 0.10 * length_score
    )

    llm_judge_weight = max(0.0, min(0.5, llm_judge_weight))
    final_score = (1 - llm_judge_weight) * heuristic_score + llm_judge_weight * llm_judge_score

    if not success:
        heuristic_score = 0.0
        final_score = 0.0

    return CaseScore(
        case_id=case.case_id,
        topic=case.topic,
        category=case.category,
        difficulty=case.difficulty,
        success=success,
        heuristic_score=round(heuristic_score, 4),
        llm_judge_score=round(llm_judge_score, 4),
        final_score=round(final_score, 4),
        metric_breakdown={
            "keyword_coverage": round(keyword_coverage, 4),
            "citation_score": round(citation_score, 4),
            "section_coverage": round(section_coverage, 4),
            "plan_score": round(plan_score, 4),
            "length_score": round(length_score, 4),
        },
        citation_count=citation_count,
        plan_task_count=plan_task_count,
        report_chars=report_chars,
        latency_seconds=round(latency_seconds, 3),
        llm_judge=llm_judge_payload,
        error=error,
    )
