"""Command line interface: `lifelog judge` and `lifelog review`."""

from __future__ import annotations

from pathlib import Path

import typer

from . import prompts, reader
from .config import Settings
from .llm import LLM

app = typer.Typer(
    help="Read markdown life logs; let AI judge trends, red lines, and next steps.",
    no_args_is_help=True,
    add_completion=False,
)


def _emit(text: str, out: Path | None) -> None:
    if out is None:
        typer.echo(text)
    else:
        out.write_text(text + "\n", encoding="utf-8")
        typer.echo(f"Wrote {out}")


@app.command()
def judge(
    paths: list[Path] = typer.Argument(..., help="Markdown log files or directories."),
    out: Path | None = typer.Option(None, "--out", "-o", help="Write output to a file."),
) -> None:
    """Judge a single day (or a set of files)."""
    content = reader.load(paths)
    text = LLM(Settings.from_env()).complete(
        prompts.JUDGE_SYSTEM, prompts.build_judge_prompt(content)
    )
    _emit(text, out)


@app.command()
def review(
    paths: list[Path] = typer.Argument(..., help="Markdown log files or directories."),
    week: str | None = typer.Option(None, "--week", help="Date range MM-DD..MM-DD."),
    out: Path | None = typer.Option(None, "--out", "-o", help="Write output to a file."),
) -> None:
    """Summarize a week."""
    content = reader.load(paths, week=week)
    text = LLM(Settings.from_env()).complete(
        prompts.REVIEW_SYSTEM, prompts.build_review_prompt(content)
    )
    _emit(text, out)


if __name__ == "__main__":
    app()
