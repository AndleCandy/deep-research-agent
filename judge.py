from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class LLMJudgeResult:
    enabled: bool
    judged: bool
    overall: float
    dimensions: Dict[str, float]
    rationale: str
    judge_model: str = ""
    error: str = ""


def _extract_json_object(raw: str) -> dict:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("empty response")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        return json.loads(raw[start : end + 1])
    raise ValueError("failed to parse json")


def _normalize_score(value: float, min_v: float = 1.0, max_v: float = 5.0) -> float:
    if max_v <= min_v:
        return 0.0
    value = max(min_v, min(max_v, value))
    return (value - min_v) / (max_v - min_v)


async def run_llm_judge(
    *,
    topic: str,
    report: str,
    citations: List[dict],
    heuristic_score: float,
    judge_model: Optional[str],
    judge_base_url: Optional[str],
    judge_api_key: Optional[str],
    judge_temperature: float,
    report_char_limit: int,
) -> LLMJudgeResult:
    truncated_report = (report or "")[:report_char_limit]
    citation_preview = citations[:8]

    prompt = (
        "你是研究报告评审员。请严格依据输入信息评分。\\n"
        "评分范围 1-5（可用一位小数）。\\n"
        "维度: factuality, completeness, citation_grounding, structure_clarity。\\n"
        "请仅输出 JSON，字段如下:\\n"
        "{\\n"
        '  "overall": 1-5,\\n'
        '  "dimensions": {"factuality":1-5,"completeness":1-5,"citation_grounding":1-5,"structure_clarity":1-5},\\n'
        '  "rationale": "不超过120字"\\n'
        "}\\n\\n"
        f"Topic: {topic}\\n"
        f"Heuristic score (0-1): {heuristic_score}\\n"
        f"Citations (up to 8): {json.dumps(citation_preview, ensure_ascii=False)}\\n"
        f"Report:\\n{truncated_report}"
    )

    try:
        from research_agent import create_llm
        from langchain_core.messages import HumanMessage

        llm = create_llm(
            model=judge_model,
            base_url=judge_base_url,
            api_key=judge_api_key,
            temperature=judge_temperature,
        )
        response = llm.invoke([HumanMessage(content=prompt)])
        data = _extract_json_object(str(response.content))

        raw_dims = data.get("dimensions", {})
        dims = {
            key: round(_normalize_score(float(raw_dims.get(key, data.get("overall", 3.0)))), 4)
            for key in ["factuality", "completeness", "citation_grounding", "structure_clarity"]
        }
        overall_norm = round(_normalize_score(float(data.get("overall", 3.0))), 4)

        return LLMJudgeResult(
            enabled=True,
            judged=True,
            overall=overall_norm,
            dimensions=dims,
            rationale=str(data.get("rationale", ""))[:200],
            judge_model=judge_model or "default",
        )
    except Exception as exc:
        return LLMJudgeResult(
            enabled=True,
            judged=False,
            overall=0.0,
            dimensions={},
            rationale="",
            judge_model=judge_model or "default",
            error=str(exc),
        )


def disabled_judge_result() -> LLMJudgeResult:
    return LLMJudgeResult(
        enabled=False,
        judged=False,
        overall=0.0,
        dimensions={},
        rationale="",
    )
