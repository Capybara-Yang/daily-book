"""
每日一书 — 后端入口
FastAPI + SQLite + DeepSeek API
同时托管前端静态文件
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from api import books, chat, survey, user, upload
from services.database import init_db
from services.scheduler import start_scheduler

# 前端静态文件路径
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库 + 定时任务
    init_db()
    start_scheduler()
    yield


app = FastAPI(title="每日一书 API", version="1.0.0", lifespan=lifespan)

# CORS — 允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境改为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(survey.router, prefix="/api/survey", tags=["问卷"])
app.include_router(books.router, prefix="/api/books", tags=["书库"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])
app.include_router(user.router, prefix="/api/user", tags=["用户"])
app.include_router(upload.router, prefix="/api/upload", tags=["上传"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "mock_mode": not os.getenv("DEEPSEEK_API_KEY")}


# 托管前端静态文件（PWA 资源）
if FRONTEND_DIST.exists():
    # 挂载静态资源目录
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    # PWA 相关文件
    @app.get("/manifest.json")
    async def manifest():
        return FileResponse(FRONTEND_DIST / "manifest.json")

    @app.get("/manifest.webmanifest")
    async def manifest_old():
        return FileResponse(FRONTEND_DIST / "manifest.json")

    @app.get("/sw.js")
    async def sw():
        return FileResponse(FRONTEND_DIST / "sw.js")

    @app.get("/workbox-{name}.js")
    async def workbox(name: str):
        return FileResponse(FRONTEND_DIST / f"workbox-{name}.js")

    # SPA fallback — 所有非 API 路由返回 index.html
    @app.get("/{path:path}")
    async def spa_fallback(path: str):
        file_path = FRONTEND_DIST / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(FRONTEND_DIST / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "name": "每日一书 API",
            "version": "1.0.0",
            "mock_mode": not os.getenv("DEEPSEEK_API_KEY"),
            "docs": "/docs",
            "note": "前端未构建，请先 cd frontend && pnpm build"
        }
