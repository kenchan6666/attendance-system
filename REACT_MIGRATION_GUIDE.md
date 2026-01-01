# React 前端完整迁移指南

## 项目结构

```
frontend/
├── package.json              # 项目配置（已有 React, Axios）
├── public/
│   └── index.html           # HTML 入口（有 <div id="root">）
└── src/
    ├── App.js              # 主应用（标签页导航）
    ├── App.css             # 全局样式
    ├── index.js            # 应用入口
    └── components/
        ├── AttendanceOps.js       # 出勤操作（签到、签退、请假）
        ├── DailyReport.js         # 日报报表（展示当日统计）
        ├── EmployeeList.js        # 员工列表（创建/查看）
        ├── DepartmentStats.js     # 部门统计（日期范围统计）
        └── PunctualityRanking.js  # 准时率排行榜（排名显示）
```

## 组件功能说明

### 1. App.js - 主应用
- **功能**: 标签页导航，全局员工列表管理
- **状态**: activeTab（当前标签），employees（员工列表）
- **标签页**:
  - 📋 出勤操作
  - 📊 日报
  - 👥 员工列表
  - 🏢 部门统计
  - 🏆 准时率排行

### 2. AttendanceOps.js - 出勤操作
- **功能**: 员工签到、签退、标记请假
- **输入**: 员工编号（支持"1"自动转换为"EMP001"）
- **API**:
  - POST `/attendance/check-in` - 签到
  - POST `/attendance/check-out` - 签退（返回工作时长）
  - POST `/attendance/mark-absent` - 标记请假

### 3. DailyReport.js - 日报
- **功能**: 展示当日出勤汇总和员工名单
- **输入**: 日期选择器（默认今天）
- **显示**: 总人数、出勤数、缺勤数、迟到数、请假数、值班数
- **API**: GET `/reports/daily-summary?date={YYYY-MM-DD}`

### 4. EmployeeList.js - 员工列表
- **功能**: 查看所有员工和创建新员工
- **表格显示**: 编号、姓名、邮箱、部门、职位、入职日期
- **创建表单**: 包括所有员工字段和部门选择
- **API**: 
  - GET `/employees/` - 获取列表
  - POST `/employees/` - 创建员工

### 5. DepartmentStats.js - 部门统计
- **功能**: 按部门和日期范围统计出勤
- **输入**: 部门选择、日期范围
- **显示**: 人数、平均出勤率、总迟到数、总缺勤数
- **API**: GET `/reports/department/{dept}/attendance?date_from={}&date_to={}`

### 6. PunctualityRanking.js - 准时率排行
- **功能**: 展示员工准时率排行榜
- **输入**: 日期范围、显示数量上限
- **排名表**: 排名、编号、姓名、出勤率(%)、迟到次数、工作日
- **排序**: 出勤率降序 → 迟到次数升序
- **API**: GET `/reports/punctuality-ranking?date_from={}&date_to={}&limit={}`

## 样式特性

### App.css 包含的样式类
- `.App` - 主容器最大宽度1200px
- `.header` - 页面标题区
- `.nav-tabs` - 标签页导航（含 .active 状态）
- `.section` - 内容区域
- `.form-container`, `.form-group` - 表单样式
- `.btn-primary`, `.btn-danger`, `.btn-success` - 按钮样式
- `.status` - 消息提示（success, error, info）
- `.stat-box` - 统计卡片（带彩色渐变）
- `.employee-list` - 员工列表
- `table` - 表格（含悬停效果）
- 响应式设计 - 支持移动设备（768px以下）

## 快速开始

### 1. 安装依赖
```bash
cd frontend
npm install
```

### 2. 启动前端
```bash
npm start
```
访问 http://localhost:3000

### 3. 确保后端正在运行
```bash
cd attendance_system
poetry run uvicorn attendance_system.main:app --reload
```
后端地址: http://127.0.0.1:8000

## 已验证的功能

✅ **所有 API 端点**已在后端测试通过
- 日报显示员工名单正确（已修复"未知员工"问题）
- 准时率排行计算准确（已修复重复计数问题）
- 员工创建和查询正常
- 出勤操作正常工作

## 常见 API 响应格式

### 日报
```json
{
  "total_active": 10,
  "present": 8,
  "absent": 2,
  "late": 1,
  "on_leave": 1,
  "on_duty": 0,
  "present_employees": [{"name": "张三", "code": "EMP001"}],
  "absent_employees": [...],
  "late_employees": [...]
}
```

### 准时率排行
```json
{
  "rankings": [
    {
      "employee_code": "EMP001",
      "employee_name": "张三",
      "attendance_rate": 95.0,
      "late_count": 1,
      "working_days": 20
    }
  ]
}
```

## 技术栈确认

- **前端框架**: React 18.2.0
- **HTTP 客户端**: Axios 1.6.0
- **开发服务器**: react-scripts 5.0.1
- **后端 API**: FastAPI @ http://127.0.0.1:8000
- **数据库**: MongoDB @ mongodb://localhost:27017/attendance_db

## 注意事项

1. **后端必须运行**: React 前端依赖后端 API，请先启动后端
2. **CORS 已启用**: 后端已配置 CORS，允许前端跨域请求
3. **日期格式**: 所有日期使用 YYYY-MM-DD 格式
4. **员工编号**: 前端自动转换（"1" → "EMP001"）
5. **刷新员工列表**: 创建新员工后，所有标签页的员工列表会自动更新

## 后续优化建议

- [ ] 添加加载动画（Spinner）
- [ ] 添加确认对话框（删除操作）
- [ ] 表格分页功能（员工列表>20人时）
- [ ] 添加表单验证（创建员工前）
- [ ] 添加数据导出功能（报表导出 CSV/Excel）
- [ ] 添加搜索和筛选功能
