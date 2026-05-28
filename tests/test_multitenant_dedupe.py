from pathlib import Path

from rag_project.services.knowledge_base import check_md5, get_string_md5, save_md5


def test_dedupe_is_tenant_scoped(monkeypatch, tmp_path: Path) -> None:
    md5_file = tmp_path / "md5.txt"
    md5_file.write_text("", encoding="utf-8")

    from rag_project import config as config_module

    monkeypatch.setattr(config_module.settings, "md5_path", md5_file)
    monkeypatch.setattr(config_module.settings, "ensure_runtime_directories", lambda: None)

    digest = get_string_md5("same text")
    save_md5(digest, "tenant_a")

    assert check_md5(digest, "tenant_a") is True
    assert check_md5(digest, "tenant_b") is False
