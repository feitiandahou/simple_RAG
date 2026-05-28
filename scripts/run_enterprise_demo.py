from pathlib import Path
import argparse
import subprocess
import sys


def run_step(cmd: list[str]) -> None:
    print(f"\n>>> {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run enterprise-style RAG demo workflow")
    parser.add_argument("--knowledge-dir", default="docs", help="Directory for batch ingestion")
    parser.add_argument("--query", default="企业级RAG的关键能力有哪些？", help="Verification query")
    parser.add_argument("--tenant-id", default="tenant_demo", help="Tenant scope for demo run")
    parser.add_argument("--permission-tag", default="internal", help="Permission tag for demo run")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    knowledge_dir = (project_root / args.knowledge_dir).resolve()

    run_step([sys.executable, "-m", "rag_project", "system-info"])
    run_step([sys.executable, "-m", "rag_project", "health-check"])
    run_step([
        sys.executable,
        "-m",
        "rag_project",
        "ingest-dir",
        str(knowledge_dir),
        "--pattern",
        "*.txt",
        "--operator",
        "demo_ops",
        "--tenant-id",
        args.tenant_id,
        "--owner",
        "demo_owner",
        "--permission-tag",
        args.permission_tag,
        "--version",
        "v1",
    ])
    run_step([sys.executable, "-m", "rag_project", "kb-stats"])
    run_step(
        [
            sys.executable,
            "-m",
            "rag_project",
            "retrieve",
            args.query,
            "--json",
            "--tenant-id",
            args.tenant_id,
            "--permission-tag",
            args.permission_tag,
        ]
    )


if __name__ == "__main__":
    main()
