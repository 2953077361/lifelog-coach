#!/usr/bin/env python3
"""一键启动 lifelog-coach。

用法：

    python run.py

脚本会自动完成：创建虚拟环境 -> 安装 Python 依赖 -> npm install -> 构建前端 -> 启动服务。
后续再启动只需再跑一次同一条命令，已就绪的步骤会自动跳过。
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
WEB = ROOT / "web"
DIST = WEB / "dist"
VENV = ROOT / ".venv"

# 这些包缺一不可，用于判断是否需要安装。
REQUIRED_IMPORTS = ["openai", "dotenv", "typer", "fastapi", "uvicorn"]

MIN_PYTHON = (3, 10)


def step(msg: str) -> None:
    print(f"\n▶ {msg}", flush=True)


def detail(msg: str) -> None:
    print(f"   {msg}", flush=True)


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """执行命令并把输出实时打到终端（Installation / build 过程需要可见）。"""
    return subprocess.run(cmd, cwd=str(cwd or ROOT), check=False)


def python_bin(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def in_virtualenv() -> bool:
    return sys.prefix != sys.base_prefix


def has_tool(name: str) -> bool:
    from shutil import which

    return which(name) is not None


def check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        raise SystemExit(
            f"需要 Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+，当前是 "
            f"{sys.version_info.major}.{sys.version_info.minor}。"
        )


def ensure_venv_and_reexec(args: list[str]) -> None:
    """不在虚拟环境里时，先建好 .venv 再用里面的解释器重跑本脚本。"""
    if not VENV.exists():
        step("创建虚拟环境 .venv")
        if has_tool("uv"):
            created = run(["uv", "venv", "--python", "3.13", str(VENV)]).returncode == 0
            if not created:
                detail("uv 创建失败，回落到标准库 venv")
                created = run([sys.executable, "-m", "venv", str(VENV)]).returncode == 0
        else:
            created = run([sys.executable, "-m", "venv", str(VENV)]).returncode == 0
        if not created:
            raise SystemExit("无法创建虚拟环境，请手动执行 python -m venv .venv 后重试。")

    py = python_bin(VENV)
    if not py.exists():
        raise SystemExit(f"虚拟环境异常：找不到 {py}")

    step("切换到虚拟环境内的解释器")
    detail(str(py))
    sys.exit(run([str(py), str(Path(__file__).resolve()), *args]).returncode)


def missing_deps() -> list[str]:
    return [mod for mod in REQUIRED_IMPORTS if not _importable(mod)]


def _importable(mod: str) -> bool:
    import importlib.util

    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def ensure_python_deps() -> None:
    missing = missing_deps()
    if not missing:
        detail("Python 依赖已就绪")
        return

    step(f"安装 Python 依赖（缺少：{', '.join(missing)}）")
    pip_cmd = [sys.executable, "-m", "pip", "install", "-e", "."]
    if run(pip_cmd).returncode == 0 and not missing_deps():
        return

    # pip 可能因环境受限失败（例如受管制的系统 Python），再试 uv。
    if has_tool("uv"):
        detail("pip 未成功，改用 uv 安装")
        if run(["uv", "pip", "install", "--python", sys.executable, "-e", "."]).returncode == 0:
            return

    raise SystemExit(
        "依赖安装失败。可手动执行：pip install -e .（或 uv pip install -e .）后再运行 python run.py"
    )


def ensure_node() -> None:
    if not has_tool("node") or not has_tool("npm"):
        raise SystemExit(
            "未检测到 Node/npm。前端需要 Node 18+，请安装后重试：https://nodejs.org\n"
            "只想用命令行的话可执行：lifelog judge <日志文件>"
        )


def ensure_npm_install() -> None:
    """node_modules 不存在，或 package.json 比它更新时才安装。"""
    mod_dir = ROOT / "node_modules"
    stamp = mod_dir / ".package-lock.json"
    pkg = ROOT / "package.json"
    if mod_dir.is_dir() and stamp.exists() and stamp.stat().st_mtime >= pkg.stat().st_mtime:
        detail("前端依赖已就绪")
        return

    step("安装前端依赖 npm install")
    if run(["npm", "install"]).returncode != 0:
        raise SystemExit("npm install 失败，请查看上方输出。")


def build_needed() -> bool:
    """dist 缺失，或任一前端源文件新于 dist 时才重新构建。"""
    if not DIST.is_dir():
        return True
    dist_files = [p for p in DIST.rglob("*") if p.is_file()]
    if not dist_files:
        return True
    dist_mtime = max(p.stat().st_mtime for p in dist_files)

    sources: Iterable[Path] = [
        WEB / "index.html",
        WEB / "vite.config.js",
        * (WEB / "src").rglob("*"),
    ]
    src_mtime = max((p.stat().st_mtime for p in sources if p.is_file()), default=0.0)
    return src_mtime > dist_mtime


def ensure_frontend(force: bool) -> None:
    if not force and not build_needed():
        detail("前端产物已是最新")
        return

    step("构建前端 npm run build")
    if run(["npm", "run", "build"]).returncode != 0:
        raise SystemExit("前端构建失败，请查看上方输出。")


def start_server(host: str, port: int, reload: bool, open_browser: bool) -> None:
    import uvicorn

    sys.path.insert(0, str(SRC))
    from lifelog_coach.server import app  # noqa: E402 - 路径注入后才能导入

    url = f"http://{host}:{port}"
    step(f"启动服务 {url}")
    if open_browser:
        # 等服务起来再打开，避免用户看到连接被拒绝的页面。
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    detail("Ctrl+C 停止服务")

    try:
        if reload:
            uvicorn.run("lifelog_coach.server:app", host=host, port=port, reload=True)
        else:
            uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        print("\n已停止。")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="一键启动 lifelog-coach 本地 Web 界面")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址，默认 127.0.0.1")
    parser.add_argument("--port", "-p", type=int, default=8777, help="端口，默认 8777")
    parser.add_argument("--rebuild", action="store_true", help="强制重新构建前端")
    parser.add_argument("--reload", action="store_true", help="代码变更时自动重启后端")
    parser.add_argument("--no-open", action="store_true", help="不自动打开浏览器")
    parser.add_argument("--no-venv", action="store_true", help="直接使用当前 Python，不切虚拟环境")
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args(sys.argv[1:])
    check_python_version()

    print("lifelog-coach · 本地启动")

    # 首次运行时把自己切换到 .venv 里执行，避免污染系统 Python。
    if not args.no_venv and not in_virtualenv():
        ensure_venv_and_reexec(sys.argv[1:])

    ensure_python_deps()

    # 缺 .env 时提示，但不阻断启动（界面上也会红字提示）。
    if not (ROOT / ".env").exists():
        step("提示：未找到 .env")
        detail("请执行 cp .env.example .env 并填入 OPENAI_API_KEY，否则无法调用 AI。")

    ensure_node()
    ensure_npm_install()
    ensure_frontend(force=args.rebuild)
    start_server(args.host, args.port, args.reload, open_browser=not args.no_open)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已取消。", flush=True)
        time.sleep(0)
