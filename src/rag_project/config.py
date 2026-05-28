import os
from pathlib import Path

from langchain_core.runnables import RunnableConfig


def _get_env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        return default


class Settings:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[2]

        data_dir_name = os.environ.get("RAG_DATA_DIR", "data")
        self.data_dir = self.project_root / data_dir_name
        self.md5_path = self.data_dir / "md5.txt"
        self.persist_directory = self.data_dir / "chroma_db"
        self.chat_history_dir = self.data_dir / "chat_history"

        self.app_name = os.environ.get("RAG_APP_NAME", "rag-project")
        self.app_env = os.environ.get("RAG_ENV", "dev")
        self.log_level = os.environ.get("RAG_LOG_LEVEL", "INFO").upper()

        self.collection_name = os.environ.get("RAG_COLLECTION_NAME", "rag")
        self.chunk_size = _get_env_int("RAG_CHUNK_SIZE", 1000)
        self.chunk_overlap = _get_env_int("RAG_CHUNK_OVERLAP", 100)
        self.separators = ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]
        self.max_split_char_number = _get_env_int("RAG_MAX_SPLIT_CHAR_NUMBER", 1000)

        self.top_k = _get_env_int("RAG_TOP_K", 4)
        self.embedding_model_name = os.environ.get("RAG_EMBEDDING_MODEL", "text-embedding-v4")
        self.chat_model_name = os.environ.get("RAG_CHAT_MODEL", "qwen-turbo")
        self.prompt_version = os.environ.get("RAG_PROMPT_VERSION", "v2_enterprise_demo")
        self.default_session_id = os.environ.get("RAG_DEFAULT_SESSION_ID", "user_001")

    @property
    def session_config(self) -> RunnableConfig:
        return self.session_config_for(self.default_session_id)

    def session_config_for(self, session_id: str) -> RunnableConfig:
        return {"configurable": {"session_id": session_id}}

    def ensure_runtime_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.chat_history_dir.mkdir(parents=True, exist_ok=True)
        self.md5_path.touch(exist_ok=True)

    def system_summary(self) -> dict[str, str | int]:
        return {
            "app_name": self.app_name,
            "app_env": self.app_env,
            "collection_name": self.collection_name,
            "embedding_model": self.embedding_model_name,
            "chat_model": self.chat_model_name,
            "prompt_version": self.prompt_version,
            "top_k": self.top_k,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
            "data_dir": str(self.data_dir),
            "persist_directory": str(self.persist_directory),
            "chat_history_dir": str(self.chat_history_dir),
        }


settings = Settings()