"""读取 Markdown 日志文件并按日期筛选段落。"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# 带完整日期的标题行，例如 "## 2026-10-10 (Sat)"。
_DATE_HEADING = re.compile(r"^#{1,6}\s+.*?(\d{4})-(\d{2})-(\d{2})", re.MULTILINE)
# --week 选项中使用的 "MM-DD" 片段。
_MD = re.compile(r"^(\d{2})-(\d{2})$")


def expand_paths(paths: list[Path]) -> list[Path]:
    """把文件、目录和 glob 模式统一展开为有序的 .md 文件列表。"""
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.is_file():
            files.append(p)
        elif not p.is_absolute():
            # 相对路径且文件不存在时，按 glob 模式处理。
            files.extend(sorted(Path().glob(str(p))))
        # 不存在的绝对路径直接匹配不到任何文件。
    # 去重并保持原有顺序。
    seen: set[Path] = set()
    out: list[Path] = []
    for f in files:
        key = f.resolve()
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def split_sections(text: str) -> list[tuple[date | None, str]]:
    """按标题中的日期把 Markdown 文件切分成若干段落。

    首个日期标题之前的文本统一归到 ``None`` 键下。
    """
    matches = list(_DATE_HEADING.finditer(text))
    if not matches:
        return [(None, text)]

    sections: list[tuple[date | None, str]] = []
    head = text[: matches[0].start()].strip()
    if head:
        sections.append((None, head))

    for i, m in enumerate(matches):
        # 段落范围为当前标题到下一个标题（或文末）。
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.start() : end].strip()
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            key: date | None = date(y, mo, d)
        except ValueError:
            # 形如 2026-13-40 这类非法日期，当作无日期段落处理。
            key = None
        sections.append((key, body))
    return sections


def _parse_md(token: str) -> tuple[int, int]:
    m = _MD.match(token.strip())
    if not m:
        raise ValueError(f"Bad date token: {token!r}. Use MM-DD, e.g. 10-05..10-11.")
    return int(m.group(1)), int(m.group(2))


def filter_week(
    sections: list[tuple[date | None, str]], week: str
) -> list[tuple[date | None, str]]:
    """保留日期落在 ``MM-DD..MM-DD`` 区间内（含端点）的段落。"""
    try:
        start_s, end_s = week.split("..")
    except ValueError:
        raise ValueError(f"Bad --week value: {week!r}. Use MM-DD..MM-DD.") from None
    sm, sd = _parse_md(start_s)
    em, ed = _parse_md(end_s)

    def in_range(d: date | None) -> bool:
        if d is None:
            return False
        return (sm, sd) <= (d.month, d.day) <= (em, ed)

    return [(d, body) for d, body in sections if in_range(d)]


def load(paths: list[Path], week: str | None = None) -> str:
    """读取给定路径并返回拼接后的 Markdown 正文。

    指定 ``week`` 时，仅保留该区间内的日期段落。
    """
    files = expand_paths(paths)
    if not files:
        raise FileNotFoundError(f"No markdown files matched: {[str(p) for p in paths]}")

    blocks: list[str] = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        if week:
            sections = filter_week(split_sections(text), week)
            parts = [body for _, body in sections]
            if not parts:
                # 该文件在本周区间内没有任何内容，跳过。
                continue
            body_text = "\n\n".join(parts)
        else:
            body_text = text
        # 用文件名注释标记每个文件的内容来源。
        blocks.append(f"<!-- {f.name} -->\n{body_text}")
    if not blocks:
        raise ValueError(f"No log content found for week {week!r}.")
    return "\n\n---\n\n".join(blocks)
