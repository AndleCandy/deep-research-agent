"""
自主研究智能体 (Autonomous Research Agent)
使用 LangGraph 构建的能够自主规划、搜索、引用来源并生成完整报告的 AI 研究助手

核心功能：
1. 自动研究规划 - 将复杂问题分解为研究子任务
2. 智能网络搜索 - 使用多种搜索策略获取信息
3. 引用追踪 - 自动记录和管理信息来源
4. 报告生成 - 输出带完整引用的专业研究报告

支持模型：OpenAI GPT 系列、Minimax 系列等 OpenAI 兼容接口
"""

import operator
import os
from typing import Annotated, List, TypedDict, Literal, Optional
from datetime import datetime
import json

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ==================== 模型配置 ====================

class ModelConfig:
    """模型配置类 - 支持多种 OpenAI 兼容接口"""
    
    # 默认配置（从环境变量读取）
    DEFAULT_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
    DEFAULT_BASE_URL = os.getenv("LLM_BASE_URL", None)
    DEFAULT_API_KEY = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    DEFAULT_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    
    # Minimax 预设配置
    MINIMAX_MODEL = "minimax-m2.1"
    MINIMAX_BASE_URL = "https://api.minimax.chat/v1"
    
    @classmethod
    def create_llm(cls, model=None, base_url=None, api_key=None, temperature=None, **kwargs):
        """创建 LLM 实例，支持自定义配置"""
        model_name = model or cls.DEFAULT_MODEL
        base = base_url or cls.DEFAULT_BASE_URL
        key = api_key or cls.DEFAULT_API_KEY
        temp = temperature if temperature is not None else cls.DEFAULT_TEMPERATURE
        
        # 如果是 Minimax 模型且未指定 base_url，使用 Minimax 的 URL
        if "minimax" in model_name.lower() and not base:
            base = cls.MINIMAX_BASE_URL
            print(f"🔄 检测到 Minimax 模型，使用 base_url: {base}")
        
        config = {"model": model_name, "temperature": temp, "api_key": key, **kwargs}
        if base:
            config["base_url"] = base
        
        return ChatOpenAI(**config)


# 全局模型配置
_current_model_config = {
    "model": ModelConfig.DEFAULT_MODEL,
    "base_url": ModelConfig.DEFAULT_BASE_URL,
    "api_key": ModelConfig.DEFAULT_API_KEY,
    "temperature": 0.3
}


def set_model_config(model=None, base_url=None, api_key=None, temperature=None):
    """设置全局模型配置"""
    global _current_model_config
    if model is not None:
        _current_model_config["model"] = model
    if base_url is not None:
        _current_model_config["base_url"] = base_url
    if api_key is not None:
        _current_model_config["api_key"] = api_key
    if temperature is not None:
        _current_model_config["temperature"] = temperature
    print(f"✅ 模型配置已更新: {_current_model_config['model']}")


def get_model_config():
    """获取当前模型配置"""
    return _current_model_config.copy()


def create_llm(temperature=None, **kwargs):
    """创建 LLM 实例（使用当前配置）"""
    config = _current_model_config.copy()
    if temperature is not None:
        config["temperature"] = temperature
    config.update(kwargs)
    return ModelConfig.create_llm(**config)


# ==================== 数据模型定义 ====================

class Citation(BaseModel):
    """引用信息模型"""
    source_id: str = Field(description="来源唯一标识符")
    title: str = Field(description="来源标题")
    url: str = Field(description="来源URL")
    snippet: str = Field(description="引用的文本片段")
    accessed_date: str = Field(description="访问日期")
    reliability_score: float = Field(default=0.8, description="可靠性评分 0-1")


class ResearchTask(BaseModel):
    """研究子任务模型"""
    task_id: str = Field(description="任务ID")
    question: str = Field(description="具体研究问题")
    priority: int = Field(default=1, description="优先级 1-5")
    status: Literal["pending", "in_progress", "completed"] = Field(default="pending")
    findings: str = Field(default="", description="研究发现")
    citations: List[Citation] = Field(default_factory=list, description="相关引用")


class AgentState(TypedDict):
    """智能体状态 - LangGraph 的核心状态管理"""
    # 消息历史
    messages: Annotated[List, operator.add]
    
    # 研究主题
    research_topic: str
    
    # 研究计划
    research_plan: List[ResearchTask]
    
    # 当前任务索引
    current_task_index: int
    
    # 所有引用
    all_citations: Annotated[List[Citation], operator.add]
    
    # 最终报告
    final_report: str
    
    # 下一步行动
    next_action: Literal["plan", "search", "synthesize", "complete", "error"]


# ==================== 工具定义 ====================

@tool
def web_search_tool(query: str, num_results: int = 5) -> str:
    """
    执行网络搜索并返回结果
    
    Args:
        query: 搜索查询
        num_results: 返回结果数量
        
    Returns:
        搜索结果的 JSON 字符串
    """
    # 模拟搜索结果（实际应用中应接入真实搜索 API）
    mock_results = [
        {
            "title": f"关于 {query} 的研究 {i+1}",
            "url": f"https://example.com/article-{i+1}",
            "snippet": f"这是关于 {query} 的详细信息。该研究表明...",
            "source_type": "academic" if i % 2 == 0 else "news",
            "date": "2025-01-15"
        }
        for i in range(num_results)
    ]
    return json.dumps(mock_results, ensure_ascii=False, indent=2)


@tool
def extract_key_info_tool(text: str, focus: str) -> str:
    """
    从文本中提取关键信息
    
    Args:
        text: 源文本
        focus: 关注焦点
        
    Returns:
        提取的关键信息
    """
    # 实际应用中可使用 LLM 进行智能提取
    return f"从文本中提取的关于 '{focus}' 的关键信息：{text[:200]}..."


@tool
def verify_source_tool(url: str) -> dict:
    """
    验证信息源的可靠性
    
    Args:
        url: 信息源URL
        
    Returns:
        可靠性评估结果
    """
    # 模拟源验证（实际应接入域名信誉评估服务）
    return {
        "reliability_score": 0.85,
        "source_type": "academic",
        "is_verified": True,
        "notes": "来自知名学术机构"
    }


# ==================== 节点函数定义 ====================

def create_research_plan(state: AgentState) -> AgentState:
    """
    规划节点：分析研究主题，创建研究计划
    """
    topic = state["research_topic"]
    
    # 使用 LLM 创建研究计划
    llm = create_llm(temperature=0.3)
    
    planning_prompt = f"""
    作为研究规划专家，请为以下主题创建详细的研究计划：
    
    主题：{topic}
    
    请将研究分解为 3-5 个具体的子问题，每个子问题应该：
    1. 具体且可搜索
    2. 相互补充但不重复
    3. 涵盖主题的不同方面
    
    以 JSON 格式返回，格式如下：
    [
        {{"task_id": "T1", "question": "具体问题1", "priority": 5}},
        {{"task_id": "T2", "question": "具体问题2", "priority": 4}}
    ]
    """
    
    response = llm.invoke([HumanMessage(content=planning_prompt)])
    
    try:
        # 解析 LLM 返回的研究计划
        plan_data = json.loads(response.content)
        research_tasks = [
            ResearchTask(**task) for task in plan_data
        ]
    except:
        # 如果解析失败，创建默认计划
        research_tasks = [
            ResearchTask(
                task_id="T1",
                question=f"{topic} 的定义和背景",
                priority=5
            ),
            ResearchTask(
                task_id="T2",
                question=f"{topic} 的最新发展",
                priority=4
            ),
            ResearchTask(
                task_id="T3",
                question=f"{topic} 的实际应用",
                priority=3
            )
        ]
    
    return {
        **state,
        "research_plan": research_tasks,
        "current_task_index": 0,
        "next_action": "search",
        "messages": state["messages"] + [
            AIMessage(content=f"已创建研究计划，共 {len(research_tasks)} 个子任务")
        ]
    }


def search_and_collect(state: AgentState) -> AgentState:
    """
    搜索节点：执行搜索并收集信息
    """
    current_idx = state["current_task_index"]
    research_plan = state["research_plan"]
    
    if current_idx >= len(research_plan):
        return {
            **state,
            "next_action": "synthesize"
        }
    
    current_task = research_plan[current_idx]
    current_task.status = "in_progress"
    
    # 执行搜索
    llm = create_llm(temperature=0.5)
    search_results = web_search_tool.invoke({"query": current_task.question})
    
    # 分析搜索结果
    analysis_prompt = f"""
    研究问题：{current_task.question}
    
    搜索结果：
    {search_results}
    
    请：
    1. 总结关键发现（200-300字）
    2. 标注哪些结果最相关
    3. 提取可引用的要点
    
    以 JSON 格式返回：
    {{
        "findings": "总结文本",
        "relevant_sources": [0, 1, 2]  // 相关结果的索引
    }}
    """
    
    analysis_response = llm.invoke([HumanMessage(content=analysis_prompt)])
    
    try:
        analysis = json.loads(analysis_response.content)
        findings = analysis.get("findings", "")
        relevant_indices = analysis.get("relevant_sources", [0])
    except:
        findings = "基于搜索结果的初步发现..."
        relevant_indices = [0]
    
    # 创建引用
    search_data = json.loads(search_results)
    new_citations = []
    
    for idx in relevant_indices:
        if idx < len(search_data):
            result = search_data[idx]
            citation = Citation(
                source_id=f"{current_task.task_id}-{idx}",
                title=result["title"],
                url=result["url"],
                snippet=result["snippet"],
                accessed_date=datetime.now().strftime("%Y-%m-%d"),
                reliability_score=0.8
            )
            new_citations.append(citation)
    
    # 更新任务状态
    current_task.status = "completed"
    current_task.findings = findings
    current_task.citations = new_citations
    research_plan[current_idx] = current_task
    
    # 决定下一步
    next_idx = current_idx + 1
    next_action = "search" if next_idx < len(research_plan) else "synthesize"
    
    return {
        **state,
        "research_plan": research_plan,
        "current_task_index": next_idx,
        "all_citations": new_citations,
        "next_action": next_action,
        "messages": state["messages"] + [
            AIMessage(content=f"已完成任务 {current_task.task_id}: {current_task.question}")
        ]
    }


def synthesize_report(state: AgentState) -> AgentState:
    """
    综合节点：整合所有研究发现，生成最终报告
    """
    topic = state["research_topic"]
    research_plan = state["research_plan"]
    all_citations = state["all_citations"]
    
    llm = create_llm(temperature=0.4)
    
    # 准备综合材料
    findings_text = "\n\n".join([
        f"## {task.question}\n{task.findings}\n相关引用: [{', '.join([c.source_id for c in task.citations])}]"
        for task in research_plan
    ])
    
    citations_text = "\n".join([
        f"[{c.source_id}] {c.title}. {c.url} (访问于 {c.accessed_date})"
        for c in all_citations
    ])
    
    synthesis_prompt = f"""
    作为研究报告撰写专家，请基于以下研究发现撰写一份完整的研究报告：
    
    主题：{topic}
    
    研究发现：
    {findings_text}
    
    要求：
    1. 结构清晰（引言、主体、结论）
    2. 整合所有子任务的发现
    3. 在正文中适当位置标注引用（格式：[source_id]）
    4. 客观中立，有理有据
    5. 长度约 800-1200 字
    
    请直接返回报告正文，不要包含 JSON 或其他格式标记。
    """
    
    report_response = llm.invoke([HumanMessage(content=synthesis_prompt)])
    report_body = report_response.content
    
    # 组装完整报告
    final_report = f"""
# {topic} - 研究报告

生成时间：{datetime.now().strftime("%Y年%m月%d日 %H:%M")}

---

{report_body}

---

## 参考文献

{citations_text}

---

**报告元数据**
- 研究子任务数：{len(research_plan)}
- 引用来源数：{len(all_citations)}
- 生成方式：自主研究智能体 (LangGraph)
"""
    
    return {
        **state,
        "final_report": final_report,
        "next_action": "complete",
        "messages": state["messages"] + [
            AIMessage(content="研究报告已生成完毕")
        ]
    }


# ==================== 路由函数 ====================

def route_next_step(state: AgentState) -> Literal["plan", "search", "synthesize", "complete"]:
    """
    路由函数：根据当前状态决定下一步行动
    """
    return state["next_action"]


# ==================== 构建 LangGraph ====================

def create_research_agent(
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: Optional[float] = None
) -> StateGraph:
    """
    创建研究智能体的 LangGraph 工作流
    
    Args:
        model: 模型名称，如 'gpt-4o', 'minimax-m2.1'
        base_url: API 基础 URL，Minimax 需要设置为 'https://api.minimax.chat/v1'
        api_key: API 密钥
        temperature: 默认温度参数
    
    示例 - 使用 Minimax:
        agent = create_research_agent(
            model="minimax-m2.1",
            base_url="https://api.minimax.chat/v1",
            api_key="your-api-key"
        )
    """
    # 如果传入了参数，更新全局配置
    if any([model, base_url, api_key, temperature]):
        set_model_config(model=model, base_url=base_url, api_key=api_key, temperature=temperature)
    
    # 初始化状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("plan", create_research_plan)
    workflow.add_node("search", search_and_collect)
    workflow.add_node("synthesize", synthesize_report)
    
    # 添加边
    workflow.add_edge(START, "plan")
    
    # 添加条件边
    workflow.add_conditional_edges(
        "plan",
        route_next_step,
        {
            "search": "search",
            "synthesize": "synthesize",
            "complete": END
        }
    )
    
    workflow.add_conditional_edges(
        "search",
        route_next_step,
        {
            "search": "search",  # 循环处理多个任务
            "synthesize": "synthesize"
        }
    )
    
    workflow.add_conditional_edges(
        "synthesize",
        route_next_step,
        {
            "complete": END
        }
    )
    
    return workflow.compile()


# ==================== 主执行函数 ====================

async def run_research(
    topic: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: Optional[float] = None
) -> dict:
    """
    运行研究智能体
    
    Args:
        topic: 研究主题
        model: 模型名称，如 'gpt-4o', 'minimax-m2.1'
        base_url: API 基础 URL
        api_key: API 密钥
        temperature: 温度参数
        
    Returns:
        包含研究报告和元数据的字典
        
    示例 - 使用 Minimax:
        result = await run_research(
            "LangGraph 核心概念",
            model="minimax-m2.1",
            base_url="https://api.minimax.chat/v1",
            api_key="your-api-key"
        )
    """
    # 创建智能体（传入配置）
    agent = create_research_agent(
        model=model, base_url=base_url, api_key=api_key, temperature=temperature
    )
    
    # 初始状态
    initial_state = {
        "messages": [HumanMessage(content=f"请研究：{topic}")],
        "research_topic": topic,
        "research_plan": [],
        "current_task_index": 0,
        "all_citations": [],
        "final_report": "",
        "next_action": "plan"
    }
    
    # 执行工作流
    final_state = await agent.ainvoke(initial_state)
    
    return {
        "report": final_state["final_report"],
        "citations": [c.dict() for c in final_state["all_citations"]],
        "research_plan": [t.dict() for t in final_state["research_plan"]],
        "messages": [str(m.content) for m in final_state["messages"]]
    }


def run_research_sync(
    topic: str,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: Optional[float] = None
) -> dict:
    """
    同步版本的研究执行函数
    
    Args:
        topic: 研究主题
        model: 模型名称
        base_url: API 基础 URL
        api_key: API 密钥
        temperature: 温度参数
        
    示例 - 使用 Minimax:
        result = run_research_sync(
            "LangGraph 核心概念",
            model="minimax-m2.1",
            base_url="https://api.minimax.chat/v1",
            api_key="your-api-key"
        )
    """
    import asyncio
    return asyncio.run(run_research(
        topic=topic,
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature
    ))


# ==================== 命令行接口 ====================

if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法: python research_agent.py '研究主题'")
        print("示例: python research_agent.py 'LangGraph 在多智能体系统中的应用'")
        print("\n环境变量配置:")
        print("  LLM_MODEL=minimax-m2.1")
        print("  LLM_BASE_URL=https://api.minimax.chat/v1")
        print("  LLM_API_KEY=your-api-key")
        sys.exit(1)
    
    research_topic = sys.argv[1]
    
    print(f"🔍 启动自主研究智能体...")
    print(f"🤖 使用模型: {_current_model_config['model']}")
    print(f"📋 研究主题: {research_topic}\n")
    
    # 执行研究
    result = run_research_sync(research_topic)
    
    # 输出报告
    print("\n" + "="*80)
    print(result["report"])
    print("="*80)
    
    # 保存报告
    filename = f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(result["report"])
    
    print(f"\n✅ 报告已保存至: {filename}")
