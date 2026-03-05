#!/bin/bash

# 自主研究智能体 - 快速启动脚本
# 作用：自动化环境设置和项目启动

set -e  # 遇到错误立即退出

echo "🤖 =================================="
echo "   自主研究智能体 - 快速启动"
echo "================================== 🤖"
echo ""

# ==================== 步骤1: 检查 Python 版本 ====================
echo "📋 步骤 1/5: 检查 Python 版本..."

if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python 3"
    echo "请先安装 Python 3.9 或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ 找到 Python $PYTHON_VERSION"

# ==================== 步骤2: 创建虚拟环境 ====================
echo ""
echo "📋 步骤 2/5: 创建虚拟环境..."

if [ ! -d "venv" ]; then
    echo "创建新的虚拟环境..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
else
    echo "✅ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# ==================== 步骤3: 安装依赖 ====================
echo ""
echo "📋 步骤 3/5: 安装依赖包..."

if [ -f "requirements.txt" ]; then
    echo "正在安装依赖..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    echo "✅ 依赖安装完成"
else
    echo "❌ 错误: 未找到 requirements.txt"
    exit 1
fi

# ==================== 步骤4: 配置环境变量 ====================
echo ""
echo "📋 步骤 4/5: 配置环境变量..."

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "从模板创建 .env 文件..."
        cp .env.example .env
        echo "⚠️  请编辑 .env 文件并填入您的 API 密钥"
        echo ""
        echo "需要的密钥:"
        echo "  - OPENAI_API_KEY (必需)"
        echo "  - TAVILY_API_KEY (推荐，用于真实搜索)"
        echo ""
        read -p "按 Enter 键继续..." 
    else
        echo "❌ 错误: 未找到 .env.example 模板"
        exit 1
    fi
else
    echo "✅ .env 文件已存在"
fi

# 检查必需的环境变量
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  警告: OPENAI_API_KEY 未配置"
fi

# ==================== 步骤5: 选择启动模式 ====================
echo ""
echo "📋 步骤 5/5: 选择启动模式..."
echo ""
echo "请选择启动模式:"
echo "  1. 运行示例 (推荐新手)"
echo "  2. 启动 Web UI"
echo "  3. 命令行研究"
echo "  4. 测试搜索功能"
echo "  5. 运行 Benchmark 评测"
echo "  6. 退出"
echo ""

read -p "请输入选项 (1-6): " choice

case $choice in
    1)
        echo ""
        echo "🚀 启动示例程序..."
        python examples.py
        ;;
    2)
        echo ""
        echo "🚀 启动 Web UI..."
        echo "浏览器将在 http://localhost:8501 打开"
        streamlit run app.py
        ;;
    3)
        echo ""
        read -p "请输入研究主题: " topic
        echo ""
        echo "🚀 开始研究: $topic"
        python research_agent.py "$topic"
        ;;
    4)
        echo ""
        echo "🚀 测试搜索功能..."
        python enhanced_search.py
        ;;
    5)
        echo ""
        read -p "请输入评测用模型 (留空使用默认): " bench_model
        read -p "是否启用低成本 LLM Judge? (y/N): " enable_judge
        echo ""
        echo "🚀 运行 Benchmark 评测..."
        judge_args=""
        if [[ "$enable_judge" == "y" || "$enable_judge" == "Y" ]]; then
            judge_args="--llm-judge-mode low_score --llm-judge-max-cases 3 --llm-judge-threshold 0.65 --llm-judge-weight 0.2"
        fi
        if [ -n "$bench_model" ]; then
            python run_benchmark.py --model "$bench_model" $judge_args
        else
            python run_benchmark.py $judge_args
        fi
        ;;
    6)
        echo ""
        echo "👋 再见！"
        exit 0
        ;;
    *)
        echo ""
        echo "❌ 无效选项"
        exit 1
        ;;
esac

echo ""
echo "✅ 完成！"
