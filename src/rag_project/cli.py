import argparse
import json
from pathlib import Path
import shutil
import sys
import uvicorn

from langchain_core.runnables import RunnableConfig

from rag_project.bootstrap import (
    build_knowledge_base_service,
    build_rag_service,
    build_vector_store_service,
    initialize_runtime,
)
from rag_project.config import settings
from rag_project.errors import RagProjectError
from rag_project.stores.file_history import clear_session_history, list_session_ids


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG project command line entry")
    subparsers = parser.add_subparsers(dest="command", required=True)

    upload_parser = subparsers.add_parser("upload-demo", help="write a demo text into vector store")
    upload_parser.add_argument("--text", default="这是一个测试文本。")
    upload_parser.add_argument("--filename", default="test.txt")
    upload_parser.add_argument("--operator", default="user_001")
    upload_parser.add_argument("--tenant-id", default="tenant_demo")
    upload_parser.add_argument("--owner", default="system")
    upload_parser.add_argument("--permission-tag", default="internal")
    upload_parser.add_argument("--version", default="v1")

    ingest_parser = subparsers.add_parser("ingest-dir", help="ingest all txt files from a directory")
    ingest_parser.add_argument("directory")
    ingest_parser.add_argument("--pattern", default="*.txt")
    ingest_parser.add_argument("--operator", default="user_001")
    ingest_parser.add_argument("--tenant-id", default="tenant_demo")
    ingest_parser.add_argument("--owner", default="system")
    ingest_parser.add_argument("--permission-tag", default="internal")
    ingest_parser.add_argument("--version", default="v1")

    retrieve_parser = subparsers.add_parser("retrieve", help="retrieve relevant documents")
    retrieve_parser.add_argument("query", nargs="?", default="什么是RAG？")
    retrieve_parser.add_argument("--json", action="store_true", dest="as_json")
    retrieve_parser.add_argument("--tenant-id")
    retrieve_parser.add_argument("--permission-tag")

    ask_parser = subparsers.add_parser("ask", help="run end-to-end rag answer")
    ask_parser.add_argument("question", nargs="?", default="什么是RAG？")
    ask_parser.add_argument("--session-id", default=settings.default_session_id)
    ask_parser.add_argument("--tenant-id")
    ask_parser.add_argument("--permission-tag")

    clear_parser = subparsers.add_parser("clear-history", help="clear local history for one session")
    clear_parser.add_argument("--session-id", default=settings.default_session_id)

    subparsers.add_parser("list-sessions", help="list local conversation sessions")
    subparsers.add_parser("kb-stats", help="show knowledge base statistics")
    subparsers.add_parser("kb-clean-system", help="clean known internal/system documents")

    reset_parser = subparsers.add_parser("kb-reset", help="reset local knowledge base storage")
    reset_parser.add_argument("--force", action="store_true", help="confirm destructive reset")

    subparsers.add_parser("system-info", help="print effective runtime config")
    subparsers.add_parser("health-check", help="run lightweight system health checks")

    api_parser = subparsers.add_parser("serve-api", help="run FastAPI service")
    api_parser.add_argument("--host", default="127.0.0.1")
    api_parser.add_argument("--port", type=int, default=8000)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "system-info":
            initialize_runtime(require_api_key=False)
            print(json.dumps(settings.system_summary(), ensure_ascii=False, indent=2))
            return

        if args.command == "health-check":
            initialize_runtime(require_api_key=False)
            report = {
                "runtime_dirs_ready": settings.data_dir.exists()
                and settings.persist_directory.exists()
                and settings.chat_history_dir.exists(),
                "md5_file_ready": settings.md5_path.exists(),
                "api_key_configured": bool(__import__("os").environ.get("DASHSCOPE_API_KEY")),
            }
            print(json.dumps(report, ensure_ascii=False, indent=2))
            if not all(report.values()):
                raise SystemExit(1)
            return

        if args.command == "serve-api":
            initialize_runtime(require_api_key=False)
            uvicorn.run("rag_project.api.app:app", host=args.host, port=args.port, reload=False)
            return

        if args.command == "list-sessions":
            initialize_runtime(require_api_key=False)
            print(json.dumps({"sessions": list_session_ids()}, ensure_ascii=False, indent=2))
            return

        if args.command == "clear-history":
            initialize_runtime(require_api_key=False)
            file_path = clear_session_history(args.session_id)
            print(json.dumps({"cleared_session": args.session_id, "file": str(file_path)}, ensure_ascii=False, indent=2))
            return

        if args.command == "kb-reset":
            initialize_runtime(require_api_key=False)
            if not args.force:
                print("kb-reset 是破坏性操作，请添加 --force 确认执行。", file=sys.stderr)
                raise SystemExit(2)

            if settings.persist_directory.exists():
                shutil.rmtree(settings.persist_directory)
            settings.persist_directory.mkdir(parents=True, exist_ok=True)
            settings.md5_path.write_text("", encoding="utf-8")
            print(
                json.dumps(
                    {
                        "reset": True,
                        "persist_directory": str(settings.persist_directory),
                        "md5_path": str(settings.md5_path),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        initialize_runtime(require_api_key=True)

        if args.command == "upload-demo":
            service = build_knowledge_base_service()
            print(
                service.upload_by_str(
                    args.text,
                    args.filename,
                    operator=args.operator,
                    tenant_id=args.tenant_id,
                    owner=args.owner,
                    permission_tag=args.permission_tag,
                    version=args.version,
                )
            )
            return

        if args.command == "ingest-dir":
            service = build_knowledge_base_service()
            directory = Path(args.directory)
            report = service.ingest_directory(
                directory=directory,
                glob_pattern=args.pattern,
                operator=args.operator,
                tenant_id=args.tenant_id,
                owner=args.owner,
                permission_tag=args.permission_tag,
                version=args.version,
            )
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return

        if args.command == "retrieve":
            service = build_vector_store_service()
            docs = service.retrieve(
                args.query,
                tenant_id=args.tenant_id,
                permission_tag=args.permission_tag,
            )
            if args.as_json:
                payload = [
                    {
                        "page_content": doc.page_content,
                        "metadata": doc.metadata,
                    }
                    for doc in docs
                ]
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            else:
                print(docs)
            return

        if args.command == "kb-stats":
            service = build_vector_store_service()
            print(json.dumps(service.stats(), ensure_ascii=False, indent=2))
            return

        if args.command == "kb-clean-system":
            service = build_vector_store_service()
            report = service.delete_by_source("md5.txt")
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return

        if args.command == "ask":
            session_config: RunnableConfig = {"configurable": {"session_id": args.session_id}}
            print(
                build_rag_service().ask(
                    args.question,
                    session_config,
                    tenant_id=args.tenant_id,
                    permission_tag=args.permission_tag,
                )
            )
            return

        parser.error("Unknown command")
    except RagProjectError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        raise SystemExit(1) from exc