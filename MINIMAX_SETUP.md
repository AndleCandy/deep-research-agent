# Minimax-m2.1 配置指南

本文档说明如何将自主研究智能体配置为使用 Minimax-m2.1 模型。

## 快速开始

### 方式1: 环境变量配置（推荐）

1. 复制环境变量模板：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入 Minimax 配置：
```env
LLM_MODEL=minimax-m2.1
LLM_BASE_URL=https://api.minimax.chat/v1
LLM_API_KEY=your-minimax-api-key-here
```

3. 运行研究：
```bash
python research_agent.py "LangGraph 核心概念"
```

### 方式2: 代码中配置

```python
from research_agent import run_research_sync

# 直接传入配置
result = run_research_sync(
    topic="LangGraph 核心概念",
    model="minimax-m2.1",
    base_url="https://api.minimax.chat/v1",
    api_key="your-minimax-api-key"
)

print(result["report"])
```

### 方式3: 全局配置

```python
from research_agent import run_research_sync, set_model_config

# 设置全局配置
set_model_config(
    model="minimax-m2.1",
    base_url="https://api.minimax.chat/v1",
    api_key="your-minimax-api-key"
)

# 之后所有调用都使用此配置
result = run_research_sync("LangGraph 核心概念")
```

## Web UI 配置

启动 Streamlit 界面：
```bash
streamlit run app.py
```

在侧边栏的 **"⚙️ 配置"** 中：
1. 选择 **"LLM 模型"** 为 `minimax-m2.1`
2. 输入您的 **Minimax API Key**
3. 开始研究

## API 说明

### 新增函数

#### `set_model_config()`
设置全局模型配置。

```python
set_model_config(
    model="minimax-m2.1",           # 模型名称
    base_url="https://api.minimax.chat/v1",  # API 基础 URL
    api_key="your-api-key",         # API 密钥
    temperature=0.3                 # 温度参数
)
```

#### `get_model_config()`
获取当前模型配置。

```python
config = get_model_config()
print(config["model"])  # 输出当前模型名称
```

#### `create_llm()`
使用当前配置创建 LLM 实例。

```python
llm = create_llm(temperature=0.5)
```

### 修改的函数

#### `create_research_agent()`
现在接受可选的配置参数：

```python
agent = create_research_agent(
    model="minimax-m2.1",
    base_url="https://api.minimax.chat/v1",
    api_key="your-api-key"
)
```

#### `run_research()` / `run_research_sync()`
现在接受可选的配置参数：

```python
result = run_research_sync(
    topic="研究主题",
    model="minimax-m2.1",
    base_url="https://api.minimax.chat/v1",
    api_key="your-api-key"
)
```

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_MODEL` | 模型名称 | `gpt-4o` |
| `LLM_BASE_URL` | API 基础 URL | `None` |
| `LLM_API_KEY` | API 密钥 | `None` |
| `LLM_TEMPERATURE` | 温度参数 | `0.3` |
| `OPENAI_API_KEY` | OpenAI API 密钥（备选） | `None` |

**优先级**: `LLM_API_KEY` > `OPENAI_API_KEY`

## 支持的模型

### OpenAI 系列
- `gpt-4o`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

### Minimax 系列
- `minimax-m2.1`（自动使用 `https://api.minimax.chat/v1`）

### 其他 OpenAI 兼容接口
任何提供 OpenAI 兼容 API 的服务都可以使用，只需设置：
- `LLM_MODEL=your-model-name`
- `LLM_BASE_URL=https://api.your-provider.com/v1`
- `LLM_API_KEY=your-api-key`

## 示例代码

运行 Minimax 专用示例：
```bash
python minimax_example.py
```

## 故障排查

### 问题1: API 密钥错误
```
错误: Authentication failed
解决: 检查 LLM_API_KEY 是否正确设置
```

### 问题2: 连接失败
```
错误: Connection error
解决: 检查网络连接和 LLM_BASE_URL 是否正确
```

### 问题3: 模型不存在
```
错误: Model not found
解决: 确认模型名称拼写正确，且账户有权限访问该模型
```

## 获取 Minimax API Key

1. 访问 [Minimax 官网](https://www.minimax.chat/)
2. 注册/登录账户
3. 在控制台创建 API Key
4. 复制 Key 到配置中
