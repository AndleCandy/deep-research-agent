from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def select_human_review_cases(
    case_records: List[Dict],
    *,
    max_cases: int,
    low_score_threshold: float,
) -> List[Dict]:
    if not case_records:
        return []

    low_score = [x for x in case_records if x.get("final_score", 0.0) < low_score_threshold]
    low_score = sorted(low_score, key=lambda x: x.get("final_score", 0.0))

    selected = low_score[:max_cases]
    if len(selected) < max_cases:
        remaining = [x for x in case_records if x not in selected]
        remaining = sorted(remaining, key=lambda x: x.get("final_score", 0.0))
        selected.extend(remaining[: max_cases - len(selected)])

    return selected


def write_human_review_artifacts(
    *,
    run_dir: str,
    selected_cases: List[Dict],
) -> Dict[str, str]:
    run_path = Path(run_dir)
    queue_path = run_path / "human_review_queue.jsonl"
    form_path = run_path / "human_review_form.md"

    with queue_path.open("w", encoding="utf-8") as f:
        for item in selected_cases:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    form_lines = [
        "# Human Review Form",
        "",
        "请对每个样本按 1-5 分打分，并记录关键问题。",
        "评分维度：factuality / completeness / citation_grounding / actionability。",
        "",
    ]

    for idx, item in enumerate(selected_cases, start=1):
        form_lines.extend(
            [
                f"## Case {idx}: {item.get('case_id')} - {item.get('topic')}",
                f"- final_score: {item.get('final_score')}",
                f"- heuristic_score: {item.get('heuristic_score')}",
                f"- llm_judge_score: {item.get('llm_judge_score')}",
                "- factuality (1-5): ",
                "- completeness (1-5): ",
                "- citation_grounding (1-5): ",
                "- actionability (1-5): ",
                "- major_issues: ",
                "- keep_or_reject: ",
                "",
            ]
        )

    form_path.write_text("\n".join(form_lines), encoding="utf-8")

    return {
        "human_review_queue_path": str(queue_path),
        "human_review_form_path": str(form_path),
    }
