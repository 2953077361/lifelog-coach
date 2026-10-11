"""Read markdown log files and select date sections."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

# A section heading that carries a full date, e.g. "## 2026-10-10 (Sat)".
_DATE_HEADING = re.compile(r"^#{1,6}\s+.*?(\d{4})-(\d{2})-(\d{2})", re.MULTILINE)
# A "MM-DD" token used in the --week option.
_MD = re.compile(r"^(\d{2})-(\d{2})$")


def expand_paths(paths: list[Path]) -> list[Path]:
    """Turn files, dirs, and globs into a sorted list of .md files."""
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
        elif p.is_file():
            files.append(p)
        elif not p.is_absolute():
            # Treat a relative non-existing path as a glob pattern.
            files.extend(sorted(Path().glob(str(p))))
        # Absolute paths that do not exist simply match nothing.
    # De-duplicate while keeping order.
    seen: set[Path] = set()
    out: list[Path] = []
    for f in files:
        key = f.resolve()
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def split_sections(text: str) -> list[tuple[date | None, str]]:
    """Split a markdown file into sections keyed by the date in each heading.

    Text before the first dated heading is kept under a ``None`` key.
    """
    matches = list(_DATE_HEADING.finditer(text))
    if not matches:
        return [(None, text)]

    sections: list[tuple[date | None, str]] = []
    head = text[: matches[0].start()].strip()
    if head:
        sections.append((None, head))

    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.start() : end].strip()
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            key: date | None = date(y, mo, d)
        except ValueError:
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
    """Keep sections whose date falls within a ``MM-DD..MM-DD`` range (inclusive)."""
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
    """Read the given paths and return concatenated markdown content.

    When ``week`` is given, only dated sections inside the range are kept.
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
                continue
            body_text = "\n\n".join(parts)
        else:
            body_text = text
        blocks.append(f"<!-- {f.name} -->\n{body_text}")
    if not blocks:
        raise ValueError(f"No log content found for week {week!r}.")
    return "\n\n---\n\n".join(blocks)
