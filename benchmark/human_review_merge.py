from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Dict, List


def merge_human_review_scores(case_scores_path: str, reviewed_jsonl_path: str, output_path: str) -> Dict:
    case_scores: List[Dict] = []
    reviewed: Dict[str, Dict] = {}

    with Path(case_scores_path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                case_scores.append(json.loads(line))

    with Path(reviewed_jsonl_path).open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                reviewed[str(item["case_id"])] = item

    merged = []
    for cs in case_scores:
        rid = str(cs.get("case_id"))
        review = reviewed.get(rid, {})
        hr_score = float(review.get("human_score", 0.0))
        reviewed_flag = hr_score > 0

        final_blended = cs.get("final_score", 0.0)
        if reviewed_flag:
            final_blended = round(0.8 * float(cs.get("final_score", 0.0)) + 0.2 * hr_score, 4)

        merged.append(
            {
                **cs,
                "human_reviewed": reviewed_flag,
                "human_score": hr_score,
                "human_notes": review.get("notes", ""),
                "final_score_with_human": final_blended,
            }
        )

    avg_with_human = mean(x["final_score_with_human"] for x in merged) if merged else 0.0
    summary = {
        "total_cases": len(merged),
        "human_reviewed_cases": sum(1 for x in merged if x["human_reviewed"]),
        "avg_final_score_with_human": round(avg_with_human, 4),
    }

    payload = {"summary": summary, "cases": merged}
    Path(output_path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload
