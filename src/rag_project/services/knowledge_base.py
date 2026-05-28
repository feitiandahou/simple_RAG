from datetime import datetime
import hashlib
from pathlib import Path
import uuid

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag_project.config import settings
from rag_project.errors import wrap_external_error
from rag_project.observability import get_logger


logger = get_logger(__name__)


def _dedupe_key(md5_str: str, tenant_id: str) -> str:
    return f"{tenant_id}:{md5_str}"


def check_md5(md5_str: str, tenant_id: str) -> bool:
    settings.ensure_runtime_directories()
    existing_hashes = settings.md5_path.read_text(encoding="utf-8").splitlines()
    dedupe_key = _dedupe_key(md5_str, tenant_id)
    clean_hashes = {line.strip() for line in existing_hashes if line.strip()}
    return dedupe_key in clean_hashes


def save_md5(md5_str: str, tenant_id: str) -> None:
    settings.ensure_runtime_directories()
    with settings.md5_path.open("a", encoding="utf-8") as file:
        file.write(f"{_dedupe_key(md5_str, tenant_id)}\n")


def get_string_md5(input_str: str, encoding: str = "utf-8") -> str:
    return hashlib.md5(input_str.encode(encoding=encoding)).hexdigest()


class KnowledgeBaseService:
    def __init__(self, embedding) -> None:
        settings.ensure_runtime_directories()
        self.embedding = embedding
        self.chroma = Chroma(
            collection_name=settings.collection_name,
            embedding_function=self.embedding,
            persist_directory=str(settings.persist_directory),
        )
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=settings.separators,
            length_function=len,
        )

    def upload_by_str(
        self,
        data: str,
        filename: str,
        operator: str = "user_001",
        tenant_id: str = "tenant_demo",
        owner: str = "system",
        permission_tag: str = "internal",
        version: str = "v1",
    ) -> str:
        clean_text = data.strip()
        if not clean_text:
            return f"文件 {filename} 内容为空，已跳过。"

        md5_hex = get_string_md5(data)
        if check_md5(md5_hex, tenant_id):
            return f"文件 {filename} 已经存在于知识库中，无需重复上传。"

        if len(clean_text) > settings.max_split_char_number:
            knowledge_chunks = self.splitter.split_text(clean_text)
        else:
            knowledge_chunks = [clean_text]

        metadatas = []
        updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        doc_id = f"{filename}-{uuid.uuid4().hex[:12]}"
        for idx, chunk in enumerate(knowledge_chunks):
            metadatas.append(
                {
                    "doc_id": doc_id,
                    "tenant_id": tenant_id,
                    "source": filename,
                    "version": version,
                    "owner": owner,
                    "permission_tag": permission_tag,
                    "updated_at": updated_at,
                    "operator": operator,
                    "chunk_index": idx,
                    "char_count": len(chunk),
                }
            )
        try:
            self.chroma.add_texts(knowledge_chunks, metadatas=metadatas)
        except Exception as exc:
            raise wrap_external_error(exc, "写入知识库") from exc
        save_md5(md5_hex, tenant_id)
        logger.info(
            "knowledge_uploaded",
            extra={
                "file_name": filename,
                "chunks": len(knowledge_chunks),
                "operator": operator,
                "tenant_id": tenant_id,
                "permission_tag": permission_tag,
            },
        )
        return f"文件 {filename} 已成功上传到知识库中，共分割成 {len(knowledge_chunks)} 个文本块。"

    def upload_text_file(
        self,
        file_path: Path,
        operator: str = "user_001",
        tenant_id: str = "tenant_demo",
        owner: str = "system",
        permission_tag: str = "internal",
        version: str = "v1",
    ) -> str:
        text = file_path.read_text(encoding="utf-8")
        return self.upload_by_str(
            text,
            file_path.name,
            operator=operator,
            tenant_id=tenant_id,
            owner=owner,
            permission_tag=permission_tag,
            version=version,
        )

    def ingest_directory(
        self,
        directory: Path,
        glob_pattern: str = "*.txt",
        operator: str = "user_001",
        tenant_id: str = "tenant_demo",
        owner: str = "system",
        permission_tag: str = "internal",
        version: str = "v1",
    ) -> dict:
        if not directory.exists() or not directory.is_dir():
            raise ValueError(f"目录不存在或不是目录: {directory}")

        success = 0
        skipped = 0
        failed = 0
        details: list[str] = []

        for file_path in sorted(directory.rglob(glob_pattern)):
            if not file_path.is_file():
                continue
            if file_path.resolve() == settings.md5_path.resolve() or file_path.name.startswith("."):
                skipped += 1
                details.append(f"{file_path.name}: 系统文件已跳过")
                continue
            try:
                result = self.upload_text_file(
                    file_path,
                    operator=operator,
                    tenant_id=tenant_id,
                    owner=owner,
                    permission_tag=permission_tag,
                    version=version,
                )
                details.append(f"{file_path.name}: {result}")
                if "无需重复上传" in result or "内容为空" in result:
                    skipped += 1
                else:
                    success += 1
            except UnicodeDecodeError:
                failed += 1
                details.append(f"{file_path.name}: 编码不是 UTF-8，已跳过")
            except Exception as exc:
                failed += 1
                details.append(f"{file_path.name}: 失败 - {exc}")

        return {
            "directory": str(directory),
            "pattern": glob_pattern,
            "tenant_id": tenant_id,
            "permission_tag": permission_tag,
            "success": success,
            "skipped": skipped,
            "failed": failed,
            "details": details,
        }