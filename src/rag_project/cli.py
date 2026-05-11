import argparse
import sys

from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.runnables import RunnableConfig

from rag_project.config import settings
from rag_project.errors import RagProjectError
from rag_project.services.knowledge_base import KnowledgeBaseService
from rag_project.services.rag_service import RagService
from rag_project.services.vector_store import VectorStoreService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG project command line entry")
    subparsers = parser.add_subparsers(dest="command", required=True)

    upload_parser = subparsers.add_parser("upload-demo", help="write a demo text into vector store")
    upload_parser.add_argument("--text", default="这是一个测试文本。")
    upload_parser.add_argument("--filename", default="test.txt")

    retrieve_parser = subparsers.add_parser("retrieve", help="retrieve relevant documents")
    retrieve_parser.add_argument("query", nargs="?", default="什么是RAG？")

    ask_parser = subparsers.add_parser("ask", help="run end-to-end rag answer")
    ask_parser.add_argument("question", nargs="?", default="什么是RAG？")
    ask_parser.add_argument("--session-id", default=settings.default_session_id)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "upload-demo":
            service = KnowledgeBaseService()
            print(service.upload_by_str(args.text, args.filename))
            return

        if args.command == "retrieve":
            service = VectorStoreService(DashScopeEmbeddings(model=settings.embedding_model_name))
            print(service.retrieve(args.query))
            return

        if args.command == "ask":
            session_config: RunnableConfig = {"configurable": {"session_id": args.session_id}}
            print(RagService().ask(args.question, session_config))
            return

        parser.error("Unknown command")
    except RagProjectError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc