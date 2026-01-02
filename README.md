# Employee Attendance Management System

### 1. Employee Management
- 创建员工 `POST /employees`
-  获取员工列表 `GET /employees`
-  获取指定员工 `GET /employees/{employee_id}`
-  按员工代码查询 `GET /employees/code/{employee_code}`
-  更新员工信息 `PUT /employees/{employee_id}`
-  停用员工 `PATCH /employees/{employee_id}/deactivate`
-  删除员工 `DELETE /employees/{employee_id}`

### 2. Attendance Management
-  签到 `POST /attendance/check-in`
-  签退 `PATCH /attendance/check-out`
-  标记缺勤 `POST /attendance/mark-absent`
-  获取出勤列表 `GET /attendance`
-  获取指定出勤记录 `GET /attendance/{attendance_id}`
-  获取今日记录 `GET /attendance/today`
-  获取月度记录 `GET /attendance/month`
-  更新出勤记录 `PUT /attendance/{attendance_id}`
-  删除出勤记录 `DELETE /attendance/{attendance_id}`

### 3. Leave Management
-  提交请假申请 `POST /attendance/leaves`
-  获取请假列表 `GET /attendance/leaves`
-  获取指定请假 `GET /attendance/leaves/{leave_id}`
-  批准请假 `PATCH /attendance/leaves/{leave_id}/approve`
-  拒绝请假 `PATCH /attendance/leaves/{leave_id}/reject`
-  删除请假 `DELETE /attendance/leaves/{leave_id}`

### 4. Reports & Analytics
-  日度汇总 `GET /reports/daily-summary`
-  月度 CSV `GET /reports/monthly-csv`
-  员工月度总结 `GET /reports/employee/{employee_id}/monthly-summary` 
-  部门统计 `GET /reports/department/{department}/attendance`
-  准时排名 `GET /reports/punctuality-ranking`

## 技术栈

- **Web框架**: FastAPI
- **数据存储**: MongoDB
- **ODM**:Beanie(Motor+pydanic)
- **前端**: 静态 HTML(尝试react)
- **部署**: Uvicorn (ASGI)

 # Attendance System

This repository is an employee attendance system built with FastAPI and MongoDB. It provides APIs and a minimal frontend for managing employees, recording check-ins/check-outs, handling leave requests, and generating simple reports.

What’s included:
- Backend: FastAPI with Beanie (MongoDB ODM)
- Frontend: static single-page HTML (build in `frontend/build`)
- Features: employee CRUD, attendance tracking, leave workflow, reports

## Highlights

- Employee management (create, update, deactivate)
- Check-in / check-out by employee code
- Leave requests with approve/reject flow (approved leaves create ON_LEAVE records)
- Daily and monthly reporting endpoints, punctuality ranking

## Quick start

Prerequisites: Python 3.11+ and a running MongoDB instance.

Install and run locally:

```bash
poetry install
poetry run uvicorn attendance_system.main:app --reload
```
run python generate_data.py to genenate 10 users

Open http://127.0.0.1:8000 in your browser. API docs are available at:

- Swagger UI: http://127.0.0.1:8000/docs

## Layout (backend)

```
attendance_system/
├─ main.py        # application bootstrap
├─ database.py    # mongo + beanie init
├─ models.py      # Beanie/Pydantic models
├─ routes/        # API routers (employees, attendance, leaves, reports)
└─ utils.py       # helpers and calculations

frontend/         # static front-end build and source
```

## Developer notes

- Models use `PydanticObjectId` for MongoDB IDs; the public API accepts `employee_code` for user-facing actions.
- The server supports live reload when run with `--reload`.

## Quick curl examples

Submit a leave request:

```bash
curl -X POST http://127.0.0.1:8000/leaves \
  -H 'Content-Type: application/json' \
  -d '{"employee_code":"EMP001","leave_type":"Sick Leave","start_date":"2026-01-10","end_date":"2026-01-12","reason":"Medical"}'
```

Get daily summary:

```bash
curl 'http://127.0.0.1:8000/reports/daily-summary?report_date=2026-01-02'
```