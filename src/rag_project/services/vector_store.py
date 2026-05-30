from collections.abc import Sequence
import re
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from rag_project.config import settings
from rag_project.errors import wrap_external_error
from rag_project.observability import get_logger


logger = get_logger(__name__)


def _tokenize_for_rerank(text: str) -> set[str]:
    # Keep both CJK single-char tokens and ASCII words to support mixed-language queries.
    return {token for token in re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", text.lower()) if token}


def _rerank_score(query: str, doc: Document) -> float:
    doc_text = doc.page_content or ""
    query_tokens = _tokenize_for_rerank(query)
    doc_tokens = _tokenize_for_rerank(doc_text)
    if not query_tokens:
        return 0.0

    overlap = len(query_tokens.intersection(doc_tokens)) / len(query_tokens)
    contains_bonus = 0.2 if query and query in doc_text else 0.0
    return overlap + contains_bonus


class VectorStoreService:
    def __init__(self, embedding) -> None:
        self.embedding = embedding
        self.vector_store = Chroma(
            collection_name=settings.collection_name,
            embedding_function=self.embedding,
            persist_directory=str(settings.persist_directory),
        )

    def get_retriever(
        self,
        tenant_id: str | None = None,
        permission_tag: str | None = None,
        k: int | None = None,
    ):
        search_kwargs: dict[str, Any] = {"k": k or settings.top_k}
        filter_parts: list[dict[str, str]] = []
        if tenant_id:
            filter_parts.append({"tenant_id": tenant_id})
        if permission_tag:
            filter_parts.append({"permission_tag": permission_tag})
        if len(filter_parts) == 1:
            search_kwargs["filter"] = filter_parts[0]
        elif len(filter_parts) > 1:
            search_kwargs["filter"] = {"$and": filter_parts}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def retrieve(
        self,
        query: str,
        tenant_id: str | None = None,
        permission_tag: str | None = None,
    ) -> Sequence[Document]:
        try:
            candidate_k = max(settings.top_k, settings.rerank_candidate_k) if settings.rerank_enabled else settings.top_k
            docs = self.get_retriever(
                tenant_id=tenant_id,
                permission_tag=permission_tag,
                k=candidate_k,
            ).invoke(query)

            if settings.rerank_enabled:
                ranked_docs = sorted(docs, key=lambda doc: _rerank_score(query, doc), reverse=True)
                docs = ranked_docs[: settings.top_k]

            logger.info(
                "vector_retrieval_completed",
                extra={
                    "query": query,
                    "count": len(docs),
                    "tenant_id": tenant_id or "",
                    "permission_tag": permission_tag or "",
                    "rerank_enabled": int(settings.rerank_enabled),
                    "candidate_k": candidate_k,
                },
            )
            return docs
        except Exception as exc:
            raise wrap_external_error(exc, "执行向量检索") from exc

    def stats(self) -> dict[str, Any]:
        # Chroma API returns implementation-specific metadata; we keep this optional.
        collection = self.vector_store._collection  # noqa: SLF001
        return {
            "collection_name": settings.collection_name,
            "count": collection.count(),
            "top_k": settings.top_k,
        }

    def delete_by_source(self, source: str) -> dict[str, Any]:
        collection = self.vector_store._collection  # noqa: SLF001
        before = collection.count()
        self.vector_store.delete(where={"source": source})
        after = collection.count()
        return {
            "collection_name": settings.collection_name,
            "source": source,
            "before": before,
            "after": after,
            "deleted": max(before - after, 0),
        }