"""评判历史的本地持久化存储。

刻意不使用数据库：所有记录写在一个 JSON 文件里（默认 ~/.lifelog-coach/history.json）。
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_DIR = Path.home() / ".lifelog-coach"
HISTORY_FILE = "history.json"
# 最多保留的记录条数，超出后丢弃最旧的。
MAX_ITEMS = 200


def history_path() -> Path:
    """历史文件路径，可用环境变量 LIFELOG_HISTORY_DIR 覆盖存放目录。"""
    base = os.getenv("LIFELOG_HISTORY_DIR", "").strip()
    root = Path(base) if base else DEFAULT_DIR
    return root / HISTORY_FILE


def _read_raw() -> list[dict[str, Any]]:
    path = history_path()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # 文件损坏时当作空历史，避免整个服务起不来。
        return []
    return data if isinstance(data, list) else []


def _write_raw(items: list[dict[str, Any]]) -> None:
    path = history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # 先写临时文件再原子替换，避免写一半被中断导致文件损坏。
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".history-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def list_history() -> list[dict[str, Any]]:
    """返回全部历史记录，按时间倒序（最新在前）。"""
    items = _read_raw()
    items.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return items


def add_record(
    mode: str,
    paths: list[str],
    week: str | None,
    result: str,
    content: str,
) -> dict[str, Any]:
    """写入一条评判记录并返回它。"""
    record = {
        "id": uuid.uuid4().hex[:12],
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": mode,
        "paths": paths,
        "week": week,
        "result": result,
        "content": content,
    }
    items = _read_raw()
    items.append(record)
    # 只保留最近 MAX_ITEMS 条。
    items.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    _write_raw(items[:MAX_ITEMS])
    return record


def get_record(record_id: str) -> dict[str, Any] | None:
    for r in _read_raw():
        if r.get("id") == record_id:
            return r
    return None


def delete_record(record_id: str) -> bool:
    """删除指定记录，返回是否真的删掉了。"""
    items = _read_raw()
    kept = [r for r in items if r.get("id") != record_id]
    if len(kept) == len(items):
        return False
    _write_raw(kept)
    return True


def clear_history() -> int:
    """清空历史，返回被删除的条数。"""
    items = _read_raw()
    if items:
        _write_raw([])
    return len(items)
