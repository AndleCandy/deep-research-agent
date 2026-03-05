"""
研究智能体 Web UI
使用 Streamlit 构建的交互式界面
支持 OpenAI、Minimax 等多种模型
"""

import streamlit as st
import asyncio
from datetime import datetime
import json
from research_agent import (
    create_research_agent,
    set_model_config,
    get_model_config,
)
from langchain_core.messages import HumanMessage


# ==================== 页面配置 ====================

st.set_page_config(
    page_title="自主研究智能体",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        padding: 1rem 0;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-planning {
        background-color: #E3F2FD;
        border-left: 4px solid #1E88E5;
    }
    .status-searching {
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
    }
    .status-synthesizing {
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
    }
    .citation-card {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ==================== 会话状态初始化 ====================

if "research_history" not in st.session_state:
    st.session_state.research_history = []

if "current_research" not in st.session_state:
    st.session_state.current_research = None

if "is_researching" not in st.session_state:
    st.session_state.is_researching = False


# ==================== 侧边栏 ====================

with st.sidebar:
    st.image("https://via.placeholder.com/300x100/1E88E5/FFFFFF?text=Research+Agent", 
             use_container_width=True)
    
    st.markdown("## ⚙️ 配置")
    
    # 研究深度
    research_depth = st.slider(
        "研究深度",
        min_value=1,
        max_value=5,
        value=3,
        help="控制子任务数量和搜索详细程度"
    )
    
    # 搜索结果数
    max_results = st.slider(
        "每个任务的搜索结果数",
        min_value=3,
        max_value=10,
        value=5
    )
    
    # 模型选择
    model_choice = st.selectbox(
        "LLM 模型",
        ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "minimax-m2.1", "自定义"],
        index=0,
        help="选择要使用的语言模型"
    )
    
    # 自定义模型配置（当选择 minimax 或自定义时显示）
    if model_choice == "minimax-m2.1":
        st.info("🔄 将使用 Minimax API: https://api.minimax.chat/v1")
        custom_base_url = "https://api.minimax.chat/v1"
        custom_api_key = st.text_input(
            "Minimax API Key",
            value="",
            type="password",
            help="您的 Minimax API 密钥"
        )
    elif model_choice == "自定义":
        custom_model = st.text_input("模型名称", value="")
        custom_base_url = st.text_input("API Base URL", value="", placeholder="https://api.example.com/v1")
        custom_api_key = st.text_input("API Key", value="", type="password")
    else:
        custom_base_url = None
        custom_api_key = None
    
    st.markdown("---")
    
    # 历史记录
    st.markdown("## 📚 研究历史")
    
    if st.session_state.research_history:
        for i, record in enumerate(reversed(st.session_state.research_history[-5:])):
            with st.expander(f"📄 {record['topic'][:30]}...", expanded=False):
                st.caption(f"🕒 {record['timestamp']}")
                st.caption(f"📊 引用数: {record['citation_count']}")
                if st.button("查看报告", key=f"view_{i}"):
                    st.session_state.selected_report = record
    else:
        st.info("暂无历史记录")
    
    st.markdown("---")
    
    # 关于
    with st.expander("ℹ️ 关于"):
        st.markdown("""
        **自主研究智能体 v1.0**
        
        基于 LangGraph 构建的智能研究助手
        
        核心功能:
        - 🎯 自动研究规划
        - 🔍 智能网络搜索
        - 📚 引用追踪管理
        - 📝 报告自动生成
        
        支持模型:
        - OpenAI GPT-4o/4-turbo/3.5-turbo
        - Minimax-m2.1
        - 其他 OpenAI 兼容接口
        
        [GitHub](https://github.com/AndleCandy/deep-research-agent)
        """)


# ==================== 主界面 ====================

st.markdown('<div class="main-header">🤖 自主研究智能体</div>', 
            unsafe_allow_html=True)

st.markdown("""
<div style='text-align: center; color: #666; margin-bottom: 2rem;'>
能自己规划、搜索、引用来源、最终输出带引用的完整报告
</div>
""", unsafe_allow_html=True)

# 创建标签页
tab1, tab2, tab3 = st.tabs(["🔍 新研究", "📊 研究进度", "📄 研究报告"])

# ==================== 标签页1: 新研究 ====================

with tab1:
    st.markdown("### 开始新的研究")
    
    # 输入区域
    col1, col2 = st.columns([3, 1])
    
    with col1:
        research_topic = st.text_input(
            "研究主题",
            placeholder="例如: LangGraph 在多智能体系统中的应用",
            help="输入您想要研究的主题"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        start_button = st.button(
            "🚀 开始研究",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.is_researching
        )
    
    # 快速主题建议
    st.markdown("**💡 快速主题:**")
    quick_topics = [
        "LangGraph 核心概念与架构",
        "AI Agent 的记忆机制",
        "多智能体系统的协调策略",
        "工具调用最佳实践"
    ]
    
    cols = st.columns(4)
    for i, topic in enumerate(quick_topics):
        with cols[i]:
            if st.button(topic, key=f"quick_{i}", use_container_width=True):
                research_topic = topic
                start_button = True
    
    # 执行研究
    if start_button and research_topic:
        st.session_state.is_researching = True
        st.session_state.current_research = {
            "topic": research_topic,
            "start_time": datetime.now(),
            "status": "starting",
            "progress": 0
        }
        st.rerun()


# ==================== 标签页2: 研究进度 ====================

with tab2:
    st.markdown("### 实时研究进度")
    
    if st.session_state.is_researching and st.session_state.current_research:
        current = st.session_state.current_research
        
        # 进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 显示当前使用的模型
        config = get_model_config()
        st.caption(f"🤖 当前模型: {config['model']}")
        
        # 状态容器
        status_container = st.container()
        
        # 执行研究（异步）
        async def execute_research():
            # 根据用户选择配置模型
            if model_choice == "minimax-m2.1":
                set_model_config(
                    model="minimax-m2.1",
                    base_url="https://api.minimax.chat/v1",
                    api_key=custom_api_key if custom_api_key else None
                )
            elif model_choice == "自定义":
                set_model_config(
                    model=custom_model,
                    base_url=custom_base_url,
                    api_key=custom_api_key if custom_api_key else None
                )
            else:
                set_model_config(model=model_choice)
            
            agent = create_research_agent()
            
            initial_state = {
                "messages": [HumanMessage(content=f"研究: {current['topic']}")],
                "research_topic": current['topic'],
                "research_plan": [],
                "current_task_index": 0,
                "all_citations": [],
                "final_report": "",
                "next_action": "plan"
            }
            
            # 流式处理
            progress = 0
            async for event in agent.astream(initial_state):
                for node_name, output in event.items():
                    # 更新进度
                    if node_name == "plan":
                        progress = 20
                        status_text.markdown("**状态:** 📋 正在规划研究...")
                        
                        if "research_plan" in output:
                            with status_container:
                                st.markdown('<div class="status-box status-planning">', 
                                          unsafe_allow_html=True)
                                st.markdown("#### 📋 研究计划已生成")
                                for task in output["research_plan"]:
                                    st.markdown(f"- **{task.task_id}**: {task.question}")
                                st.markdown('</div>', unsafe_allow_html=True)
                    
                    elif node_name == "search":
                        progress = min(progress + 15, 80)
                        status_text.markdown("**状态:** 🔍 正在搜索和收集信息...")
                        
                        if "messages" in output and output["messages"]:
                            with status_container:
                                st.markdown('<div class="status-box status-searching">', 
                                          unsafe_allow_html=True)
                                st.markdown(f"#### 🔍 {output['messages'][-1].content}")
                                st.markdown('</div>', unsafe_allow_html=True)
                    
                    elif node_name == "synthesize":
                        progress = 90
                        status_text.markdown("**状态:** 📝 正在生成报告...")
                        
                        with status_container:
                            st.markdown('<div class="status-box status-synthesizing">', 
                                      unsafe_allow_html=True)
                            st.markdown("#### 📝 正在综合研究发现...")
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    progress_bar.progress(progress / 100)
            
            # 完成
            progress_bar.progress(1.0)
            status_text.markdown("**状态:** ✅ 研究完成！")
            
            # 获取最终结果
            final_state = output
            return final_state
        
        # 运行异步任务
        try:
            final_result = asyncio.run(execute_research())
            
            # 保存到历史
            st.session_state.research_history.append({
                "topic": current['topic'],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "report": final_result["final_report"],
                "citations": final_result["all_citations"],
                "citation_count": len(final_result["all_citations"])
            })
            
            st.session_state.is_researching = False
            st.session_state.current_research = final_result
            
            st.success("✅ 研究完成！请查看 '研究报告' 标签页")
            
        except Exception as e:
            st.error(f"❌ 研究过程中出错: {str(e)}")
            st.session_state.is_researching = False
    
    else:
        st.info("👈 请从 '新研究' 标签页开始研究任务")


# ==================== 标签页3: 研究报告 ====================

with tab3:
    st.markdown("### 研究报告查看")
    
    # 选择报告
    if st.session_state.research_history:
        selected_index = st.selectbox(
            "选择报告",
            range(len(st.session_state.research_history)),
            format_func=lambda i: f"{st.session_state.research_history[i]['topic']} - {st.session_state.research_history[i]['timestamp']}"
        )
        
        report_data = st.session_state.research_history[selected_index]
        
        # 报告元数据
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("引用数量", report_data['citation_count'])
        with col2:
            st.metric("生成时间", report_data['timestamp'])
        with col3:
            st.metric("报告长度", f"{len(report_data['report'])} 字符")
        
        st.markdown("---")
        
        # 报告内容
        st.markdown("#### 📄 完整报告")
        st.markdown(report_data['report'])
        
        # 下载按钮
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 下载 Markdown",
                report_data['report'],
                file_name=f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown"
            )
        
        with col2:
            # 转换为 JSON
            json_data = json.dumps({
                "topic": report_data['topic'],
                "timestamp": report_data['timestamp'],
                "report": report_data['report'],
                "citations": [c.dict() if hasattr(c, 'dict') else c for c in report_data['citations']]
            }, ensure_ascii=False, indent=2)
            
            st.download_button(
                "📥 下载 JSON",
                json_data,
                file_name=f"research_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        # 引用详情
        with st.expander("📚 查看所有引用", expanded=False):
            for citation in report_data['citations']:
                if isinstance(citation, dict):
                    st.markdown(f"""
                    <div class="citation-card">
                        <strong>[{citation['source_id']}]</strong> {citation['title']}<br>
                        <a href="{citation['url']}" target="_blank">{citation['url']}</a><br>
                        <em>{citation['snippet'][:200]}...</em><br>
                        <small>访问于: {citation['accessed_date']}</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    else:
        st.info("暂无研究报告。请先完成一次研究任务。")


# ==================== 页脚 ====================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.9rem;'>
    🤖 自主研究智能体 | 基于 LangGraph 构建 | 
    <a href='https://github.com/AndleCandy/deep-research-agent'>GitHub</a>
</div>
""", unsafe_allow_html=True)
