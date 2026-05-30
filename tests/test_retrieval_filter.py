from rag_project.services.vector_store import VectorStoreService
from langchain_core.documents import Document


class DummyVectorStore:
    def __init__(self) -> None:
        self.last_search_kwargs = None
        self.docs: list[Document] = []

    def as_retriever(self, search_kwargs):
        self.last_search_kwargs = search_kwargs

        docs = self.docs

        class DummyRetriever:
            def invoke(self_inner, query):  # noqa: ARG002
                return docs

        return DummyRetriever()


def test_retriever_uses_and_filter_for_tenant_and_permission() -> None:
    service = VectorStoreService.__new__(VectorStoreService)
    service.vector_store = DummyVectorStore()

    service.get_retriever(tenant_id="tenant_demo", permission_tag="internal")

    assert service.vector_store.last_search_kwargs == {
        "k": 4,
        "filter": {
            "$and": [
                {"tenant_id": "tenant_demo"},
                {"permission_tag": "internal"},
            ]
        },
    }


def test_retriever_uses_single_filter_when_only_tenant() -> None:
    service = VectorStoreService.__new__(VectorStoreService)
    service.vector_store = DummyVectorStore()

    service.get_retriever(tenant_id="tenant_demo", permission_tag=None)

    assert service.vector_store.last_search_kwargs == {
        "k": 4,
        "filter": {"tenant_id": "tenant_demo"},
    }


def test_retrieve_uses_candidate_k_and_reranks_when_enabled(monkeypatch) -> None:
    from rag_project import config as config_module

    monkeypatch.setattr(config_module.settings, "rerank_enabled", True)
    monkeypatch.setattr(config_module.settings, "rerank_candidate_k", 3)
    monkeypatch.setattr(config_module.settings, "top_k", 1)

    service = VectorStoreService.__new__(VectorStoreService)
    service.vector_store = DummyVectorStore()
    service.vector_store.docs = [
        Document(page_content="irrelevant text", metadata={}),
        Document(page_content="best match for washing", metadata={}),
        Document(page_content="another unrelated note", metadata={}),
    ]

    docs = service.retrieve("washing")

    assert service.vector_store.last_search_kwargs == {"k": 3}
    assert len(docs) == 1
    assert docs[0].page_content == "best match for washing"


def test_retrieve_uses_top_k_only_when_rerank_disabled(monkeypatch) -> None:
    from rag_project import config as config_module

    monkeypatch.setattr(config_module.settings, "rerank_enabled", False)
    monkeypatch.setattr(config_module.settings, "top_k", 2)

    service = VectorStoreService.__new__(VectorStoreService)
    service.vector_store = DummyVectorStore()
    service.vector_store.docs = [Document(page_content="a", metadata={})]

    service.retrieve("washing")

    assert service.vector_store.last_search_kwargs == {"k": 2}
