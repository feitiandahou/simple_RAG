from collections.abc import Sequence
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from rag_project.config import settings
from rag_project.errors import wrap_external_error
from rag_project.observability import get_logger


logger = get_logger(__name__)


class VectorStoreService:
    def __init__(self, embedding) -> None:
        self.embedding = embedding
        self.vector_store = Chroma(
            collection_name=settings.collection_name,
            embedding_function=self.embedding,
            persist_directory=str(settings.persist_directory),
        )

    def get_retriever(self, tenant_id: str | None = None, permission_tag: str | None = None):
        search_kwargs: dict[str, Any] = {"k": settings.top_k}
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
            docs = self.get_retriever(tenant_id=tenant_id, permission_tag=permission_tag).invoke(query)
            logger.info(
                "vector_retrieval_completed",
                extra={
                    "query": query,
                    "count": len(docs),
                    "tenant_id": tenant_id or "",
                    "permission_tag": permission_tag or "",
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