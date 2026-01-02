from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse
from httpx import AsyncClient
import os
import time
import logging
from attendance_system.logger import setup_logging

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from attendance_system.models import Employee, AttendanceRecord, LeaveRequest


from attendance_system.routes.attendance import router as attendance_router
from attendance_system.routes.employees import router as employees_router
from attendance_system.routes.reports import router as reports_router
from attendance_system.routes.leave import router as leave_router

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

        response.headers["X-Process-Time"] = str(process_time)
        
        # 记录日志
        logger.info(
            f"{request.method} {request.url.path} | "
            f"Status: {response.status_code} | "
            f"Process Time: {process_time:.4f}s"
        )
        
        return response


class VersionHeaderMiddleware(BaseHTTPMiddleware):
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

_mongo_client: AsyncIOMotorClient = None
_mongo_db = None

logger.info("Using MongoDB URL from env or default (not showing credentials)")

@app.on_event("startup")
async def startup_db():
    global _mongo_client, _mongo_db
    try:
        _mongo_client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        # ping 测试连接
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
        # 解析数据库名
        db_name = MONGODB_URL.split("/")[-1].split("?")[0]
        if not db_name:
            db_name = "attendance_db"
        _mongo_db = _mongo_client[db_name]
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
# app.add_middleware(CSPMiddleware)

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置前端静态文件
frontend_build_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "build")
logger.info(f"Frontend build path: {frontend_build_path}")
logger.info(f"Frontend build path exists: {os.path.exists(frontend_build_path)}")

# REACT_DEV_URL = "http://localhost:3000"

# 添加API路由
app.include_router(employees_router)
app.include_router(attendance_router)
app.include_router(reports_router)
app.include_router(leave_router)

# 添加API根路由
@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok"}

# 挂载静态文件
if os.path.exists(frontend_build_path):
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="static")
