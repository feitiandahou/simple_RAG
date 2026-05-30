import os
from collections.abc import Iterator
import time

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableWithMessageHistory

from rag_project.config import settings
from rag_project.errors import ensure_dashscope_api_key, wrap_external_error
from rag_project.observability import get_logger
from rag_project.prompting import build_prompt_template
from rag_project.services.vector_store import VectorStoreService
from rag_project.stores.file_history import get_history

logger = get_logger(__name__)


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


class RagService:
    def __init__(self, vector_service: VectorStoreService, chat_model) -> None:
        ensure_dashscope_api_key(os.environ.get("DASHSCOPE_API_KEY"))

        self.vector_service = vector_service
        self.prompt_template = build_prompt_template()
        self.chat_model = chat_model
        self.chain = self._build_chain()

    def _build_chain(self):
        prompt_debug_enabled = _is_truthy(os.environ.get("RAG_DEBUG_PROMPT"))
        max_history_messages = 12  # Keep last 6 rounds (human+ai)

        def dedupe_documents(docs: list[Document]) -> list[Document]:
            seen: set[str] = set()
            unique_docs: list[Document] = []
            for doc in docs:
                metadata = doc.metadata or {}
                source = metadata.get("source", "")
                chunk_index = metadata.get("chunk_index", "")
                doc_id = metadata.get("doc_id", "")
                key = f"{doc_id}|{source}|{chunk_index}|{doc.page_content}"
                if key in seen:
                    continue
                seen.add(key)
                unique_docs.append(doc)
            return unique_docs

        def format_document(docs: list[Document]) -> str:
            if not docs:
                return "无相关参考资料。"
            deduped_docs = dedupe_documents(docs)
            return "\n\n".join(
                f"文档片段：{doc.page_content}\n文档元数据: {doc.metadata}" for doc in deduped_docs
            )

        def retrieve_context(value: dict) -> str:
            docs = self.vector_service.retrieve(
                value["input"],
                tenant_id=value.get("tenant_id"),
                permission_tag=value.get("permission_tag"),
            )
            return format_document(list(docs))

        def format_for_prompt_template(value: dict) -> dict:
            history_messages = value["input"]["history"][-max_history_messages:]
            return {
                "input": value["input"]["input"],
                "context": value["context"],
                "history": history_messages,
            }

        def debug_prompt(prompt_value):
            if not prompt_debug_enabled:
                return prompt_value

            try:
                messages = prompt_value.to_messages()
                rendered_prompt = "\n\n".join(
                    f"[{getattr(message, 'type', 'unknown')}] {getattr(message, 'content', str(message))}"
                    for message in messages
                )
            except Exception:
                rendered_prompt = str(prompt_value)

            logger.info(
                "rag_prompt_rendered (version=%s)\n%s",
                settings.prompt_version,
                rendered_prompt,
            )
            return prompt_value

        chain = (
            {
                "input": RunnablePassthrough(),
                "context": RunnableLambda(retrieve_context),
            }
            | RunnableLambda(format_for_prompt_template)
            | self.prompt_template
            | RunnableLambda(debug_prompt)
            | self.chat_model
            | StrOutputParser()
        )

        return RunnableWithMessageHistory(
            chain,
            get_history,
            input_message_key="input",
            history_messages_key="history",
        )

    def ask(
        self,
        question: str,
        config: RunnableConfig,
        tenant_id: str | None = None,
        permission_tag: str | None = None,
    ) -> str:
        try:
            start = time.perf_counter()
            answer = self.chain.invoke(
                {
                    "input": question,
                    "tenant_id": tenant_id,
                    "permission_tag": permission_tag,
                },
                config,
            )
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.info(
                "rag_ask_completed",
                extra={
                    "question": question,
                    "answer_size": len(answer),
                    "tenant_id": tenant_id or "",
                    "permission_tag": permission_tag or "",
                    "latency_ms": elapsed_ms,
                    "prompt_version": settings.prompt_version,
                },
            )
            return answer
        except Exception as exc:
            raise wrap_external_error(exc, "执行 RAG 问答") from exc

    def stream_answer(
        self,
        question: str,
        config: RunnableConfig,
        tenant_id: str | None = None,
        permission_tag: str | None = None,
    ) -> Iterator[str]:
        try:
            logger.info(
                "rag_stream_started",
                extra={
                    "question": question,
                    "tenant_id": tenant_id or "",
                    "permission_tag": permission_tag or "",
                    "prompt_version": settings.prompt_version,
                },
            )
            for chunk in self.chain.stream(
                {
                    "input": question,
                    "tenant_id": tenant_id,
                    "permission_tag": permission_tag,
                },
                config,
            ):
                yield chunk
        except Exception as exc:
            raise wrap_external_error(exc, "执行 RAG 问答") from exc