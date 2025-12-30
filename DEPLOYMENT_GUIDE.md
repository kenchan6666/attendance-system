# 部署和测试指南

## 快速开始

### 环境要求
- Python 3.8+
- Poetry (推荐) 或 pip

### 安装依赖

**使用 Poetry:**
```bash
cd attendance_system
poetry install
```

**使用 pip:**
```bash
pip install fastapi uvicorn pydantic email-validator python-multipart
```

### 启动服务

**开发环境 (推荐, 有热重载):**
```bash
poetry run uvicorn attendance_system.main:app --reload --host 127.0.0.1 --port 8000
```

**生产环境:**
```bash
poetry run uvicorn attendance_system.main:app --host 0.0.0.0 --port 8000 --workers 4
```

服务器启动后访问:
- **前端**: http://127.0.0.1:8000
- **API 文档**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## 测试指南

### 单元测试

创建 `test_api.py`:
```python
import requests
from datetime import date

BASE_URL = "http://127.0.0.1:8000"

def test_employee_creation():
    """测试创建员工"""
    response = requests.post(
        f"{BASE_URL}/employees",
        json={
            "name": "张三",
            "employee_code": "EMP001",
            "email": "zhangsan@example.com",
            "department": "Sales",
            "position": "Manager"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "张三"
    return data["id"]

def test_check_in(emp_id):
    """测试签到"""
    response = requests.post(
        f"{BASE_URL}/attendance/check-in",
        json={"employee_id": emp_id}
    )
    assert response.status_code == 201
    return response.json()["id"]

def test_check_out(attendance_id):
    """测试签退"""
    response = requests.patch(
        f"{BASE_URL}/attendance/check-out",
        json={"attendance_id": attendance_id}
    )
    assert response.status_code == 200

def test_daily_summary():
    """测试日报"""
    response = requests.get(
        f"{BASE_URL}/reports/daily-summary",
        params={"report_date": date.today()}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_active" in data
    assert "on_duty" in data

if __name__ == "__main__":
    print("创建员工...")
    emp_id = test_employee_creation()
    print(f"✓ 员工创建成功，ID: {emp_id}")
    
    print("签到...")
    att_id = test_check_in(emp_id)
    print(f"✓ 签到成功，ID: {att_id}")
    
    print("签退...")
    test_check_out(att_id)
    print("✓ 签退成功")
    
    print("查看日报...")
    test_daily_summary()
    print("✓ 日报查询成功")
    
    print("\n✅ 所有测试通过！")
```

运行测试:
```bash
python test_api.py
```

### 使用 curl 测试

**1. 创建员工**
```bash
curl -X POST http://127.0.0.1:8000/employees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "李四",
    "employee_code": "EMP002",
    "email": "lisi@example.com",
    "department": "IT",
    "position": "Developer"
  }'
```

**2. 获取员工列表**
```bash
curl http://127.0.0.1:8000/employees
```

**3. 签到**
```bash
curl -X POST http://127.0.0.1:8000/attendance/check-in \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 1}'
```

**4. 签退**
```bash
curl -X PATCH http://127.0.0.1:8000/attendance/check-out \
  -H "Content-Type: application/json" \
  -d '{"attendance_id": 1}'
```

**5. 查看日报**
```bash
curl "http://127.0.0.1:8000/reports/daily-summary?report_date=2024-12-30"
```

**6. 下载 CSV**
```bash
curl -o attendance.csv "http://127.0.0.1:8000/reports/monthly-csv?year=2024&month=12"
```

### 使用 Postman 测试

1. 打开 Postman
2. 导入 Swagger JSON: http://127.0.0.1:8000/openapi.json
3. 或手动创建请求，选择 POST/PATCH/DELETE 等方法
4. 设置请求体为 JSON 格式
5. 点击 Send

### 使用 Swagger UI 交互式测试

1. 访问 http://127.0.0.1:8000/docs
2. 展开各个端点
3. 点击 "Try it out" 按钮
4. 填入参数和请求体
5. 点击 "Execute" 执行请求

---

## API 响应时间监控

系统在每个响应中包含 `X-Process-Time` 头，显示处理时间（秒）:

```bash
$ curl -i http://127.0.0.1:8000/reports/daily-summary?report_date=2024-12-30

HTTP/1.1 200 OK
X-Process-Time: 0.0234
X-Attendance-API-Version: 1.0.0
...
```

### 日志文件

日志默认保存在 `logs/attendance_api.log`：

```bash
tail -f logs/attendance_api.log
```

日志示例:
```
2024-12-30 10:00:00 - attendance_system.main - INFO - POST /employees | Status: 201 | Process Time: 0.0123s
2024-12-30 10:00:01 - attendance_system.main - INFO - POST /attendance/check-in | Status: 201 | Process Time: 0.0089s
```

---

## 常见问题

### Q: 服务器无法启动？
**A:** 检查端口 8000 是否被占用：
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

如果占用，使用其他端口:
```bash
poetry run uvicorn attendance_system.main:app --port 8001
```

### Q: 数据在重启后消失？
**A:** 目前使用内存数据库，重启后数据会丢失。可以集成 SQLAlchemy 或 MongoDB 持久化数据。

### Q: 如何修改默认端口？
**A:** 修改启动命令中的 `--port` 参数，或在代码中修改 `main.py`。

### Q: 如何处理 CORS 问题？
**A:** 修改 `main.py` 中的 `allow_origins` 列表：
```python
allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", ...],
```

### Q: 如何添加身份验证？
**A:** 可以使用 FastAPI 的 OAuth2 和 JWT:
```python
from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()

@app.get("/protected")
def protected_route(credentials: HTTPAuthCredentials = Depends(security)):
    # 验证 token
    return {"message": "这是受保护的资源"}
```

### Q: 如何部署到生产环境？
**A:** 
1. 使用 Gunicorn + Uvicorn workers:
```bash
poetry run gunicorn attendance_system.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

2. 或使用 Docker:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install poetry && poetry install --no-dev

CMD ["poetry", "run", "uvicorn", "attendance_system.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

3. 使用 Nginx 反向代理:
```nginx
server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
    }
}
```

---

## 性能优化建议

1. **缓存**: 使用 Redis 缓存报告结果
2. **数据库**: 迁移到 PostgreSQL/MySQL 提高并发处理
3. **异步**: 对耗时操作使用 `async def` 和 `BackgroundTasks`
4. **分页**: 大型列表查询务必使用分页
5. **索引**: 数据库中为常查询字段添加索引

---

## 监控和告警

建议添加以下监控：
- API 响应时间
- 错误率
- 数据库连接数
- 内存占用
- CPU 使用率

可以使用 Prometheus + Grafana 或 New Relic 等工具。
