from rag_project.services.vector_store import VectorStoreService


class DummyVectorStore:
    def __init__(self) -> None:
        self.last_search_kwargs = None

    def as_retriever(self, search_kwargs):
        self.last_search_kwargs = search_kwargs
        return object()


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
