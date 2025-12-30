# 快速参考 (Quick Reference)

## 启动服务
```bash
poetry run uvicorn attendance_system.main:app --reload
```

## 访问地址
- **前端**: http://127.0.0.1:8000
- **API 文档**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## API 端点概览 (27 个)

### 员工管理 (7)
```
POST   /employees                      创建员工
GET    /employees                      获取列表
GET    /employees/{id}                 获取详情
GET    /employees/code/{code}          按代码查询
PUT    /employees/{id}                 更新信息
PATCH  /employees/{id}/deactivate      停用员工
DELETE /employees/{id}                 删除员工
```

### 出勤管理 (11)
```
POST   /attendance/check-in/{id}       路径参数签到
POST   /attendance/check-in            JSON 体签到
PATCH  /attendance/check-out/{id}      路径参数签退
PATCH  /attendance/check-out           JSON 体签退
POST   /attendance/mark-absent         标记缺勤
GET    /attendance                     获取列表
GET    /attendance/{id}                获取详情
GET    /attendance/today               获取今日
GET    /attendance/month               获取月度
PUT    /attendance/{id}                更新记录
DELETE /attendance/{id}                删除记录
```

### 请假管理 (6)
```
POST   /attendance/leaves              提交申请
GET    /attendance/leaves              获取列表
GET    /attendance/leaves/{id}         获取详情
PATCH  /attendance/leaves/{id}/approve 批准请假
PATCH  /attendance/leaves/{id}/reject  拒绝请假
DELETE /attendance/leaves/{id}         删除申请
```

### 报告分析 (5)
```
GET    /reports/daily-summary                              日度汇总
GET    /reports/monthly-csv                                月度 CSV
GET    /reports/employee/{id}/monthly-summary              员工月度总结
GET    /reports/department/{dept}/attendance               部门统计
GET    /reports/punctuality-ranking                        准时排名
```

## 常用 curl 命令

### 创建员工
```bash
curl -X POST http://127.0.0.1:8000/employees \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "employee_code": "EMP001",
    "email": "zhangsan@example.com",
    "department": "Sales",
    "position": "Manager"
  }'
```

### 签到
```bash
curl -X POST http://127.0.0.1:8000/attendance/check-in \
  -H "Content-Type: application/json" \
  -d '{"employee_id": 1}'
```

### 签退
```bash
curl -X PATCH http://127.0.0.1:8000/attendance/check-out \
  -H "Content-Type: application/json" \
  -d '{"attendance_id": 1}'
```

### 查看日报
```bash
curl "http://127.0.0.1:8000/reports/daily-summary?report_date=2024-12-30"
```

### 导出 CSV
```bash
curl -o attendance.csv "http://127.0.0.1:8000/reports/monthly-csv?year=2024&month=12"
```

## 数据模型

### 员工 (Employee)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 唯一ID |
| name | str | 员工名 |
| employee_code | str | 代码 (EMP\d{3}) |
| email | str | 邮箱 |
| department | str | 部门 |
| position | str | 职位 |
| is_deactivated | bool | 是否停用 |
| created_at | datetime | 创建时间 |

### 出勤记录 (AttendanceRecord)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 唯一ID |
| employee_id | int | 员工ID |
| date | date | 出勤日期 |
| check_in_time | datetime | 签到时间 |
| check_out_time | datetime | 签退时间 |
| status | enum | Present/Late/Absent/OnLeave |
| working_hours | float | 工作时长 |
| notes | str | 备注 |

### 请假申请 (LeaveRequest)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 唯一ID |
| employee_id | int | 员工ID |
| leave_type | enum | Sick/Annual/Personal/Other |
| from_date | date | 开始日期 |
| to_date | date | 结束日期 |
| reason | str | 原因 |
| status | enum | Pending/Approved/Rejected |
| created_at | datetime | 创建时间 |

## 错误代码

| 代码 | 说明 |
|------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 204 | 删除成功 (无响应体) |
| 400 | 请求错误 |
| 404 | 资源不存在 |
| 409 | 冲突 (如重复签到) |
| 500 | 服务器错误 |

## 响应头

所有响应包含:
- `X-Attendance-API-Version: 1.0.0` - API 版本
- `X-API-Server: FastAPI` - 服务器类型
- `X-Process-Time: 0.0234` - 处理时间 (秒)

## 查询参数常用值

### 出勤状态
- `Present` - 准时到勤
- `Late` - 迟到
- `Absent` - 缺勤
- `OnLeave` - 请假

### 请假类型
- `Sick` - 病假
- `Annual` - 年假
- `Personal` - 事假
- `Other` - 其他

### 部门
- `Sales` - 销售部
- `IT` - IT部
- `HR` - 人力资源部
- `Finance` - 财务部
- 等... (自定义)

## 项目结构

```
attendance_system/
├── main.py                 FastAPI 应用 + 中间件
├── models.py               Pydantic 数据模型
├── enums.py                枚举定义
├── database.py             全局数据存储
├── utils.py                工具函数
├── logger.py               日志配置
├── routes/
│   ├── employees.py        员工管理 (7 个端点)
│   ├── attendance.py       出勤+请假 (17 个端点)
│   └── reports.py          报告分析 (5 个端点)
└── static/
    └── frontend.html       前端页面

文档文件:
├── README.md               项目说明 (本文件)
├── API_DOCUMENTATION.md    完整 API 文档
├── DEPLOYMENT_GUIDE.md     部署测试指南
├── CHANGELOG.md            版本历史
└── QUICK_REFERENCE.md      快速参考 (本文件)
```

## 中间件

1. **CORSMiddleware** - 跨域资源共享
2. **CSPMiddleware** - 内容安全策略
3. **RequestTimingMiddleware** - 请求计时
4. **VersionHeaderMiddleware** - 版本信息

## 工具函数

```python
# utils.py
calculate_working_hours(check_in, check_out)  # 计算工作时长
determine_status(check_in, check_out)         # 判断状态
is_weekend(date)                              # 判断周末
calculate_leave_days(from_date, to_date)      # 计算请假天数
```

## 性能指标

- **响应时间**: 通常 < 50ms (见 X-Process-Time 响应头)
- **并发处理**: 支持 4+ 个 worker 进程
- **数据容量**: 内存存储，重启后清空 (可升级为数据库)

## 环境变量

当前版本无环境变量配置。如需定制，可修改:
- `main.py` 中的 CORS 配置
- `logger.py` 中的日志级别
- 各个路由中的业务逻辑

## 扩展建议

1. **数据库**: SQLAlchemy + PostgreSQL/MySQL
2. **认证**: JWT + OAuth2
3. **缓存**: Redis
4. **测试**: pytest + pytest-asyncio
5. **部署**: Docker + Kubernetes
6. **监控**: Prometheus + Grafana

## 许可证

MIT

---

**最后更新**: 2024-12-30
**版本**: 1.0.0
**作者**: 出勤系统开发团队
