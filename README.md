# RAG Project

一个可运行、可学习、可扩展的 RAG（Retrieval-Augmented Generation）项目示例。

本项目提供从知识入库、向量检索到问答生成的完整链路，支持命令行、API、Web 三种使用方式，适合用于：

- RAG 技术学习
- 企业内部技术演示
- 小规模原型验证

## 功能概览

- 文本知识入库（单条上传、目录批量导入）
- 向量检索（支持结构化 JSON 输出）
- 两阶段检索（召回 + 可选重排序 rerank）
- 带历史对话的 RAG 问答
- 检索上下文去重（减少重复片段）
- 对话历史窗口控制（仅保留最近 6 轮）
- 多租户与权限上下文（tenant_id / permission_tag）
- 会话管理（列出会话、清空会话）
- 运维命令（健康检查、系统信息、知识库统计、重置与清理）
- FastAPI 服务接口
- Streamlit 演示页面
- 最小自动化测试集
- Docker/Compose 最小部署支持

## 技术栈

- 向量库：Chroma
- 嵌入模型：DashScope text-embedding-v4
- 对话模型：Tongyi qwen-turbo
- 后端 API：FastAPI
- Web 演示：Streamlit
- 依赖管理：uv

## 快速开始

### 1. 环境要求

- Python >= 3.12
- uv
- 可用的 DASHSCOPE_API_KEY

### 2. 安装依赖

```powershell
uv sync
```

### 3. 配置环境变量

PowerShell:

```powershell
$env:DASHSCOPE_API_KEY = "your-dashscope-key"
```

或复制 `.env.example` 到 `.env` 并填写。

## 常用运行方式

### A. 命令行方式

查看系统状态：

```powershell
uv run python -m rag_project system-info
uv run python -m rag_project health-check
```

写入示例知识：

```powershell
uv run python -m rag_project upload-demo --text "这是一个测试文本" --filename test.txt
```

批量导入目录：

```powershell
uv run python -m rag_project ingest-dir ./docs --pattern *.txt --operator ops_team --tenant-id tenant_a --owner hr_lead --permission-tag internal --version v1
```

执行检索：

```powershell
uv run python -m rag_project retrieve "什么是RAG？" --json --tenant-id tenant_a --permission-tag internal
```

执行问答：

```powershell
uv run python -m rag_project ask "什么是RAG？" --session-id user_001 --tenant-id tenant_a --permission-tag internal
```

会话管理：

```powershell
uv run python -m rag_project list-sessions
uv run python -m rag_project clear-history --session-id user_001
```

知识库运维：

```powershell
uv run python -m rag_project kb-stats
uv run python -m rag_project kb-clean-system
uv run python -m rag_project kb-reset --force
```

### B. API 方式

启动 API 服务：

```powershell
uv run python -m rag_project serve-api --host 0.0.0.0 --port 8000
```

核心接口：

- GET /health
- GET /system-info
- POST /kb/upload
- POST /kb/ingest-dir
- GET /kb/stats
- POST /retrieve
- POST /ask
- GET /sessions
- DELETE /sessions/{session_id}

### C. Web 页面方式

知识库上传页面：

```powershell
uv run python -m streamlit run apps/file_upload.py --server.port 8502
```

RAG 问答页面：

```powershell
uv run python -m streamlit run apps/qa.py --server.port 8503
```

## 一键演示流程

项目提供企业演示脚本：

```powershell
uv run python scripts/run_enterprise_demo.py --knowledge-dir docs --tenant-id tenant_demo --permission-tag internal
```

该脚本会自动执行：

- system-info
- health-check
- ingest-dir
- kb-stats
- retrieve --json

## 环境变量说明

关键变量：

- DASHSCOPE_API_KEY：DashScope 访问密钥
- RAG_ENV：运行环境（dev/test/prod）
- RAG_LOG_LEVEL：日志级别（INFO/DEBUG 等）
- RAG_DATA_DIR：运行时数据目录（默认 data）
- RAG_COLLECTION_NAME：向量集合名（默认 rag）
- RAG_TOP_K：检索返回条数（默认 4）
- RAG_RERANK_ENABLED：是否启用重排序（默认 false）
- RAG_RERANK_CANDIDATE_K：重排序候选召回条数（默认 12）
- RAG_EMBEDDING_MODEL：嵌入模型名
- RAG_CHAT_MODEL：对话模型名
- RAG_PROMPT_VERSION：提示词版本
- RAG_DEFAULT_SESSION_ID：默认会话 ID
- RAG_DEBUG_PROMPT：是否打印最终渲染后的 Prompt（默认关闭；开启值支持 1/true/yes/on）

### 查看最终提示词（默认关闭）

如果你想看到“最终喂给 LLM 的 Prompt”，可以打开调试开关：

PowerShell（当前终端生效）：

```powershell
$env:RAG_DEBUG_PROMPT = "true"
uv run python -m rag_project ask "什么是RAG？" --session-id user_001
```

你会在日志中看到 `rag_prompt_rendered`，其中包含渲染后的完整提示词内容。

提示：当前问答链会先对检索到的文档片段做去重，并且只把最近 6 轮历史对话注入提示词，避免上下文重复和历史无限增长。

关闭方式：

```powershell
Remove-Item Env:RAG_DEBUG_PROMPT
```

或显式设置为 `false`。

### 启用重排序（默认关闭）

系统默认只做向量召回。若要启用两阶段检索（先召回，再重排序），可设置：

```powershell
$env:RAG_RERANK_ENABLED = "true"
$env:RAG_RERANK_CANDIDATE_K = "12"
```

说明：

- `RAG_TOP_K`：最终返回条数。
- `RAG_RERANK_CANDIDATE_K`：第一阶段召回候选数，建议大于等于 `RAG_TOP_K`。

## 项目结构

```text
rag-project/
|- apps/                 # Streamlit 启动入口
|- data/                 # 本地运行时数据
|- docs/                 # 项目文档
|- scripts/              # 演示脚本
|- src/rag_project/
|  |- api/               # FastAPI 接口层
|  |- apps/              # 前端应用逻辑
|  |- services/          # 业务服务层
|  |- stores/            # 存储抽象层
|  |- bootstrap.py       # 统一装配与初始化
|  |- cli.py             # 命令行入口
|  |- config.py          # 配置中心
|- tests/                # 自动化测试
|- Dockerfile
|- docker-compose.yml
|- pyproject.toml
|- README.md
```

## 测试

安装测试依赖并执行：

```powershell
uv sync --extra dev
uv run pytest -q
```

当前测试覆盖：

- 多租户去重逻辑
- 检索过滤构造
- API 核心接口

## 部署

### Docker Compose 一键部署

```powershell
docker compose up -d --build
```

详细步骤见 docs/deploy_api.md。

## 学习文档

若你是第一次接触 RAG，建议先阅读：

- docs/rag_learning_guide.md

## 常见问题

- 若提示 DASHSCOPE_API_KEY 未配置，请检查环境变量或 .env。
- 若提示 DashScope 账户不可用，请检查账户余额和服务状态。
- 若检索结果异常，可先执行 kb-stats 与 kb-clean-system 进行排查。

## 说明

本项目定位为学习与演示用途，默认以可理解、可运行、可扩展为目标。

