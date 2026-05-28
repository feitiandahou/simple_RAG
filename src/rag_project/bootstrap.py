import os

from dotenv import load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings

from rag_project.config import settings
from rag_project.errors import ensure_dashscope_api_key
from rag_project.observability import configure_logging, get_logger
from rag_project.services.knowledge_base import KnowledgeBaseService
from rag_project.services.rag_service import RagService
from rag_project.services.vector_store import VectorStoreService


load_dotenv()
logger = get_logger(__name__)


def initialize_runtime(require_api_key: bool = True) -> None:
    configure_logging()
    settings.ensure_runtime_directories()
    if require_api_key:
        ensure_dashscope_api_key(os.environ.get("DASHSCOPE_API_KEY"))
    logger.info("runtime_initialized", extra={"env": settings.app_env, "app": settings.app_name})


def build_embedding_client() -> DashScopeEmbeddings:
    return DashScopeEmbeddings(model=settings.embedding_model_name)


def build_chat_client() -> ChatTongyi:
    return ChatTongyi(model=settings.chat_model_name)  # type: ignore[call-arg]


def build_vector_store_service() -> VectorStoreService:
    return VectorStoreService(embedding=build_embedding_client())


def build_knowledge_base_service() -> KnowledgeBaseService:
    return KnowledgeBaseService(embedding=build_embedding_client())


def build_rag_service() -> RagService:
    return RagService(
        vector_service=build_vector_store_service(),
        chat_model=build_chat_client(),
    )
