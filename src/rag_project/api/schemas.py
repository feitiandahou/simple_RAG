from pydantic import BaseModel, Field


class UploadRequest(BaseModel):
    text: str
    filename: str = "uploaded.txt"
    operator: str = "user_001"
    tenant_id: str = "tenant_demo"
    owner: str = "system"
    permission_tag: str = "internal"
    version: str = "v1"


class IngestDirectoryRequest(BaseModel):
    directory: str
    pattern: str = "*.txt"
    operator: str = "user_001"
    tenant_id: str = "tenant_demo"
    owner: str = "system"
    permission_tag: str = "internal"
    version: str = "v1"


class RetrieveRequest(BaseModel):
    query: str
    tenant_id: str | None = None
    permission_tag: str | None = None


class AskRequest(BaseModel):
    question: str
    session_id: str = "user_001"
    tenant_id: str | None = None
    permission_tag: str | None = None


class ClearSessionRequest(BaseModel):
    session_id: str = Field(default="user_001", min_length=1)
