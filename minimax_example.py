"""
Minimax 模型使用示例
演示如何使用 minimax-m2.1 模型运行研究智能体
"""

import asyncio
from research_agent import (
    run_research_sync,
    create_research_agent,
    set_model_config
)


# ============================================
# 示例1: 使用环境变量配置 Minimax
# ============================================

def example_with_env():
    """
    通过环境变量配置 Minimax
    
    在 .env 文件中设置:
        LLM_MODEL=minimax-m2.1
        LLM_BASE_URL=https://api.minimax.chat/v1
        LLM_API_KEY=your-minimax-api-key
    
    然后直接运行:
        python minimax_example.py
    """
    print("=" * 80)
    print("示例1: 使用环境变量配置 Minimax")
    print("=" * 80)
    
    # 直接运行，配置会从环境变量读取
    result = run_research_sync("LangGraph 核心概念")
    
    print("\n📄 研究报告:")
    print(result["report"][:1000] + "...")
    print(f"\n📚 引用数量: {len(result['citations'])}")


# ============================================
# 示例2: 代码中直接配置 Minimax
# ============================================

def example_with_code():
    """
    在代码中直接配置 Minimax
    """
    print("\n" + "=" * 80)
    print("示例2: 代码中直接配置 Minimax")
    print("=" * 80)
    
    # 方式A: 使用 set_model_config 设置全局配置
    set_model_config(
        model="minimax-m2.1",
        base_url="https://api.minimax.chat/v1",
        api_key="your-minimax-api-key-here",  # 替换为您的密钥
        temperature=0.3
    )
    
    # 然后运行研究
    result = run_research_sync("AI Agent 的记忆机制")
    
    print("\n📄 研究报告:")
    print(result["report"][:1000] + "...")


# ============================================
# 示例3: 运行时传入配置
# ============================================

def example_runtime_config():
    """
    在运行时传入配置
    """
    print("\n" + "=" * 80)
    print("示例3: 运行时传入配置")
    print("=" * 80)
    
    # 直接在 run_research_sync 中传入配置
    result = run_research_sync(
        topic="多智能体系统的协调策略",
        model="minimax-m2.1",
        base_url="https://api.minimax.chat/v1",
        api_key="your-minimax-api-key-here"  # 替换为您的密钥
    )
    
    print("\n📄 研究报告:")
    print(result["report"][:1000] + "...")


# ============================================
# 示例4: 使用 create_research_agent 创建带配置的 agent
# ============================================

async def example_create_agent():
    """
    使用 create_research_agent 创建带配置的 agent
    """
    print("\n" + "=" * 80)
    print("示例4: 使用 create_research_agent 创建带配置的 agent")
    print("=" * 80)
    
    from langchain_core.messages import HumanMessage
    
    # 创建带 Minimax 配置的 agent
    agent = create_research_agent(
        model="minimax-m2.1",
        base_url="https://api.minimax.chat/v1",
        api_key="your-minimax-api-key-here"  # 替换为您的密钥
    )
    
    # 准备初始状态
    initial_state = {
        "messages": [HumanMessage(content="研究: 工具调用最佳实践")],
        "research_topic": "工具调用最佳实践",
        "research_plan": [],
        "current_task_index": 0,
        "all_citations": [],
        "final_report": "",
        "next_action": "plan"
    }
    
    # 运行研究
    result = await agent.ainvoke(initial_state)
    
    print("\n📄 研究报告:")
    print(result["final_report"][:1000] + "...")


# ============================================
# 示例5: 流式输出（实时查看进度）
# ============================================

async def example_streaming():
    """
    流式输出示例
    """
    print("\n" + "=" * 80)
    print("示例5: 流式输出（实时查看进度）")
    print("=" * 80)
    
    from langchain_core.messages import HumanMessage
    
    # 先设置配置
    set_model_config(
        model="minimax-m2.1",
        base_url="https://api.minimax.chat/v1",
        api_key="your-minimax-api-key-here"  # 替换为您的密钥
    )
    
    agent = create_research_agent()
    
    initial_state = {
        "messages": [HumanMessage(content="研究: LangGraph 状态管理")],
        "research_topic": "LangGraph 状态管理",
        "research_plan": [],
        "current_task_index": 0,
        "all_citations": [],
        "final_report": "",
        "next_action": "plan"
    }
    
    print("\n🚀 开始流式研究...\n")
    
    async for event in agent.astream(initial_state):
        for node_name, node_output in event.items():
            print(f"🔄 节点: {node_name}")
            
            if "messages" in node_output and node_output["messages"]:
                last_message = node_output["messages"][-1]
                print(f"   💬 {last_message.content}\n")


# ============================================
# 主函数
# ============================================

async def main():
    print("\n" + "🤖 " + "=" * 76 + " 🤖")
    print("    Minimax 模型使用示例")
    print("🤖 " + "=" * 76 + " 🤖\n")
    
    print("可用示例:")
    print("  1. 使用环境变量配置")
    print("  2. 代码中直接配置")
    print("  3. 运行时传入配置")
    print("  4. 使用 create_research_agent")
    print("  5. 流式输出")
    print("\n请先替换示例中的 'your-minimax-api-key-here' 为您的实际 API 密钥")
    print("\n输入示例编号运行（留空退出）: ", end="")
    
    choice = input().strip()
    
    if choice == "1":
        example_with_env()
    elif choice == "2":
        example_with_code()
    elif choice == "3":
        example_runtime_config()
    elif choice == "4":
        await example_create_agent()
    elif choice == "5":
        await example_streaming()
    else:
        print("\n退出。请记得替换 API 密钥后再次运行。")


if __name__ == "__main__":
    asyncio.run(main())
