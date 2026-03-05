from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class BenchmarkCase:
    case_id: str
    topic: str
    category: str
    difficulty: str
    expected_keywords: List[str] = field(default_factory=list)
    required_sections: List[str] = field(default_factory=lambda: ["引言", "结论"])
    min_citations: int = 3
    min_plan_tasks: int = 3
    min_report_chars: int = 700


REQUIRED_KEYS = {"case_id", "topic", "category", "difficulty"}


def _parse_case(raw: dict) -> BenchmarkCase:
    missing = REQUIRED_KEYS - set(raw.keys())
    if missing:
        raise ValueError(f"缺少必要字段: {sorted(missing)}")

    return BenchmarkCase(
        case_id=str(raw["case_id"]),
        topic=str(raw["topic"]),
        category=str(raw["category"]),
        difficulty=str(raw["difficulty"]),
        expected_keywords=list(raw.get("expected_keywords", [])),
        required_sections=list(raw.get("required_sections", ["引言", "结论"])),
        min_citations=int(raw.get("min_citations", 3)),
        min_plan_tasks=int(raw.get("min_plan_tasks", 3)),
        min_report_chars=int(raw.get("min_report_chars", 700)),
    )


def load_benchmark_dataset(path: str | Path) -> List[BenchmarkCase]:
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"数据集不存在: {dataset_path}")

    cases: List[BenchmarkCase] = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            try:
                case = _parse_case(raw)
            except Exception as exc:
                raise ValueError(f"数据集第 {idx} 行非法: {exc}") from exc
            cases.append(case)

    if not cases:
        raise ValueError("数据集为空")

    return cases
