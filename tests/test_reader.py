from datetime import date

import pytest

from lifelog_coach import reader

# 测试样本：包含前言、两个日期段落和一个区间外段落。
SAMPLE = """# 2026-10 Logs

preamble text

## 2026-10-10 (Sat)

### body
protein 57g

## 2026-10-11 (Sun)

protein 114g

## 2026-10-16 (Fri)

empty
"""


def test_split_sections_dates():
    secs = reader.split_sections(SAMPLE)
    dated = [d for d, _ in secs if d]
    assert dated == [date(2026, 10, 10), date(2026, 10, 11), date(2026, 10, 16)]


def test_split_keeps_preamble():
    secs = reader.split_sections(SAMPLE)
    assert secs[0][0] is None
    assert "preamble" in secs[0][1]


def test_filter_week():
    secs = reader.split_sections(SAMPLE)
    kept = reader.filter_week(secs, "10-05..10-11")
    assert [d for d, _ in kept] == [date(2026, 10, 10), date(2026, 10, 11)]


def test_filter_week_single_day():
    secs = reader.split_sections(SAMPLE)
    kept = reader.filter_week(secs, "10-16..10-16")
    assert [d for d, _ in kept] == [date(2026, 10, 16)]


def test_filter_week_bad_token():
    with pytest.raises(ValueError):
        reader.filter_week(reader.split_sections(SAMPLE), "10-05")


def test_load_week(tmp_path):
    f = tmp_path / "2026-10.md"
    f.write_text(SAMPLE, encoding="utf-8")
    out = reader.load([f], week="10-05..10-11")
    assert "protein 57g" in out
    assert "protein 114g" in out
    assert "empty" not in out


def test_load_no_week(tmp_path):
    f = tmp_path / "2026-10.md"
    f.write_text(SAMPLE, encoding="utf-8")
    out = reader.load([f])
    assert "preamble" in out
    assert "empty" in out


def test_load_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        reader.load([tmp_path / "nope.md"])


def test_expand_dir_filters_md(tmp_path):
    (tmp_path / "a.md").write_text("x", encoding="utf-8")
    (tmp_path / "b.txt").write_text("y", encoding="utf-8")
    files = reader.expand_paths([tmp_path])
    assert [f.name for f in files] == ["a.md"]
