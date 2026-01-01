#!/usr/bin/env python
"""
测试脚本：验证所有 API 端点功能
"""
import requests
import json
import random
from datetime import date, datetime, timedelta

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"Content-Type": "application/json"}

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_employees():
    """测试员工管理端点"""
    print_section("1. 测试员工管理 API")
    
    # 创建员工
    emp_code = f"E{random.randint(10000, 99999)}"[:6]
    emp_data = {
        "full_name": "张三",
        "employee_code": emp_code,
        "email": "zhangsan@example.com",
        "department": "Sales",
        "position": "Manager",
        "hire_date": date.today().isoformat()
    }
    resp = requests.post(f"{BASE_URL}/employees", json=emp_data, headers=HEADERS)
    print(f"POST /employees: {resp.status_code}")
    emp = resp.json() if resp.status_code == 201 else None
    
    if emp:
        emp_id = emp.get("id")
        
        # 获取员工列表
        resp = requests.get(f"{BASE_URL}/employees")
        print(f"GET /employees: {resp.status_code} - {len(resp.json())} 员工")
        
        # 获取指定员工
        resp = requests.get(f"{BASE_URL}/employees/{emp_id}")
        print(f"GET /employees/{emp_id}: {resp.status_code}")
        
        return emp_id
    return None

def test_attendance(emp_id):
    """测试出勤管理端点"""
    print_section("2. 测试出勤管理 API")
    
    # 签到 (JSON body 版本)
    check_in_data = {"employee_id": emp_id}
    resp = requests.post(f"{BASE_URL}/attendance/check-in", json=check_in_data, headers=HEADERS)
    print(f"POST /attendance/check-in (JSON): {resp.status_code}")
    
    # 获取今日出勤记录
    resp = requests.get(f"{BASE_URL}/attendance/today", params={"target_date": date.today()})
    print(f"GET /attendance/today: {resp.status_code} - {len(resp.json())} 条记录")
    records = resp.json()
    
    if records:
        record_id = records[0]["id"]
        
        # 签退 (JSON body 版本)
        check_out_data = {"attendance_id": record_id}
        resp = requests.patch(f"{BASE_URL}/attendance/check-out", json=check_out_data, headers=HEADERS)
        print(f"PATCH /attendance/check-out (JSON): {resp.status_code}")
        
        # 删除出勤记录
        resp = requests.delete(f"{BASE_URL}/attendance/{record_id}")
        print(f"DELETE /attendance/{record_id}: {resp.status_code}")
    
    return emp_id

def test_leaves(emp_id):
    """测试请假管理端点"""
    print_section("3. 测试请假管理 API")
    
    # 提交请假申请
    leave_data = {
        "employee_id": emp_id,
        "leave_type": "Sick",
        "from_date": date.today(),
        "to_date": date.today(),
        "reason": "身体不适"
    }
    resp = requests.post(f"{BASE_URL}/attendance/leaves", json=leave_data, headers=HEADERS)
    print(f"POST /attendance/leaves: {resp.status_code}")
    leave = resp.json() if resp.status_code == 201 else None
    
    if leave:
        leave_id = leave.get("id")
        
        # 获取请假列表
        resp = requests.get(f"{BASE_URL}/attendance/leaves")
        print(f"GET /attendance/leaves: {resp.status_code} - {len(resp.json())} 条请假")
        
        # 获取指定请假
        resp = requests.get(f"{BASE_URL}/attendance/leaves/{leave_id}")
        print(f"GET /attendance/leaves/{leave_id}: {resp.status_code}")
        
        # 拒绝请假
        resp = requests.patch(f"{BASE_URL}/attendance/leaves/{leave_id}/reject")
        print(f"PATCH /attendance/leaves/{leave_id}/reject: {resp.status_code}")
        
        # 删除请假
        resp = requests.delete(f"{BASE_URL}/attendance/leaves/{leave_id}")
        print(f"DELETE /attendance/leaves/{leave_id}: {resp.status_code}")

def test_reports(emp_id):
    """测试报告端点"""
    print_section("4. 测试报告 API")
    
    today = date.today()
    
    # 日报
    resp = requests.get(f"{BASE_URL}/reports/daily-summary", params={"report_date": today})
    print(f"GET /reports/daily-summary: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  - 总员工数: {data.get('total_active', 0)}")
        print(f"  - 当前在岗: {data.get('on_duty', 0)}")
    
    # 月度员工总结
    resp = requests.get(f"{BASE_URL}/reports/employee/{emp_id}/monthly-summary", 
                       params={"year": today.year, "month": today.month})
    print(f"GET /reports/employee/{emp_id}/monthly-summary: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  - 出勤日: {data.get('present_days', 0)}")
        print(f"  - 出勤率: {data.get('attendance_rate', 0)}%")
    
    # 部门统计 (Sales)
    resp = requests.get(f"{BASE_URL}/reports/department/Sales/attendance",
                       params={"date_from": str(today.replace(day=1)), "date_to": str(today)})
    print(f"GET /reports/department/Sales/attendance: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  - 部门员工: {data.get('total_employees', 0)}")
        print(f"  - 平均出勤率: {data.get('avg_attendance_rate', 0)}%")
    
    # 准时排名
    resp = requests.get(f"{BASE_URL}/reports/punctuality-ranking",
                       params={"date_from": str(today.replace(day=1)), "date_to": str(today), "limit": 10})
    print(f"GET /reports/punctuality-ranking: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"  - 排名总数: {len(data.get('rankings', []))}")

def main():
    print("\n开始测试所有 API 端点...")
    print(f"基础 URL: {BASE_URL}\n")
    
    try:
        emp_id = test_employees()
        if emp_id:
            test_attendance(emp_id)
            test_leaves(emp_id)
            test_reports(emp_id)
        
        print_section("测试完成")
        print("✅ 所有 API 端点测试完成！")
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
