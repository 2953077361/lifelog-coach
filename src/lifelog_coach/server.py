"""本地 Web 服务：向前端暴露 REST API，并在构建完成后托管 Vue 的静态资源。

只监听 127.0.0.1，纯本地使用。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import history as history_mod
from . import prompts, reader
from .config import Settings
from .llm import LLM

# web/dist 目录：src/lifelog_coach/server.py -> 上溯三级即项目根。
DIST_DIR = Path(__file__).resolve().parents[2] / "web" / "dist"


# 请求模型必须定义在模块级：FastAPI 解析注解时只看模块全局命名空间，
# 写在 create_app() 内部会导致注解无法解析，参数被误判为 query。
class RunRequest(BaseModel):
    mode: str = Field(default="judge", pattern="^(judge|review)$")
    paths: list[str]
    week: str | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="lifelog-coach", version="0.1.0")

    # 开发模式下 Vite dev server（5173）需要跨域访问本机 API。
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/status")
    def status() -> dict[str, Any]:
        """返回当前 LLM 配置摘要（不含密钥原文）。"""
        try:
            s = Settings.from_env()
            configured = bool(s.api_key)
        except RuntimeError:
            # 缺少 key 时不应让状态接口报错，前端据此提示用户去配置。
            s, configured = None, False
        return {
            "configured": configured,
            "base_url": s.base_url if s else "",
            "model": s.model if s else "",
            "history_path": str(history_mod.history_path()),
            "dist_ready": DIST_DIR.is_dir(),
        }

    @app.get("/api/browse")
    def browse(path: str | None = None) -> dict[str, Any]:
        """列出目录内容：子目录 + .md 文件，供前端文件选择器使用。"""
        target = Path(path).expanduser() if path else Path.cwd()
        target = target.resolve()
        if not target.exists():
            raise HTTPException(404, f"路径不存在: {target}")
        if target.is_file():
            target = target.parent

        try:
            entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except PermissionError:
            raise HTTPException(403, f"无权限访问: {target}") from None

        items = []
        for p in entries:
            if p.name.startswith("."):
                continue
            if p.is_dir():
                items.append({"name": p.name, "path": str(p), "type": "dir"})
            elif p.suffix.lower() == ".md":
                items.append({"name": p.name, "path": str(p), "type": "file"})
        return {"cwd": str(target), "parent": str(target.parent), "items": items}

    @app.post("/api/run")
    def run(req: RunRequest) -> dict[str, Any]:
        """读取日志 -> 调用 LLM 评判 -> 落历史 -> 返回结果。"""
        if not req.paths:
            raise HTTPException(400, "请先选择至少一个日志文件或目录。")

        paths = [Path(p).expanduser() for p in req.paths]
        try:
            content = reader.load(paths, week=req.week if req.mode == "review" else None)
        except FileNotFoundError as e:
            raise HTTPException(404, str(e)) from None
        except ValueError as e:
            raise HTTPException(400, str(e)) from None

        system = prompts.JUDGE_SYSTEM if req.mode == "judge" else prompts.REVIEW_SYSTEM
        build = (
            prompts.build_judge_prompt
            if req.mode == "judge"
            else prompts.build_review_prompt
        )
        try:
            result = LLM(Settings.from_env()).complete(system, build(content))
        except RuntimeError as e:
            # 通常是缺少 OPENAI_API_KEY。
            raise HTTPException(400, str(e)) from None
        except Exception as e:  # noqa: BLE001 - 把上游 SDK 的错误原样透给前端
            raise HTTPException(502, f"LLM 调用失败: {e}") from None

        record = history_mod.add_record(
            mode=req.mode,
            paths=[str(p) for p in paths],
            week=req.week if req.mode == "review" else None,
            result=result,
            content=content,
        )
        return {"record": record, "content": content}

    @app.get("/api/history")
    def get_history() -> list[dict[str, Any]]:
        return history_mod.list_history()

    @app.get("/api/history/{record_id}")
    def get_history_item(record_id: str) -> dict[str, Any]:
        rec = history_mod.get_record(record_id)
        if rec is None:
            raise HTTPException(404, "记录不存在")
        return rec

    @app.delete("/api/history/{record_id}")
    def delete_history_item(record_id: str) -> dict[str, Any]:
        if not history_mod.delete_record(record_id):
            raise HTTPException(404, "记录不存在")
        return {"ok": True}

    @app.delete("/api/history")
    def clear_history() -> dict[str, Any]:
        return {"removed": history_mod.clear_history()}

    if DIST_DIR.is_dir():
        assets = DIST_DIR / "assets"
        if assets.is_dir():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/")
        def index() -> FileResponse:
            return FileResponse(str(DIST_DIR / "index.html"))

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str) -> Any:
            """SPA 路由兜底：未知路径回落到 index.html。"""
            candidate = DIST_DIR / full_path
            if candidate.is_file():
                return FileResponse(str(candidate))
            return FileResponse(str(DIST_DIR / "index.html"))
    else:
        @app.get("/")
        def placeholder() -> JSONResponse:
            return JSONResponse(
                {
                    "detail": (
                        "前端尚未构建。请在 web/ 下执行 npm install && npm run build，"
                        "或运行 npm run dev 启动 Vite 开发服务器。"
                    )
                }
            )

    return app


app = create_app()


def serve(host: str = "127.0.0.1", port: int = 8777, reload: bool = False) -> None:
    """启动 uvicorn。放在这里而不是 cli，方便被外部脚本复用。"""
    try:
        import uvicorn
    except ModuleNotFoundError as e:
        raise SystemExit(
            "缺少 Web 依赖，请执行：uv pip install -e \".[web]\""
        ) from e

    if os.getenv("LIFELOG_HISTORY_DIR"):
        # 仅做一次存在性校验，避免运行时才发现目录不可写。
        Path(os.environ["LIFELOG_HISTORY_DIR"]).expanduser().mkdir(
            parents=True, exist_ok=True
        )

    uvicorn.run("lifelog_coach.server:app", host=host, port=port, reload=reload)
