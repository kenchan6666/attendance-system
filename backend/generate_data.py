import asyncio
import os
from datetime import date, timedelta
from random import choice, randint
from typing import List

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from attendance_system.models import Employee, EmployeeCreate, LeaveRequest, LeaveCreate, AttendanceRecord
from attendance_system.enums import Department, LeaveType
from attendance_system.utils import calculate_leave_days

# MongoDB URL
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/attendance_db")

# 名字列表（15 个，30 个员工重复使用）
NAMES = [
    "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen"
]

POSITIONS = ["Developer", "Designer", "Manager", "Analyst", "Tester", "HR", "Sales", "Marketing", "Finance", "Operations"]

REASONS = ["生病需要休息", "家庭事务", "年假", "个人原因", "参加婚礼", "旅游", "身体不适", "照顾家人"]

async def main():
    print("connecting MongoDB...")
    try:
        client = AsyncIOMotorClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        await client.server_info()
        print("MongoDB connected!")
    except Exception as e:
        print(f"connection failed: {e}")
        return

    db_name = MONGODB_URL.split("/")[-1].split("?")[0] or "attendance_db"
    db = client[db_name]

    print("Initializing Beanie...")
    try:
        await init_beanie(
            database=db,
            document_models=[Employee, AttendanceRecord, LeaveRequest]
        )
        print("Beanie successfully initialized!")
    except Exception as e:
        print(f"Beanie initialization failed: {e}")
        return

    print("start generating data...")

    for i in range(1, 11):
        emp_code = f"EMP{i:03d}"
        name = NAMES[(i - 1) % len(NAMES)].capitalize()
        email = f"{name.lower()}{i}@company.com"
        department = choice(list(Department))
        position = choice(POSITIONS)
        hire_date = date(2024, randint(1, 12), randint(1, 28))

        # 检查是否已存在
        existing = await Employee.find_one({"employee_code": emp_code})
        if existing:
            print(f"{emp_code} exits, skipping")
            employee = existing
        else:
            emp_data = EmployeeCreate(
                employee_code=emp_code,
                full_name=name,
                email=email,
                department=department,
                position=position,
                hire_date=hire_date
            )
            employee = Employee(**emp_data.model_dump())
            await employee.insert()

        # 前 10 个员工生成 1-3 条请假记录
        if i <= 10:
            num_leaves = randint(1, 3)
            for _ in range(num_leaves):
                leave_type = choice(list(LeaveType))
                days_ago = randint(0, 60)
                start_date = date.today() - timedelta(days=days_ago)
                duration = randint(1, 5)
                end_date = start_date + timedelta(days=duration - 1)

                existing_leave = await LeaveRequest.find_one({
                    "employee_id": employee.id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                if existing_leave:
                    continue

                total_days = calculate_leave_days(start_date, end_date)

                leave = LeaveRequest(
                    employee_id=employee.id,
                    leave_type=leave_type,
                    start_date=start_date,
                    end_date=end_date,
                    total_days=total_days,
                    reason=choice(REASONS),
                    status="Pending"
                )
                await leave.insert()

    print("\n30 finidhed!")

if __name__ == "__main__":
    asyncio.run(main())