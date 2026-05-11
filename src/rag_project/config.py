from pathlib import Path

from langchain_core.runnables import RunnableConfig


class Settings:
    def __init__(self) -> None:
        self.project_root = Path(__file__).resolve().parents[2]
        self.data_dir = self.project_root / "data"
        self.md5_path = self.data_dir / "md5.txt"
        self.persist_directory = self.data_dir / "chroma_db"
        self.chat_history_dir = self.data_dir / "chat_history"

        self.collection_name = "rag"
        self.chunk_size = 1000
        self.chunk_overlap = 100
        self.separators = ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]
        self.max_split_char_number = 1000

        self.similarity_threshold = 1
        self.embedding_model_name = "text-embedding-v4"
        self.chat_model_name = "qwen-turbo"
        self.default_session_id = "user_001"

    @property
    def session_config(self) -> RunnableConfig:
        return {"configurable": {"session_id": self.default_session_id}}

    def ensure_runtime_directories(self) -> None:
        self.data_dir.mkdir(exist_ok=True)
        self.persist_directory.mkdir(exist_ok=True)
        self.chat_history_dir.mkdir(exist_ok=True)
        self.md5_path.touch(exist_ok=True)


settings = Settings()