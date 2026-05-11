from dotenv import load_dotenv
from langchain_chroma import Chroma

from rag_project.config import settings
from rag_project.errors import ensure_dashscope_api_key, wrap_external_error

load_dotenv()


class VectorStoreService:
    def __init__(self, embedding) -> None:
        ensure_dashscope_api_key(__import__("os").environ.get("DASHSCOPE_API_KEY"))
        self.embedding = embedding
        self.vector_store = Chroma(
            collection_name=settings.collection_name,
            embedding_function=self.embedding,
            persist_directory=str(settings.persist_directory),
        )

    def get_retriever(self):
        return self.vector_store.as_retriever()

    def retrieve(self, query: str):
        try:
            return self.get_retriever().invoke(query)
        except Exception as exc:
            raise wrap_external_error(exc, "执行向量检索") from exc