#!/usr/bin/env python
"""测试前端相关的功能"""
import requests
import json

def test_frontend_workflow():
    """模拟前端的工作流程"""
    API = "http://127.0.0.1:8000"
    
    print("=== 1. 获取员工列表 ===")
    r = requests.get(f"{API}/employees")
    employees = r.json()
    print(f"✓ 获取 {len(employees)} 个活跃员工")
    if employees:
        for i, emp in enumerate(employees[:3]):
            print(f"  {i+1}. {emp['full_name']} (ID: {emp['_id']})")
    
    if not employees:
        print("✗ 没有员工，创建一个测试员工...")
        import random
        code = f"EMP{random.randint(1, 999):03d}"
        r = requests.post(f"{API}/employees", json={
            "full_name": "李四",
            "employee_code": code,
            "email": "lisi@test.com",
            "department": "IT",
            "position": "Engineer",
            "hire_date": "2025-01-01"
        })
        if r.status_code == 201:
            emp = r.json()
            print(f"✓ 创建成功: {emp['full_name']} (ID: {emp['_id']})")
            employees = [emp]
        else:
            print(f"✗ 创建失败: {r.text}")
            return
    
    # 使用第一个员工进行签到测试
    emp_id = employees[0]['_id']
    emp_name = employees[0]['full_name']
    
    print("\n=== 2. 测试签到 ===")
    print(f"使用员工: {emp_name} (ID: {emp_id})")
    r = requests.post(f"{API}/attendance/check-in", 
                      json={"employee_id": emp_id},
                      headers={"Content-Type": "application/json"})
    print(f"Status: {r.status_code}")
    if r.status_code == 201:
        record = r.json()
        print(f"✓ 签到成功")
        print(f"  状态: {record['status']}")
        print(f"  时间: {record['check_in_time']}")
    else:
        print(f"✗ 签到失败: {r.text}")
        return
    
    print("\n=== 3. 测试签退 ===")
    r = requests.patch(f"{API}/attendance/check-out",
                       json={"employee_id": emp_id},
                       headers={"Content-Type": "application/json"})
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        record = r.json()
        print(f"✓ 签退成功")
        print(f"  工时: {record.get('working_hours', 'N/A')} 小时")
        print(f"  状态: {record['status']}")
    else:
        print(f"✗ 签退失败: {r.text}")

if __name__ == "__main__":
    test_frontend_workflow()
