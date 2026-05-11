# 简易 RAG（Retrieval-Augmented Generation）项目

这是一个用于学习 RAG 基本流程的示例项目，包含 3 条主线能力：

- 文本写入知识库
- 从向量库检索相关内容
- 带历史对话的 RAG 问答

当前项目基于以下组件：

- 向量库：Chroma
- 嵌入模型：DashScope `text-embedding-v4`
- 对话模型：Tongyi `qwen-turbo`
- Web 界面：Streamlit

## 运行环境

- Python `>= 3.12`
- 依赖管理：`uv`
- 需要有效的 `DASHSCOPE_API_KEY`

安装依赖：

```powershell
uv sync
```

## 环境变量

本项目实际使用的关键环境变量如下：

- `DASHSCOPE_API_KEY`：DashScope 的模型与嵌入调用密钥

PowerShell 示例：

```powershell
$env:DASHSCOPE_API_KEY = "your-dashscope-key"
```

也可以在项目根目录创建 `.env` 文件：

```env
DASHSCOPE_API_KEY="your-dashscope-key"
```

## 项目结构

- `knowledge_base.py`：将文本切分后写入 Chroma 向量库
- `vector_stores.py`：连接已有向量库并返回检索器
- `file_history_store.py`：将对话历史写入本地 `chat_history/` 目录
- `rag.py`：组装完整 RAG 调用链，包含检索、提示词、模型和历史对话
- `app_file_upload.py`：Streamlit 知识库上传页面
- `app_qa.py`：Streamlit RAG 问答页面
- `app_simple_example.py`：不带检索的通义千问聊天示例
- `config_data.py`：项目运行配置
- `main.py`：当前仅为占位脚本，没有接入实际 RAG 流程

## 推荐使用顺序

建议按下面顺序体验项目：

1. 准备环境变量和依赖
2. 先写入一段测试知识到向量库
3. 验证向量检索是否正常
4. 运行 RAG 脚本或 Streamlit 页面

## 命令行验证

### 1. 写入测试知识

```powershell
uv run python knowledge_base.py
```

这个脚本会写入一条测试文本到本地 Chroma 数据库。

### 2. 验证向量检索

```powershell
uv run python vector_stores.py
```

如果知识库中已有内容，这个脚本会打印检索到的 `Document` 列表。

### 3. 验证完整 RAG 链

```powershell
uv run python rag.py
```

这个脚本会执行：

- 问题向量检索
- 组装提示词
- 调用 Tongyi 模型生成回答
- 记录本轮对话历史

## Web 页面启动方式

### 1. 知识库上传页面

```powershell
uv run python -m streamlit run app_file_upload.py --server.port 8502
```


### 2. RAG 问答页面

```powershell
uv run python -m streamlit run app_qa.py --server.port 8503
```

说明：在当前 Windows 环境中，直接使用 `uv run streamlit run ...` 可能会出现 `uv trampoline failed to canonicalize script path`。使用 `uv run python -m streamlit run ...` 更稳定。

## 当前配置说明

默认配置位于 `config_data.py`：

- 向量库目录：`./chroma_db`
- 集合名：`rag`
- 嵌入模型：`text-embedding-v4`
- 聊天模型：`qwen-turbo`
- 默认会话 ID：`user_001`

如果你清空 `chroma_db/` 或 `md5.txt`，会影响检索结果和去重逻辑。

## 当前已确认的注意点

- 项目当前没有静态错误，`rag.py` 和 `app_qa.py` 已能运行。
- `main.py` 目前只是占位文件，README 不再把它当作实际入口。
- `rag.py` 运行时会看到 `RunnableWithMessageHistory` 的弃用警告，但不影响当前功能。
- 如果知识库里只有测试文本，那么检索结果和最终回答会明显偏向那条测试数据。

## 一个最小可用流程

```powershell
uv sync
uv run python knowledge_base.py
uv run python vector_stores.py
uv run python rag.py
uv run python -m streamlit run app_qa.py --server.port 8504
```

## 后续可扩展方向

- 支持上传更多文本格式，而不只限于 `.txt`
- 为检索器增加 `k` 值、阈值等可配置项
- 将对话历史和知识库路径改为按用户隔离
- 用 LangGraph 替代 `RunnableWithMessageHistory`

## 开发提示

- 将密钥放在 `.env` 中，不要提交到仓库。
- 如需重建知识库，可清理 `chroma_db/` 后重新执行写入脚本。
- 如需清空历史对话，可删除 `chat_history/` 下对应会话文件。

