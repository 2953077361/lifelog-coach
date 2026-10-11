"""judge / review 两个命令的 prompt 模板。

保持简短可调：这是整个产品的“大脑”。
"""

from __future__ import annotations

JUDGE_SYSTEM = (
    "You are a strict, rational, data-driven chief life officer. "
    "Read the user's markdown life log and reply in markdown only. "
    "Point out broken targets (red lines) plainly. No motivational fluff."
)

JUDGE_TEMPLATE = """This is my log material:

{content}

Judge: (1) the trend, (2) any red line broken (targets missed), \
(3) the single most important thing to do tomorrow.
Reply in markdown only. Be concise, direct, and cite the numbers."""

# 周复盘复用同一套人设，只是结论粒度不同。
REVIEW_SYSTEM = JUDGE_SYSTEM

REVIEW_TEMPLATE = """This is my log material for the week:

{content}

Judge: (1) the week's trend, (2) the biggest problem, (3) three actions for next week.
Reply in markdown only."""


def build_judge_prompt(content: str) -> str:
    """用日志正文渲染单日评判的 user prompt。"""
    return JUDGE_TEMPLATE.format(content=content)


def build_review_prompt(content: str) -> str:
    """用日志正文渲染周复盘的 user prompt。"""
    return REVIEW_TEMPLATE.format(content=content)
