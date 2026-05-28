from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException

from rag_project.api.schemas import AskRequest, IngestDirectoryRequest, RetrieveRequest, UploadRequest
from rag_project.bootstrap import (
    build_knowledge_base_service,
    build_rag_service,
    build_vector_store_service,
    initialize_runtime,
)
from rag_project.config import settings
from rag_project.errors import RagProjectError
from rag_project.stores.file_history import clear_session_history, list_session_ids


app = FastAPI(title="RAG Project API", version="0.1.0")


@lru_cache(maxsize=1)
def _kb_service():
    initialize_runtime(require_api_key=True)
    return build_knowledge_base_service()


@lru_cache(maxsize=1)
def _vector_service():
    initialize_runtime(require_api_key=True)
    return build_vector_store_service()


@lru_cache(maxsize=1)
def _rag_service():
    initialize_runtime(require_api_key=True)
    return build_rag_service()


@app.get("/health")
def health() -> dict:
    initialize_runtime(require_api_key=False)
    return {
        "runtime_dirs_ready": settings.data_dir.exists()
        and settings.persist_directory.exists()
        and settings.chat_history_dir.exists(),
        "md5_file_ready": settings.md5_path.exists(),
        "api_key_configured": bool(__import__("os").environ.get("DASHSCOPE_API_KEY")),
    }


@app.get("/system-info")
def system_info() -> dict:
    initialize_runtime(require_api_key=False)
    return settings.system_summary()


@app.post("/kb/upload")
def kb_upload(payload: UploadRequest) -> dict:
    try:
        message = _kb_service().upload_by_str(
            payload.text,
            payload.filename,
            operator=payload.operator,
            tenant_id=payload.tenant_id,
            owner=payload.owner,
            permission_tag=payload.permission_tag,
            version=payload.version,
        )
        return {"message": message}
    except RagProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/kb/ingest-dir")
def kb_ingest_dir(payload: IngestDirectoryRequest) -> dict:
    try:
        return _kb_service().ingest_directory(
            directory=Path(payload.directory),
            glob_pattern=payload.pattern,
            operator=payload.operator,
            tenant_id=payload.tenant_id,
            owner=payload.owner,
            permission_tag=payload.permission_tag,
            version=payload.version,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/kb/stats")
def kb_stats() -> dict:
    return _vector_service().stats()


@app.post("/retrieve")
def retrieve(payload: RetrieveRequest) -> list[dict]:
    try:
        docs = _vector_service().retrieve(
            payload.query,
            tenant_id=payload.tenant_id,
            permission_tag=payload.permission_tag,
        )
        return [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    except RagProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/ask")
def ask(payload: AskRequest) -> dict:
    try:
        answer = _rag_service().ask(
            question=payload.question,
            config=settings.session_config_for(payload.session_id),
            tenant_id=payload.tenant_id,
            permission_tag=payload.permission_tag,
        )
        refs = _vector_service().retrieve(
            payload.question,
            tenant_id=payload.tenant_id,
            permission_tag=payload.permission_tag,
        )
        citations = [
            {
                "source": doc.metadata.get("source", "unknown"),
                "tenant_id": doc.metadata.get("tenant_id", ""),
                "permission_tag": doc.metadata.get("permission_tag", ""),
            }
            for doc in refs
        ]
        return {"answer": answer, "citations": citations}
    except RagProjectError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/sessions")
def list_sessions() -> dict:
    initialize_runtime(require_api_key=False)
    return {"sessions": list_session_ids()}


@app.delete("/sessions/{session_id}")
def clear_session(session_id: str) -> dict:
    initialize_runtime(require_api_key=False)
    file_path = clear_session_history(session_id)
    return {"cleared_session": session_id, "file": str(file_path)}
