# API 文档

## 目录

1. [员工管理 API](#员工管理-api)
2. [出勤管理 API](#出勤管理-api)
3. [请假管理 API](#请假管理-api)
4. [报告分析 API](#报告分析-api)
5. [错误处理](#错误处理)
6. [响应头](#响应头)

---

## 员工管理 API

### 创建员工
```
POST /employees
```

**请求体:**
```json
{
  "name": "张三",
  "employee_code": "EMP001",
  "email": "zhangsan@example.com",
  "department": "Sales",
  "position": "Manager"
}
```

**响应 (201 Created):**
```json
{
  "id": 1,
  "name": "张三",
  "employee_code": "EMP001",
  "email": "zhangsan@example.com",
  "department": "Sales",
  "position": "Manager",
  "is_deactivated": false,
  "created_at": "2024-12-30T10:00:00"
}
```

### 获取员工列表
```
GET /employees?department=Sales&skip=0&limit=10
```

**查询参数:**
- `department` (可选): 部门名称过滤
- `skip`: 分页偏移 (默认 0)
- `limit`: 分页大小 (默认 10，最大 100)

**响应 (200 OK):**
```json
[
  {
    "id": 1,
    "name": "张三",
    "employee_code": "EMP001",
    ...
  }
]
```

### 获取员工详情
```
GET /employees/{employee_id}
```

**响应 (200 OK):** 员工对象

**错误:**
- 404: 员工不存在

### 按员工代码查询
```
GET /employees/code/{employee_code}
```

### 更新员工
```
PUT /employees/{employee_id}
```

**请求体:** 完整员工对象 (id 和 employee_code 无法修改)

### 停用员工
```
PATCH /employees/{employee_id}/deactivate
```

**响应 (200 OK):** 更新后的员工对象 (is_deactivated=true)

### 删除员工
```
DELETE /employees/{employee_id}
```

**响应 (204 No Content)**

---

## 出勤管理 API

### 签到 (路径参数版本)
```
POST /attendance/check-in/{employee_id}
```

**查询参数:**
- `check_in_time` (可选): 签到时间，格式 ISO 8601

**响应 (201 Created):**
```json
{
  "id": 1,
  "employee_id": 1,
  "date": "2024-12-30",
  "check_in_time": "2024-12-30T09:00:00",
  "check_out_time": null,
  "status": "Present",
  "working_hours": null,
  "notes": null
}
```

**错误:**
- 400: 周末不能签到
- 404: 员工不存在
- 409: 今日已签到

### 签到 (JSON 体版本)
```
POST /attendance/check-in
```

**请求体:**
```json
{
  "employee_id": 1
}
```

### 签退
```
PATCH /attendance/check-out/{attendance_id}
```

**查询参数:**
- `check_out_time` (可选): 签退时间

**响应 (200 OK):** 更新后的出勤记录

### 签退 (JSON 体版本)
```
PATCH /attendance/check-out
```

**请求体:**
```json
{
  "attendance_id": 1
}
```

### 标记缺勤
```
POST /attendance/mark-absent
```

**请求体:**
```json
{
  "employee_id": 1,
  "date": "2024-12-30",
  "reason": "生病"
}
```

**响应 (201 Created):** 新的出勤记录 (状态为 Absent)

### 获取出勤列表
```
GET /attendance?employee_id=1&date_from=2024-12-01&date_to=2024-12-31&skip=0&limit=100
```

**查询参数:**
- `employee_id` (可选): 员工 ID 过滤
- `date_from` (可选): 开始日期
- `date_to` (可选): 结束日期
- `status` (可选): 出勤状态 (Present/Late/Absent/OnLeave)
- `department` (可选): 部门过滤
- `skip`: 分页偏移
- `limit`: 分页大小

### 获取出勤详情
```
GET /attendance/{attendance_id}
```

### 获取今日出勤
```
GET /attendance/today?target_date=2024-12-30
```

### 获取月度出勤
```
GET /attendance/month?year=2024&month=12&employee_id=1
```

### 更新出勤记录
```
PUT /attendance/{attendance_id}
```

**请求体:** 完整出勤记录对象

### 删除出勤记录
```
DELETE /attendance/{attendance_id}
```

**响应 (204 No Content)**

---

## 请假管理 API

### 提交请假申请
```
POST /attendance/leaves
```

**请求体:**
```json
{
  "employee_id": 1,
  "leave_type": "Sick",
  "from_date": "2024-12-31",
  "to_date": "2025-01-02",
  "reason": "身体不适"
}
```

**leave_type 可选值:**
- Sick: 病假
- Annual: 年假
- Personal: 事假
- Other: 其他

**响应 (201 Created):** 新的请假申请

### 获取请假列表
```
GET /attendance/leaves?employee_id=1&status=Pending&leave_type=Sick&skip=0&limit=10
```

**查询参数:**
- `employee_id` (可选): 员工 ID 过滤
- `status` (可选): 申请状态 (Pending/Approved/Rejected)
- `leave_type` (可选): 请假类型
- `skip`: 分页偏移
- `limit`: 分页大小

### 获取请假详情
```
GET /attendance/leaves/{leave_id}
```

### 批准请假
```
PATCH /attendance/leaves/{leave_id}/approve
```

**响应 (200 OK):** 更新后的请假申请

**自动操作:**
- 状态变更为 Approved
- 自动为请假期间的每一天创建 ON_LEAVE 出勤记录

### 拒绝请假
```
PATCH /attendance/leaves/{leave_id}/reject
```

**响应 (200 OK):** 更新后的请假申请

**限制:**
- 只能拒绝状态为 Pending 的申请

### 删除请假申请
```
DELETE /attendance/leaves/{leave_id}
```

**响应 (204 No Content)**

**限制:**
- 只能删除状态为 Pending 的申请

---

## 报告分析 API

### 日度汇总
```
GET /reports/daily-summary?report_date=2024-12-30
```

**查询参数:**
- `report_date`: 报告日期

**响应:**
```json
{
  "date": "2024-12-30",
  "total_active": 10,
  "present": 8,
  "absent": 1,
  "late": 1,
  "on_leave": 0,
  "on_duty": 8,
  "absent_employees": ["李四"],
  "late_employees": ["王五"]
}
```

### 月度 CSV 导出
```
GET /reports/monthly-csv?year=2024&month=12
```

**响应:** CSV 文件下载

### 员工月度总结
```
GET /reports/employee/{employee_id}/monthly-summary?year=2024&month=12
```

**响应:**
```json
{
  "employee_id": "1",
  "employee_name": "张三",
  "year": 2024,
  "month": 12,
  "working_days": 22,
  "present_days": 20,
  "late_days": 1,
  "absent_days": 1,
  "leave_days": 0,
  "total_hours": 160.5,
  "avg_check_in_time": "09:05:00",
  "attendance_rate": 95.45
}
```

### 部门统计
```
GET /reports/department/{department}/attendance?date_from=2024-12-01&date_to=2024-12-31
```

**响应:**
```json
{
  "department": "Sales",
  "date_from": "2024-12-01",
  "date_to": "2024-12-31",
  "total_employees": 10,
  "avg_attendance_rate": 92.5,
  "total_late": 3,
  "total_absent": 2
}
```

### 准时排名
```
GET /reports/punctuality-ranking?date_from=2024-12-01&date_to=2024-12-31&limit=10
```

**查询参数:**
- `date_from` (可选): 开始日期
- `date_to` (可选): 结束日期
- `limit`: 返回前 N 名 (默认 10)

**响应:**
```json
{
  "date_from": "2024-12-01",
  "date_to": "2024-12-31",
  "total_ranked": 10,
  "rankings": [
    {
      "employee_id": "1",
      "employee_name": "张三",
      "attendance_rate": 100.0,
      "late_count": 0,
      "working_days": 22
    },
    ...
  ]
}
```

---

## 错误处理

### 错误响应格式
所有错误响应遵循以下格式：

```json
{
  "detail": "错误信息描述"
}
```

### 常见错误码

| 状态码 | 说明 |
|-------|------|
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 409 | 资源冲突 (例: 重复签到) |
| 500 | 服务器内部错误 |

---

## 响应头

### 自定义响应头

所有 API 响应包含以下自定义响应头：

```
X-Attendance-API-Version: 1.0.0    # API 版本
X-API-Server: FastAPI              # 服务器类型
X-Process-Time: 0.0234             # 请求处理时间 (秒)
```

### 例子
```
$ curl -i http://localhost:8000/employees

HTTP/1.1 200 OK
X-Attendance-API-Version: 1.0.0
X-API-Server: FastAPI
X-Process-Time: 0.0234
Content-Type: application/json

[...]
```

---

## 使用示例

### 完整的出勤流程

1. **创建员工**
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

2. **签到**
```bash
curl -X POST http://localhost:8000/attendance/check-in \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 1}'
```

3. **签退**
```bash
curl -X PATCH http://localhost:8000/attendance/check-out \
  -H "Content-Type: application/json" \
  -d '{"attendance_id": 1}'
```

4. **查看日报**
```bash
curl http://localhost:8000/reports/daily-summary?report_date=2024-12-30
```

5. **查看月度总结**
```bash
curl http://localhost:8000/reports/employee/1/monthly-summary?year=2024&month=12
```

---

## 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
