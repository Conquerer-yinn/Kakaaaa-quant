"""存储层：追加写入与按关键列去重。"""
import pandas as pd
import pytest

import storage.excel_helper as excel_helper
from storage.excel_helper import ExcelHelper


@pytest.fixture
def base_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(excel_helper, "MASTER_DATA_DIR", str(tmp_path / "master"))
    monkeypatch.setattr(excel_helper, "BACKUP_DIR", str(tmp_path / "backups"))
    return str(tmp_path / "master")


def test_append_then_dedupe_keeps_last(base_dir):
    first = pd.DataFrame({"日期": ["20260101", "20260102"], "值": [1, 2]})
    ExcelHelper.append_rows(first, "t.xlsx", dedupe_subset=["日期"], base_dir=base_dir)

    second = pd.DataFrame({"日期": ["20260102", "20260103"], "值": [20, 3]})
    path = ExcelHelper.append_rows(second, "t.xlsx", dedupe_subset=["日期"], base_dir=base_dir)

    result = pd.read_excel(path)
    assert result["日期"].astype(str).tolist() == ["20260101", "20260102", "20260103"]
    assert result.loc[result["日期"].astype(str) == "20260102", "值"].item() == 20


def test_append_normalizes_date_column(base_dir):
    df = pd.DataFrame({"日期": ["2026-01-05"], "值": [1]})
    path = ExcelHelper.append_rows(df, "d.xlsx", base_dir=base_dir)

    result = pd.read_excel(path)
    assert str(result.loc[0, "日期"]) == "20260105"


def test_append_empty_raises(base_dir):
    with pytest.raises(ValueError):
        ExcelHelper.append_rows(pd.DataFrame(), "t.xlsx", base_dir=base_dir)
