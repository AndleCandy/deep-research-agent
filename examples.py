"""
研究智能体使用示例
演示各种使用场景和高级功能
"""

import asyncio
from research_agent import (
    create_research_agent,
    AgentState,
    ResearchTask,
    Citation
)
from langchain_core.messages import HumanMessage


# ==================== 示例1: 基础研究 ====================

async def example_basic_research():
    """基础研究示例"""
    print("\n" + "="*80)
    print("示例1: 基础研究 - LangGraph 核心概念")
    print("="*80 + "\n")
    
    agent = create_research_agent()
    
    initial_state = {
        "messages": [HumanMessage(content="研究 LangGraph 的核心概念")],
        "research_topic": "LangGraph 核心概念与架构",
        "research_plan": [],
        "current_task_index": 0,
        "all_citations": [],
        "final_report": "",
        "next_action": "plan"
    }
    
    result = await agent.ainvoke(initial_state)
    
    print("📊 研究计划:")
    for task in result["research_plan"]:
        print(f"  - [{task.status}] {task.question}")
    
    print(f"\n📚 引用数量: {len(result['all_citations'])}")
    print(f"\n📄 报告预览:")
    print(result["final_report"][:500] + "...\n")


# ==================== 示例2: 自定义研究计划 ====================

async def example_custom_plan():
    """自定义研究计划示例"""
    print("\n" + "="*80)
    print("示例2: 自定义研究计划")
    print("="*80 + "\n")
    
    agent = create_research_agent()
    
    # 手动创建研究计划
    custom_plan = [
        ResearchTask(
            task_id="T1",
            question="多智能体系统的定义和特点",
            priority=5
        ),
        ResearchTask(
            task_id="T2",
            question="LangGraph 在多智能体协作中的应用",
            priority=4
        ),
        ResearchTask(
            task_id="T3",
            question="实际案例：使用 LangGraph 构建多智能体系统",
            priority=3
        )
    ]
    
    initial_state = {
        "messages": [HumanMessage(content="自定义研究计划")],
        "research_topic": "LangGraph 多智能体系统实践",
        "research_plan": custom_plan,
        "current_task_index": 0,
        "all_citations": [],
        "final_report": "",
        "next_action": "search"  # 跳过规划，直接搜索
    }
    
    result = await agent.ainvoke(initial_state)
    print("✅ 使用自定义研究计划完成研究\n")


# ==================== 示例3: 流式输出 ====================

async def example_streaming():
    """流式输出示例 - 实时显示研究进度"""
    print("\n" + "="*80)
    print("示例3: 流式输出 - 实时研究进度")
    print("="*80 + "\n")
    
    agent = create_research_agent()
    
    initial_state = {
        "messages": [HumanMessage(content="研究 AI Agent 的记忆机制")],
        "research_topic": "AI Agent 的记忆机制",
        "research_plan": [],
        "current_task_index": 0,
        "all_citations": [],
        "final_report": "",
        "next_action": "plan"
    }
    
    # 使用 astream 进行流式处理
    async for event in agent.astream(initial_state):
        for node_name, node_output in event.items():
            print(f"🔄 节点: {node_name}")
            
            # 显示消息更新
            if "messages" in node_output and node_output["messages"]:
                last_message = node_output["messages"][-1]
                print(f"   💬 {last_message.content}\n")


# ==================== 示例4: 人机协作 ====================

async def example_human_in_loop():
    """人机协作示例 - 在关键步骤请求人工审核"""
    print("\n" + "="*80)
    print("示例4: 人机协作研究")
    print("="*80 + "\n")
    
    from langgraph.checkpoint.memory import MemorySaver
    
    # 使用检查点保存状态
    memory = MemorySaver()
    agent = create_research_agent()
    
    # 模拟中断点：在生成报告前请求审核
    print("ℹ️  实际应用中，可以在 synthesize 节点前添加 interrupt 实现人工审核\n")
    print("   示例代码:")
    print("   workflow.add_edge('search', 'human_review')")
    print("   workflow.add_edge('human_review', 'synthesize')\n")


# ==================== 示例5: 错误处理和重试 ====================

async def example_error_handling():
    """错误处理示例"""
    print("\n" + "="*80)
    print("示例5: 错误处理和重试机制")
    print("="*80 + "\n")
    
    # 在实际应用中，应在节点函数中添加 try-except
    print("💡 最佳实践:")
    print("  1. 为每个节点添加异常处理")
    print("  2. 记录失败任务到 state")
    print("  3. 实现自动重试逻辑")
    print("  4. 提供降级方案（如使用缓存结果）\n")
    
    error_handling_code = '''
def search_and_collect_with_retry(state: AgentState) -> AgentState:
    """带重试的搜索节点"""
    max_retries = 3
    current_task = state["research_plan"][state["current_task_index"]]
    
    for attempt in range(max_retries):
        try:
            # 执行搜索
            results = web_search_tool.invoke({"query": current_task.question})
            # ... 处理结果
            break
        except Exception as e:
            if attempt == max_retries - 1:
                # 最后一次失败，使用降级策略
                current_task.findings = "搜索失败，使用缓存数据"
                current_task.status = "failed"
            else:
                # 等待后重试
                await asyncio.sleep(2 ** attempt)
    
    return state
'''
    print(error_handling_code)


# ==================== 示例6: 批量研究 ====================

async def example_batch_research():
    """批量研究示例"""
    print("\n" + "="*80)
    print("示例6: 批量研究多个主题")
    print("="*80 + "\n")
    
    topics = [
        "LangGraph 的状态管理机制",
        "多智能体系统的协调策略",
        "AI Agent 的工具调用最佳实践"
    ]
    
    agent = create_research_agent()
    
    tasks = []
    for topic in topics:
        initial_state = {
            "messages": [HumanMessage(content=f"研究: {topic}")],
            "research_topic": topic,
            "research_plan": [],
            "current_task_index": 0,
            "all_citations": [],
            "final_report": "",
            "next_action": "plan"
        }
        tasks.append(agent.ainvoke(initial_state))
    
    print("🚀 并行执行 3 个研究任务...\n")
    results = await asyncio.gather(*tasks)
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {topics[i-1]}")
        print(f"   状态: ✅ 完成")
        print(f"   引用数: {len(result['all_citations'])}")
        print()


# ==================== 示例7: 可视化工作流 ====================

def example_visualize_graph():
    """可视化 LangGraph 工作流"""
    print("\n" + "="*80)
    print("示例7: 可视化研究工作流")
    print("="*80 + "\n")
    
    agent = create_research_agent()
    
    try:
        # 尝试生成 Mermaid 图
        print("📊 工作流结构（Mermaid 格式）:\n")
        print("""
graph TD
    START([开始]) --> plan[规划节点<br/>创建研究计划]
    plan --> search[搜索节点<br/>执行搜索和收集]
    search --> |更多任务| search
    search --> |完成所有任务| synthesize[综合节点<br/>生成报告]
    synthesize --> END([结束])
    
    style plan fill:#e1f5ff
    style search fill:#fff4e1
    style synthesize fill:#e7f5e1
        """)
        
        print("\n💡 在 LangGraph Studio 中可以可视化查看和调试工作流")
        
    except Exception as e:
        print(f"可视化失败: {e}")


# ==================== 主函数 ====================

async def main():
    """运行所有示例"""
    print("\n" + "🤖 " + "="*76 + " 🤖")
    print("    自主研究智能体 (Research Agent) - 完整示例集")
    print("🤖 " + "="*76 + " 🤖\n")
    
    examples = [
        ("基础研究", example_basic_research),
        ("自定义计划", example_custom_plan),
        ("流式输出", example_streaming),
        ("人机协作", example_human_in_loop),
        ("错误处理", example_error_handling),
        ("批量研究", example_batch_research),
        ("可视化工作流", lambda: example_visualize_graph())
    ]
    
    # 运行示例（可根据需要选择）
    print("可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\n输入示例编号运行（留空运行所有）: ", end="")
    choice = input().strip()
    
    if choice:
        idx = int(choice) - 1
        if 0 <= idx < len(examples):
            name, func = examples[idx]
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()
    else:
        # 运行所有示例
        for name, func in examples:
            if asyncio.iscoroutinefunction(func):
                await func()
            else:
                func()
            await asyncio.sleep(1)  # 示例间暂停


if __name__ == "__main__":
    asyncio.run(main())
