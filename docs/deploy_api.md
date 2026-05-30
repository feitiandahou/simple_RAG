# API 最小部署说明

本说明用于快速部署企业演示版 API 服务。

## 方式一：本机直接启动

1. 安装依赖：

```powershell
uv sync
```

2. 配置环境变量（至少包含 DASHSCOPE_API_KEY）：

```powershell
$env:DASHSCOPE_API_KEY = "your-dashscope-key"
```

如需查看最终渲染后的 Prompt（默认关闭）：

```powershell
$env:RAG_DEBUG_PROMPT = "true"
```

如需启用检索重排序（默认关闭）：

```powershell
$env:RAG_RERANK_ENABLED = "true"
$env:RAG_RERANK_CANDIDATE_K = "12"
```

3. 启动 API：

```powershell
uv run python -m rag_project serve-api --host 0.0.0.0 --port 8000
```

4. 健康检查：

```powershell
curl http://127.0.0.1:8000/health
```

## 方式二：Docker Compose 一键部署

1. 在项目根目录准备 `.env`，至少包含：

```env
DASHSCOPE_API_KEY=your-dashscope-key
RAG_ENV=prod
RAG_LOG_LEVEL=INFO
RAG_DEBUG_PROMPT=false
RAG_RERANK_ENABLED=false
RAG_RERANK_CANDIDATE_K=12
```

2. 构建并启动：

```powershell
docker compose up -d --build
```

3. 查看服务日志：

```powershell
docker compose logs -f rag-api
```

4. 验证接口：

```powershell
curl http://127.0.0.1:8000/system-info
```

## 最小生产建议

- 将 `DASHSCOPE_API_KEY` 放入安全密钥管理系统，不要硬编码在镜像中。
- 将 `./data` 映射到持久化磁盘或云存储卷。
- 对外暴露前增加网关层（鉴权、限流、审计）。
