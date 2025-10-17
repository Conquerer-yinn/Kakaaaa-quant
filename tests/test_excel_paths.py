"""存储层：路径规则与写前备份。"""
import os

import storage.excel_helper as excel_helper
from storage.excel_helper import ExcelHelper


def _patch_dirs(monkeypatch, tmp_path):
    monkeypatch.setattr(excel_helper, "MASTER_DATA_DIR", str(tmp_path / "master"))
    monkeypatch.setattr(excel_helper, "BACKUP_DIR", str(tmp_path / "backups"))


def test_build_storage_path_creates_dirs(tmp_path, monkeypatch):
    _patch_dirs(monkeypatch, tmp_path)
    path = ExcelHelper.build_master_path("a.xlsx")

    assert path == os.path.join(str(tmp_path / "master"), "a.xlsx")
    assert (tmp_path / "master").exists()
    assert (tmp_path / "backups").exists()


def test_backup_file_roundtrip(tmp_path, monkeypatch):
    _patch_dirs(monkeypatch, tmp_path)
    source = tmp_path / "master" / "data.xlsx"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"excel-bytes")

    backup_path = ExcelHelper.backup_file(str(source))

    assert backup_path is not None
    assert os.path.exists(backup_path)
    assert os.path.basename(backup_path).endswith("_data.xlsx")
    assert os.path.dirname(backup_path) == str(tmp_path / "backups")


def test_backup_missing_file_returns_none(tmp_path, monkeypatch):
    _patch_dirs(monkeypatch, tmp_path)
    assert ExcelHelper.backup_file(str(tmp_path / "nope.xlsx")) is None
