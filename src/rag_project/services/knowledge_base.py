from datetime import datetime
import hashlib

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_project.config import settings
from rag_project.errors import ensure_dashscope_api_key, wrap_external_error

load_dotenv()


def check_md5(md5_str: str) -> bool:
    settings.ensure_runtime_directories()
    existing_hashes = settings.md5_path.read_text(encoding="utf-8").splitlines()
    return md5_str in {line.strip() for line in existing_hashes if line.strip()}


def save_md5(md5_str: str) -> None:
    settings.ensure_runtime_directories()
    with settings.md5_path.open("a", encoding="utf-8") as file:
        file.write(f"{md5_str}\n")


def get_string_md5(input_str: str, encoding: str = "utf-8") -> str:
    return hashlib.md5(input_str.encode(encoding=encoding)).hexdigest()


class KnowledgeBaseService:
    def __init__(self) -> None:
        settings.ensure_runtime_directories()
        ensure_dashscope_api_key(__import__("os").environ.get("DASHSCOPE_API_KEY"))
        self.chroma = Chroma(
            collection_name=settings.collection_name,
            embedding_function=DashScopeEmbeddings(model=settings.embedding_model_name),
            persist_directory=str(settings.persist_directory),
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=settings.separators,
            length_function=len,
        )

    def upload_by_str(self, data: str, filename: str, operator: str = "user_001") -> str:
        md5_hex = get_string_md5(data)
        if check_md5(md5_hex):
            return f"文件 {filename} 已经存在于知识库中，无需重复上传。"

        if len(data) > settings.max_split_char_number:
            knowledge_chunks = self.splitter.split_text(data)
        else:
            knowledge_chunks = [data]

        metadata = {
            "source": filename,
            "create_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator": operator,
        }
        try:
            self.chroma.add_texts(knowledge_chunks, metadatas=[metadata for _ in knowledge_chunks])
        except Exception as exc:
            raise wrap_external_error(exc, "写入知识库") from exc
        save_md5(md5_hex)
        return f"文件 {filename} 已成功上传到知识库中，共分割成 {len(knowledge_chunks)} 个文本块。"