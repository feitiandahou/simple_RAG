# 简易 RAG（Retrieval-Augmented Generation）项目

这是一个用于学习 RAG 基本流程的示例项目，已经按完整项目的常见规范重组为“核心包 + 应用入口 + 脚本入口 + 运行时数据目录”的结构，便于继续扩展。

当前项目包含 3 条主线能力：

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

关键环境变量：

- `DASHSCOPE_API_KEY`：DashScope 的模型与嵌入调用密钥

PowerShell 示例：

```powershell
$env:DASHSCOPE_API_KEY = "your-dashscope-key"
```

也可以复制 `.env.example` 为 `.env` 后填写：

```env
DASHSCOPE_API_KEY="your-dashscope-key"
```

## 项目结构

```text
rag-project/
|- apps/
|  |- file_upload.py
|  |- qa.py
|- data/
|  |- chat_history/
|  |- chroma_db/
|  |- md5.txt
|- scripts/
|  |- seed_knowledge_base.py
|  |- check_retrieval.py
|  |- run_rag_demo.py
|- src/
|  |- rag_project/
|     |- apps/
|     |- services/
|     |- stores/
|     |- cli.py
|     |- config.py
|- .env.example
|- pyproject.toml
|- README.md
```

目录职责：

- `src/rag_project/`：项目核心代码
- `src/rag_project/services/`：知识库、向量检索、RAG 业务逻辑
- `src/rag_project/stores/`：本地历史消息存储
- `apps/`：Streamlit 启动入口
- `scripts/`：命令行演示脚本入口
- `data/`：本地运行时数据目录，不提交到仓库

## 推荐使用顺序

1. 准备环境变量和依赖
2. 写入测试知识到向量库
3. 验证向量检索
4. 运行 RAG 脚本或 Web 页面

## 命令行验证

### 1. 写入测试知识

```powershell
uv run python scripts/seed_knowledge_base.py
```

可选参数：

```powershell
uv run python scripts/seed_knowledge_base.py --text "这是新的测试文本" --filename custom.txt
```

### 2. 验证向量检索

```powershell
uv run python scripts/check_retrieval.py "什么是RAG？"
```

### 3. 验证完整 RAG 链

```powershell
uv run python scripts/run_rag_demo.py "什么是RAG？"
```

这个脚本会执行：

- 问题向量检索
- 组装提示词
- 调用 Tongyi 模型生成回答
- 记录本轮对话历史

## Web 页面启动方式

### 1. 知识库上传页面

```powershell
uv run python -m streamlit run apps/file_upload.py --server.port 8502
```

### 2. RAG 问答页面

```powershell
uv run python -m streamlit run apps/qa.py --server.port 8503
```

说明：在当前 Windows 环境中，直接使用 `uv run streamlit run ...` 可能会出现 `uv trampoline failed to canonicalize script path`。使用 `uv run python -m streamlit run ...` 更稳定。

## 当前配置说明

默认配置位于 `src/rag_project/config.py`：

- 运行时数据目录：`./data`
- 向量库目录：`./data/chroma_db`
- 历史消息目录：`./data/chat_history`
- 去重文件：`./data/md5.txt`
- 集合名：`rag`
- 嵌入模型：`text-embedding-v4`
- 聊天模型：`qwen-turbo`
- 默认会话 ID：`user_001`

如果你清空 `data/chroma_db/` 或 `data/md5.txt`，会影响检索结果和去重逻辑。

## 一个最小可用流程

```powershell
uv sync
uv run python scripts/seed_knowledge_base.py
uv run python scripts/check_retrieval.py
uv run python scripts/run_rag_demo.py
uv run python -m streamlit run apps/qa.py --server.port 8504
```

## 后续可扩展方向

- 支持上传更多文本格式，而不只限于 `.txt`
- 为检索器增加 `k` 值、阈值等可配置项
- 将对话历史和知识库路径改为按用户隔离
- 用 LangGraph 替代 `RunnableWithMessageHistory`

## 开发提示

- 将密钥放在 `.env` 中，不要提交到仓库。
- 如需重建知识库，可清理 `data/chroma_db/` 后重新执行写入脚本。
- 如需清空历史对话，可删除 `data/chat_history/` 下对应会话文件。
- 新增业务代码优先放在 `src/rag_project/` 下，不要再回到根目录平铺脚本。

## 常见运行问题

- 如果命令行或页面提示 `DashScope 账户当前处于欠费或不可用状态`，说明当前阿里云百炼账户余额、账单或服务状态异常，不是本地代码结构问题。
- 如果提示 `请先设置 DASHSCOPE_API_KEY 环境变量`，说明本地 `.env` 或当前终端环境变量没有正确配置。
- 这两个问题修复后，无需改代码，直接重新执行 `scripts/` 或 `apps/` 下的入口即可。

