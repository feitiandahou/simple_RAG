from fastapi.testclient import TestClient
from langchain_core.documents import Document

from rag_project.api import app as api_app


class FakeVectorService:
    def retrieve(self, query, tenant_id=None, permission_tag=None):
        return [
            Document(
                page_content=f"hit for {query}",
                metadata={
                    "source": "demo.txt",
                    "tenant_id": tenant_id or "",
                    "permission_tag": permission_tag or "",
                },
            )
        ]

    def stats(self):
        return {"collection_name": "rag", "count": 1, "top_k": 4}


class FakeRagService:
    def ask(self, question, config, tenant_id=None, permission_tag=None):
        return f"answer for {question} ({tenant_id}:{permission_tag})"


class FakeKbService:
    def upload_by_str(self, *args, **kwargs):
        return "ok"

    def ingest_directory(self, *args, **kwargs):
        return {"success": 1, "skipped": 0, "failed": 0, "details": []}


def test_health_endpoint() -> None:
    client = TestClient(api_app.app)
    response = client.get("/health")

    assert response.status_code == 200
    assert "runtime_dirs_ready" in response.json()


def test_retrieve_endpoint_with_filters(monkeypatch) -> None:
    api_app._vector_service.cache_clear()
    monkeypatch.setattr(api_app, "_vector_service", lambda: FakeVectorService())

    client = TestClient(api_app.app)
    response = client.post(
        "/retrieve",
        json={
            "query": "what is rag",
            "tenant_id": "tenant_demo",
            "permission_tag": "internal",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["metadata"]["tenant_id"] == "tenant_demo"
    assert payload[0]["metadata"]["permission_tag"] == "internal"


def test_ask_endpoint_returns_citations(monkeypatch) -> None:
    api_app._rag_service.cache_clear()
    api_app._vector_service.cache_clear()
    api_app._kb_service.cache_clear()

    monkeypatch.setattr(api_app, "_rag_service", lambda: FakeRagService())
    monkeypatch.setattr(api_app, "_vector_service", lambda: FakeVectorService())
    monkeypatch.setattr(api_app, "_kb_service", lambda: FakeKbService())

    client = TestClient(api_app.app)
    response = client.post(
        "/ask",
        json={
            "question": "what is rag",
            "session_id": "session_a",
            "tenant_id": "tenant_demo",
            "permission_tag": "internal",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert payload["citations"][0]["source"] == "demo.txt"
