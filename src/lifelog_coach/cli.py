"""命令行入口：`lifelog judge` 与 `lifelog review`。"""

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
    """输出结果：未指定 -o 时打印到 stdout，否则写入文件。"""
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
    """评判单日日志（或一组文件）。"""
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
    """总结一周日志。"""
    content = reader.load(paths, week=week)
    text = LLM(Settings.from_env()).complete(
        prompts.REVIEW_SYSTEM, prompts.build_review_prompt(content)
    )
    _emit(text, out)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="Bind address."),
    port: int = typer.Option(8777, "--port", "-p", help="Listen port."),
    reload: bool = typer.Option(False, "--reload", help="Reload on code changes."),
) -> None:
    """启动本地 Web 界面（Vue 前端 + API 服务）。"""
    from .server import serve as _serve

    typer.echo(f"Web UI: http://{host}:{port}")
    _serve(host=host, port=port, reload=reload)


if __name__ == "__main__":
    app()
