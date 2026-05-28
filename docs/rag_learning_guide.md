# RAG 项目新手学习手册（面向外行）

本文档的目标是：

- 让没有接触过 RAG 的读者看懂这个项目在做什么
- 让你知道每个文件在系统里扮演什么角色
- 让你可以从命令行、API、前端三个入口跑通同一套能力
- 让你理解这个项目目前是“企业级演示版”，不是重安全和重合规的生产平台

---

## 1. 先用一句话理解这个项目

这个项目是一个“可检索知识库 + 大模型问答”的系统。

当你提问时，系统先去知识库里找相关文本，再把这些文本连同问题一起发给模型，让模型在“有依据”的前提下回答。

这就是 RAG：

- Retrieval：检索
- Augmented：增强（把检索结果拼进提示词）
- Generation：生成答案

---

## 2. 不懂 AI 也能理解的核心流程

可以把系统想成一个“有资料库的客服助手”。

用户流程：

1. 上传文档到知识库
2. 系统把文档切片并向量化，写入向量库
3. 用户提问
4. 系统先检索最相关片段
5. 系统把“问题 + 片段 + 历史对话”交给大模型
6. 返回答案，并可附带引用来源

如果没有检索到足够依据，系统提示词会引导模型谨慎回答。

---

## 3. 项目结构总览（先看这个）

你可以先从这几个目录建立心智模型：

- src/rag_project/config.py：全局配置中心
- src/rag_project/bootstrap.py：服务装配中心
- src/rag_project/cli.py：命令行入口
- src/rag_project/api/app.py：FastAPI 服务入口
- src/rag_project/services：业务服务层（知识库、检索、问答）
- src/rag_project/stores：本地会话历史存储
- src/rag_project/apps：Streamlit 演示前端
- scripts：一键流程脚本
- tests：最小自动化测试

一个重要认知：

- apps 是演示界面
- api 和 cli 才是平台能力入口

---

## 4. 配置系统是怎么工作的

配置文件在 src/rag_project/config.py。

这个文件做了三件事：

1. 读取环境变量
2. 提供默认值
3. 生成运行时路径和运行时摘要

关键配置分组：

- 目录配置：data_dir、persist_directory、chat_history_dir、md5_path
- 模型配置：embedding_model_name、chat_model_name、prompt_version
- 检索配置：top_k
- 切片配置：chunk_size、chunk_overlap、max_split_char_number
- 运行配置：app_env、log_level

你可以把它理解为：

- 代码写死的是“默认行为”
- 环境变量决定“当前环境行为”

---

## 5. bootstrap 装配层：为什么重要

文件：src/rag_project/bootstrap.py

这个模块的作用是“统一建对象”，避免在 CLI、API、前端里重复写初始化代码。

它负责：

- initialize_runtime：日志初始化、目录创建、可选 API Key 校验
- build_embedding_client：构建 embedding 客户端
- build_chat_client：构建 chat 客户端
- build_vector_store_service：构建检索服务
- build_knowledge_base_service：构建入库服务
- build_rag_service：构建 RAG 服务

对新手最重要的理解：

- 业务入口不直接 new 很多对象
- 都通过 bootstrap 统一拿到实例

这是一种常见工程化做法。

---

## 6. 三层核心服务（services）

### 6.1 知识库服务

文件：src/rag_project/services/knowledge_base.py

职责：

- 接收文本
- 去重
- 切片
- 附加元数据
- 写入向量库

关键点：

1. 去重是 tenant 维度

去重键不是单纯 md5，而是 tenant_id:md5。

这意味着：

- 同一租户上传同一内容会被去重
- 不同租户上传同一内容不会互相影响

2. 元数据标准化

每个 chunk 会带：

- doc_id
- tenant_id
- source
- version
- owner
- permission_tag
- updated_at
- operator
- chunk_index
- char_count

这是后续过滤检索和审计分析的基础。

3. 批量导入

ingest_directory 支持目录级导入，带统计输出：

- success
- skipped
- failed
- details

### 6.2 向量检索服务

文件：src/rag_project/services/vector_store.py

职责：

- 对接 Chroma
- 生成 retriever
- 执行检索
- 做统计和清理

关键点：

1. 支持 tenant 和 permission 过滤

当同时提供 tenant_id 和 permission_tag 时，使用 $and 过滤条件。

2. 可观测日志

每次检索会记录：

- query
- count
- tenant_id
- permission_tag

3. 运维能力

- stats：查看集合数量
- delete_by_source：按 source 删除脏数据

### 6.3 RAG 问答服务

文件：src/rag_project/services/rag_service.py

职责：

- 检索上下文
- 组装提示词
- 调模型
- 维护历史消息

关键点：

1. 提示词版本化

提示词模板不写死在类里，而来自 src/rag_project/prompting.py。

通过 RAG_PROMPT_VERSION 选择版本。

2. 检索增强

调用 vector_service.retrieve 拿上下文，再拼到 prompt。

3. 历史对话

通过 RunnableWithMessageHistory 接入历史，历史来源是 stores/file_history.py。

4. 观测指标

ask 会记录耗时 latency_ms、prompt_version 等信息。

---

## 7. stores：为什么还要单独一层

文件：src/rag_project/stores/file_history.py

职责：

- 把对话历史保存为本地 JSON 文件
- 支持列出会话
- 支持清空会话
- 规范化 session_id，避免非法字符

为什么不直接写在 RAG 服务里？

因为“存储策略”经常变化。

今天是文件，明天可能是 Redis 或数据库。抽出来后替换成本更低。

---

## 8. API 层（FastAPI）怎么理解

文件：src/rag_project/api/app.py

这层是“对外能力暴露层”。

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

请求体模型在 src/rag_project/api/schemas.py。

对新手的建议：

先看 /health 和 /system-info，再看 /retrieve，最后看 /ask。

/ask 是综合能力，依赖前面的所有模块。

---

## 9. CLI 层：最快的学习入口

文件：src/rag_project/cli.py

CLI 提供了几乎所有操作。

建议学习顺序：

1. system-info
2. health-check
3. upload-demo 或 ingest-dir
4. retrieve
5. ask
6. kb-stats / kb-clean-system / kb-reset
7. serve-api

你可以把 CLI 理解为“平台调试面板”。

---

## 10. Streamlit 前端：演示用，不是平台核心

文件：

- src/rag_project/apps/file_upload_app.py
- src/rag_project/apps/qa_app.py

它们是“演示入口”。

作用：

- 更直观地上传文本
- 在页面里进行会话问答
- 输入 tenant 和 permission 上下文

但核心业务逻辑不在这里，核心在 services、api、cli。

---

## 11. 提示词治理（prompting）

文件：src/rag_project/prompting.py

它维护一个 PROMPT_REGISTRY（提示词注册表）。

当前提供：

- v1
- v2_enterprise_demo

v2 的特点是更强调证据约束：

- 不允许臆测
- 证据不足要明确说明

这不是“万能防幻觉”，但比纯自由问答更可控。

---

## 12. 日志与错误处理

日志文件：src/rag_project/observability.py

- 输出 JSON 结构日志
- 字段包含时间、级别、logger、message

错误处理文件：src/rag_project/errors.py

- 统一项目异常 RagProjectError
- 外部服务异常 ExternalServiceError
- 对常见问题做用户友好提示（如 API Key、欠费）

这样做的价值：

- 错误信息对业务方更可读
- 便于后续接日志平台

---

## 13. 最小测试集在验证什么

测试目录：tests

### 13.1 多租户去重

tests/test_multitenant_dedupe.py

验证点：

- tenant_a 保存过的 hash，不会影响 tenant_b

### 13.2 检索过滤构造

tests/test_retrieval_filter.py

验证点：

- tenant + permission 同时存在时，过滤器应为 $and
- 仅 tenant 时，过滤器是单条件

### 13.3 API 核心接口

tests/test_api_core.py

验证点：

- health 正常响应
- retrieve 能接收过滤参数并返回
- ask 返回答案与 citations

这些测试属于“最小可信保障”，不是完整回归体系。

---

## 14. 一键演示脚本做了什么

文件：scripts/run_enterprise_demo.py

会按顺序执行：

1. system-info
2. health-check
3. ingest-dir
4. kb-stats
5. retrieve --json

这是给初学者最友好的“端到端流程入口”。

---

## 15. 容器化与部署

你可以通过以下文件做最小部署：

- Dockerfile
- docker-compose.yml
- docs/deploy_api.md

部署方式分两种：

- 本机直接 uv 运行
- Docker Compose 一键部署

建议先本机，确认流程后再容器化。

---

## 16. 新手常见误区

1. 以为“模型回答错”一定是模型问题

很多时候是检索不到、过滤条件太严、知识没入库。

2. 只看前端不看服务层

前端只是展示。真正决定行为的是 services 和 api。

3. 忽略元数据

tenant_id、permission_tag 不是装饰字段，它们决定是否串库。

4. 忽略运维命令

kb-stats、kb-clean-system、kb-reset 是你排障的第一工具。

---

## 17. 建议的学习路线（7 步）

1. 通读本文，建立整体认知
2. 跑 uv run python -m rag_project system-info
3. 跑 scripts/run_enterprise_demo.py
4. 阅读 config -> bootstrap -> cli
5. 阅读 knowledge_base -> vector_store -> rag_service
6. 用 FastAPI 调 /retrieve 和 /ask
7. 阅读 tests，理解“如何验证自己改动没破坏核心能力”

---

## 18. 这套项目离真正企业生产还差什么

这个项目已经是“企业级演示版”，但仍有明显边界：

- 向量库仍是本地 Chroma（不是高可用集群）
- 会话历史仍是文件（不是 Redis/数据库）
- 缺少完善鉴权、审计、脱敏、权限继承
- 缺少完整离线/在线评测闭环
- 缺少 CI/CD、灰度发布、回滚策略

这些并不影响学习，但会影响真实生产可用性。

---

## 19. 总结

如果你是外行，可以先记住三句话：

1. RAG 的本质是“先找资料，再让模型作答”。
2. 这个项目已经把“演示 UI、服务逻辑、API 接口、运维命令”分开了。
3. 学会看 config、services、api、tests，你就能从会用走向会改。

当你能解释清楚下面这个链路时，就算真正入门了：

- 文档如何入库
- 问题如何检索
- 上下文如何拼 prompt
- 模型如何返回答案
- 为什么答案能追溯到来源
