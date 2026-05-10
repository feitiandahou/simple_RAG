
# 简易 RAG（Retrieval-Augmented Generation）项目

这是一个用于学习和快速搭建简易 RAG 流程的示例项目。项目包含基本的文档上传、向量化（索引）和基于检索的问答示例脚本，便于扩展为真实的检索增强生成服务。

**快速开始**
1. 环境管理（使用 `uv`）

本项目使用 `uv` 管理虚拟环境。请先确保已安装 `uv`，然后使用 `uv` 创建并激活环境（具体命令依 `uv` 版本与配置而异）：

```powershell

uv sync

uv run python -m streamlit run app_file_upload.py --server.port 8502

uv run python -m streamlit run app_simple_example.py --server.port 8503
```

**环境变量**
- `OPENAI_API_KEY`（或你使用的 LLM 服务密钥）
- 可选：`VECTOR_STORE_PATH`（向量索引持久化路径）

在 PowerShell 设置示例：

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

**运行示例**
- 构建索引/上传文档（使用 `app_file_upload.py`）：

```powershell
python app_file_upload.py
```

- 运行查询流程（示例）：

```powershell
python main.py --query "你的问题"
```

（注：具体命令参数取决于脚本实现，可根据需要修改 `main.py` 与 `app_file_upload.py`）

**实现要点 / 推荐流程**
- 文档采集 -> 文档切分 -> 嵌入向量化 -> 建立向量检索索引 -> 查询时检索 top-k 文档 -> 将检索到的上下文与问题一起送入 LLM 生成最终答案。

**开发者提示**
- 将密钥与敏感配置放入 `.env` 或系统环境变量，不要提交到仓库。
- 代码风格：建议使用 `black` 、`ruff` 等工具进行格式化和静态检查。

**贡献**
欢迎通过 Issues 和 Pull Requests 贡献改进：文档处理、向量库替换（FAISS、Weaviate、Chroma 等）、LLM 后端切换等。

**许可证**
MIT（或根据需要替换）。

