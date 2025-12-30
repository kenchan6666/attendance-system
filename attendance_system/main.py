from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from attendance_system.routes.attendance import router as attendance_router
from attendance_system.routes.employees import router as employees_router
from attendance_system.routes.reports import router as reports_router
from fastapi.staticfiles import StaticFiles
import os
import time
import logging
from attendance_system.logger import setup_logging
from fastapi.middleware.cors import CORSMiddleware

# 初始化日志
setup_logging()
logger = logging.getLogger(__name__)

class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        # 完全宽松的 CSP，允许所有内容
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

# 配置静态文件目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 添加中间件 (顺序很重要，从下到上执行)
# 1. 版本头中间件 (最后添加)
app.add_middleware(VersionHeaderMiddleware)

# 2. 请求计时中间件
app.add_middleware(RequestTimingMiddleware)

# 3. CSP 响应头中间件
app.add_middleware(CSPMiddleware)

# 4. CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(employees_router, prefix="/employees", tags=["Employees"])
app.include_router(attendance_router)
app.include_router(reports_router)

@app.get("/")
def home():
    static_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "frontend.html")
    if os.path.exists(static_file):
        return FileResponse(static_file, media_type="text/html")
    return {"message": "Welcome! Visit /docs for API documentation or /static/frontend.html for frontend demo"}
