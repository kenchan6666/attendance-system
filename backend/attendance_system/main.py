from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse
from httpx import AsyncClient
from attendance_system.routes.attendance import router as attendance_router
from attendance_system.routes.employees import router as employees_router
from attendance_system.routes.reports import router as reports_router
import os
import time
import logging
from attendance_system.logger import setup_logging
from fastapi.middleware.cors import CORSMiddleware

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from attendance_system.models import Employee, AttendanceRecord, LeaveRequest

# 初始化日志
setup_logging()
logger = logging.getLogger(__name__)

class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = "default-src *; script-src * 'unsafe-inline' 'unsafe-eval'; style-src * 'unsafe-inline'; img-src * data: blob:"
        return response


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """记录每个请求的处理时间"""
    async def dispatch(self, request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        # 记录日志
        logger.info(
            f"{request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Process Time: {process_time:.4f}s"
        )
        
        return response


class VersionHeaderMiddleware(BaseHTTPMiddleware):
    """添加 API 版本信息头"""
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Attendance-API-Version"] = "1.0.0"
        response.headers["X-API-Server"] = "FastAPI"
        return response


app = FastAPI(
    title="Staff Attendance Record System",
    description="Staff Attendance Record Management API",
    version="1.0.0",
)

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/attendance_db")

# 全局 MongoDB 客户端与数据库连接
_mongo_client: AsyncIOMotorClient = None
_mongo_db = None

# 简单打印所用连接（不打印敏感凭据）
logger.info("Using MongoDB URL from env or default (not showing credentials)")

@app.on_event("startup")
async def startup_db():
    global _mongo_client, _mongo_db
    try:
        _mongo_client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        # ping 测试连接（添加超时）
        import asyncio
        await asyncio.wait_for(_mongo_client.admin.command('ping'), timeout=5.0)
        logger.info("Connected to MongoDB successfully!")
        print("Connected to MongoDB successfully!")
    except asyncio.TimeoutError:
        logger.error("MongoDB connection timeout - check if MongoDB is running on the configured URL")
        raise RuntimeError("MongoDB connection timeout")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        print(f"MongoDB connection failed: {e}")
        raise
    
    try:
        _mongo_db = _mongo_client.attendance_db
        await init_beanie(
            database=_mongo_db,
            document_models=[Employee, AttendanceRecord, LeaveRequest]
        )
        logger.info("Beanie initialized successfully!")
        print("Beanie initialized successfully!")
    except Exception as e:
        logger.error(f"Beanie initialization failed: {e}")
        print(f"Beanie initialization failed: {e}")
        raise

# 添加中间件
app.add_middleware(VersionHeaderMiddleware)
app.add_middleware(RequestTimingMiddleware)
# app.add_middleware(CSPMiddleware)  # <--- 加上这一行！

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 React 前端静态文件
frontend_build_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "build")
logger.info(f"Frontend build path: {frontend_build_path}")
logger.info(f"Frontend build path exists: {os.path.exists(frontend_build_path)}")

REACT_DEV_URL = "http://localhost:3001"

# 先添加路由，然后挂载静态文件
app.include_router(employees_router, prefix="/employees", tags=["Employees"])
app.include_router(attendance_router)
app.include_router(reports_router)


# 定义前端路由 - 必须在挂载静态文件之前
# @app.get("/")
# async def root(request: Request):
#     """代理到 React 开发服务器，失败则返回静态 HTML"""
#     try:
#         async with AsyncClient() as client:
#             response = await client.get(f"{REACT_DEV_URL}/", timeout=2)
#             return response.content
#     except Exception as e:
#         logger.debug(f"React dev server not available: {e}, falling back to static HTML")
#         index_file = os.path.join(frontend_build_path, "index.html")
#         if os.path.exists(index_file):
#             return FileResponse(index_file, media_type="text/html")
#         return {"message": "React dev server not running"}


# @app.get("/{full_path:path}")
# async def serve_spa(full_path: str, request: Request):
#     """代理所有请求到 React 开发服务器或静态构建"""
#     try:
#         async with AsyncClient() as client:
#             url = f"{REACT_DEV_URL}/{full_path}"
#             if request.query_params:
#                 url += f"?{request.query_params}"
#             response = await client.get(url, timeout=2)
#             if response.status_code == 200:
#                 return response.content
#     except Exception as e:
#         logger.debug(f"React dev server proxy failed for {full_path}: {e}")
    
#     # 回退到静态文件或 index.html
#     file_path = os.path.join(frontend_build_path, full_path)
    
#     if os.path.isfile(file_path):
#         return FileResponse(file_path)
    
#     # 返回 index.html 让前端路由处理
#     index_file = os.path.join(frontend_build_path, "index.html")
#     if os.path.exists(index_file):
#         return FileResponse(index_file, media_type="text/html")
    
#     return {"error": "Not found"}

# 挂载静态文件
if os.path.exists(frontend_build_path):
    # 临时：直接挂载 build 目录到根路径
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static")
