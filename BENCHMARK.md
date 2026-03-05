# Research Agent Benchmark 指南

本文档对应本仓库新增的评测体系，覆盖：
- Benchmark 框架
- 研究问题数据集
- 自动化 evaluation 代码

## 1. 目录结构

```text
benchmark/
  __init__.py
  dataset.py          # BenchmarkCase 定义 + JSONL 读取
  scoring.py          # 单题指标打分逻辑
  judge.py            # LLM-as-a-Judge 轻量评审
  human_review.py     # 人工评审队列与表单生成
  human_review_merge.py # 人工打分回填合并工具
  runner.py           # 执行评测、聚合统计、落盘结果
benchmark_datasets/
  research_questions_zh_v1.jsonl  # 中文研究问题数据集（v1）
run_benchmark.py      # CLI 入口
benchmark_results/    # 评测输出目录（运行后自动生成）
```

## 2. 数据集格式

每行是一个 JSON 对象（JSONL），字段如下：

- `case_id`: 唯一 ID
- `topic`: 研究主题
- `category`: 题目类别（用于分组统计）
- `difficulty`: 难度等级（easy/medium/hard）
- `expected_keywords`: 期望覆盖关键词列表
- `required_sections`: 报告要求章节名（默认 `引言`、`结论`）
- `min_citations`: 最小引用数
- `min_plan_tasks`: 最小研究子任务数
- `min_report_chars`: 最小报告字数（按字符数）

## 3. 评分指标（启发式 + LLM Judge 融合）

### 3.1 启发式分数 `heuristic_score`（范围 0~1）

- `keyword_coverage` (35%): 关键词覆盖率
- `citation_score` (25%): 引用数量满足程度
- `section_coverage` (20%): 必需章节覆盖率
- `plan_score` (10%): 研究计划任务数满足程度
- `length_score` (10%): 报告长度满足程度

### 3.2 LLM Judge 分数 `llm_judge_score`（范围 0~1）

- 默认关闭（`--llm-judge-mode off`），零额外成本。
- 可选模式：
  - `sample`: 抽样评审（默认隔一个样本评一次）
  - `low_score`: 只评审低分样本（按启发式阈值）
  - `all`: 全量评审（成本最高，不建议默认使用）

### 3.3 最终分数 `final_score`

融合公式：

`final_score = (1 - llm_judge_weight) * heuristic_score + llm_judge_weight * llm_judge_score`

默认 `llm_judge_weight=0.2`，并建议保持在 `<=0.3` 以保证稳定性和可解释性。  
任务失败（报错或空报告）时，最终分数记为 0。

## 4. 运行评测

### 基础命令

```bash
python run_benchmark.py
```

默认数据集：`benchmark_datasets/research_questions_zh_v1.jsonl`

### 常见参数

```bash
python run_benchmark.py \
  --dataset benchmark_datasets/research_questions_zh_v1.jsonl \
  --model minimax-m2.1 \
  --base-url https://api.minimax.chat/v1 \
  --api-key <YOUR_API_KEY> \
  --limit 5
```

也支持从环境变量读取 API Key：`LLM_API_KEY` 或 `OPENAI_API_KEY`。

### 无 API 联调（推荐先跑）

```bash
python run_benchmark.py --dry-run --limit 3
```

`--dry-run` 会生成可控的模拟输出，主要用于验证数据集读取、评分逻辑、结果落盘是否正确。

### 低成本 LLM Judge（推荐）

```bash
python run_benchmark.py \
  --llm-judge-mode low_score \
  --llm-judge-max-cases 3 \
  --llm-judge-threshold 0.65 \
  --llm-judge-weight 0.2 \
  --llm-judge-report-char-limit 2500
```

这个配置会把 LLM Judge 控制在小样本且短上下文，显著降低 token 消耗。

## 5. 输出结果

每次评测会在 `benchmark_results/<timestamp>/` 下生成：

- `summary.json`: 总体指标（成功率、平均分、分类统计）
- `case_scores.jsonl`: 每个 case 的打分明细
- `raw_outputs.jsonl`: 每个 case 的原始输出和报错信息
- `human_review_queue.jsonl`: 待人工复核样本队列
- `human_review_form.md`: 人工复核打分模板

`summary.json` 中会额外包含：
- `avg_heuristic_score`
- `avg_final_score`
- `llm_judge_invocations`

## 6. 人工评审回填（可选）

你可以把人工评审结果整理成 JSONL（每行至少包含 `case_id`、`human_score`、`notes`），然后用：

```python
from benchmark.human_review_merge import merge_human_review_scores

merge_human_review_scores(
    case_scores_path="benchmark_results/<ts>/case_scores.jsonl",
    reviewed_jsonl_path="benchmark_results/<ts>/human_reviewed.jsonl",
    output_path="benchmark_results/<ts>/merged_with_human.json"
)
```

## 7. 扩展建议

1. 增加更严格的事实性评估（人工标注或 LLM-as-a-judge）。
2. 增加多语言题集（英文、双语），并做跨语言一致性测试。
3. 为 `hard` 题引入更高的 `min_citations` 和更细分的结构要求。
4. 将 `benchmark_results` 接入可视化看板，追踪模型版本回归趋势。
