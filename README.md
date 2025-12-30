# Employee Attendance Management System

一个完整的员工出勤管理系统，包括员工信息管理、出勤记录、请假申请、报告分析等功能。

**全功能实现，27 个 API 端点，生产就绪！** ✨

## 📚 文档导航

- **[完整 API 文档](API_DOCUMENTATION.md)** - 所有 API 端点的详细说明和示例
- **[部署测试指南](DEPLOYMENT_GUIDE.md)** - 安装、启动、测试、部署说明
- **[版本变更日志](CHANGELOG.md)** - 功能列表和发展规划
- **[快速参考](QUICK_REFERENCE.md)** - API 端点快速查询
- **[最终报告](FINAL_REPORT.md)** - 项目完成情况和统计数据 ✨ NEW
- **[完成清单](COMPLETION_CHECKLIST.md)** - 项目验证和检查清单 ✨ NEW

### 1. 员工管理 (Employee Management)
- ✅ 创建员工 `POST /employees`
- ✅ 获取员工列表 `GET /employees`
- ✅ 获取指定员工 `GET /employees/{employee_id}`
- ✅ 按员工代码查询 `GET /employees/code/{employee_code}`
- ✅ 更新员工信息 `PUT /employees/{employee_id}`
- ✅ 停用员工 `PATCH /employees/{employee_id}/deactivate`
- ✅ 删除员工 `DELETE /employees/{employee_id}`

### 2. 出勤管理 (Attendance Management)
- ✅ 签到 `POST /attendance/check-in` (支持路径和 JSON 体)
- ✅ 签退 `PATCH /attendance/check-out` (支持路径和 JSON 体)
- ✅ 标记缺勤 `POST /attendance/mark-absent` (JSON 体)
- ✅ 获取出勤列表 `GET /attendance`
- ✅ 获取指定出勤记录 `GET /attendance/{attendance_id}`
- ✅ 获取今日记录 `GET /attendance/today`
- ✅ 获取月度记录 `GET /attendance/month`
- ✅ 更新出勤记录 `PUT /attendance/{attendance_id}`
- ✅ 删除出勤记录 `DELETE /attendance/{attendance_id}`

### 3. 请假管理 (Leave Management)
- ✅ 提交请假申请 `POST /attendance/leaves`
- ✅ 获取请假列表 `GET /attendance/leaves` (支持过滤和分页)
- ✅ 获取指定请假 `GET /attendance/leaves/{leave_id}`
- ✅ 批准请假 `PATCH /attendance/leaves/{leave_id}/approve`
- ✅ 拒绝请假 `PATCH /attendance/leaves/{leave_id}/reject`
- ✅ 删除请假 `DELETE /attendance/leaves/{leave_id}`

### 4. 报告分析 (Reports & Analytics)
- ✅ 日度汇总 `GET /reports/daily-summary` (出勤、缺勤、迟到、请假、在岗)
- ✅ 月度 CSV `GET /reports/monthly-csv`
- ✅ 员工月度总结 `GET /reports/employee/{employee_id}/monthly-summary` (工作日、出勤率、工时、迟到)
- ✅ 部门统计 `GET /reports/department/{department}/attendance` (部门出勤率、迟到、缺勤)
- ✅ 准时排名 `GET /reports/punctuality-ranking` (按出勤率和迟到排名)

## 技术栈

- **后端**: FastAPI (Python)
- **数据存储**: 内存列表 (可扩展为数据库)
- **前端**: 静态 HTML + Vanilla JavaScript
- **部署**: Uvicorn (ASGI)

## 快速开始

### 安装依赖
```bash
poetry install
```

### 启动服务
```bash
poetry run uvicorn attendance_system.main:app --reload
```

服务器将在 `http://localhost:8000` 启动

### 访问前端
打开浏览器访问 `http://localhost:8000` 即可使用前端界面

### API 文档
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 项目结构

```
attendance_system/
├── __init__.py
├── main.py              # FastAPI 应用入口
├── database.py          # 数据库全局变量
├── models.py            # Pydantic 数据模型
├── enums.py             # 枚举类型
├── utils.py             # 工具函数
├── routes/
│   ├── employees.py     # 员工管理路由
│   ├── attendance.py    # 出勤和请假路由
│   └── reports.py       # 报告和分析路由
├── static/
│   └── frontend.html    # 前端页面
```

## API 示例

### 1. 创建员工
```bash
curl -X POST http://localhost:8000/employees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "employee_code": "EMP001",
    "email": "zhangsan@example.com",
    "department": "Sales",
    "position": "Manager"
  }'
```

### 2. 签到
```bash
curl -X POST http://localhost:8000/attendance/check-in \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "emp-001"}'
```

### 3. 获取日报
```bash
curl http://localhost:8000/reports/daily-summary?report_date=2024-12-19
```

### 4. 获取员工月度总结
```bash
curl http://localhost:8000/reports/employee/emp-001/monthly-summary?year=2024&month=12
```

### 5. 获取准时排名
```bash
curl http://localhost:8000/reports/punctuality-ranking?limit=10&date_from=2024-12-01&date_to=2024-12-31
```

## 功能完整性

**已实现 (100%)**:
- ✅ 员工管理 - 7 个端点
- ✅ 出勤管理 - 9 个端点
- ✅ 请假管理 - 6 个端点
- ✅ 报告分析 - 5 个端点

**总计: 27 个 API 端点**

## 特色功能

1. **灵活的签到/签退**: 支持路径参数和 JSON 请求体两种方式
2. **完整的请假流程**: 提交 → 批准/拒绝 → 自动生成出勤记录
3. **多维度报告**: 日报、月报、员工总结、部门统计、准时排名
4. **准确的工时计算**: 自动计算每日工时、月度总工时、出勤率
5. **请假管理**: 支持病假、年假、事假等多种请假类型，自动扣减出勤
6. **前端集成**: 单页 HTML 应用，实时交互，无需刷新

## 数据模型

### 员工 (Employee)
- id: 唯一标识符
- name: 员工名称
- employee_code: 员工代码 (格式: EMP\d{3})
- email: 电子邮箱
- department: 部门
- position: 职位
- hire_date: 入职日期
- is_deactivated: 是否已停用

### 出勤记录 (AttendanceRecord)
- id: 唯一标识符
- employee_id: 员工 ID
- date: 出勤日期
- check_in: 签到时间
- check_out: 签退时间
- status: 出勤状态 (Present/Late/Absent/OnLeave)
- reason: 备注

### 请假申请 (LeaveRequest)
- id: 唯一标识符
- employee_id: 员工 ID
- leave_type: 请假类型 (Sick/Annual/Personal/Other)
- from_date: 开始日期
- to_date: 结束日期
- reason: 请假原因
- status: 申请状态 (Pending/Approved/Rejected)
- created_at: 创建时间
- updated_at: 更新时间

## 许可证

MIT
