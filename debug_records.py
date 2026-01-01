import asyncio
import os
from datetime import date
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from attendance_system.models import AttendanceRecord, Employee, LeaveRequest

async def debug():
    # 连接数据库
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017/attendance_db")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.attendance_db
    
    await init_beanie(
        database=db,
        document_models=[Employee, AttendanceRecord, LeaveRequest]
    )
    
    # 查询2025-12-31的记录
    today = date(2025, 12, 31)
    today_records = await AttendanceRecord.find({"date": today}).to_list()
    print(f"=== 2025-12-31 出勤记录 (今天) ===")
    print(f"总共找到: {len(today_records)} 条记录")
    
    # 统计各种状态
    status_count = {}
    present_count = 0
    late_count = 0
    absent_count = 0
    half_day_count = 0
    
    for r in today_records:
        status_key = str(r.status)
        status_count[status_key] = status_count.get(status_key, 0) + 1
        
        if 'PRESENT' in status_key:
            present_count += 1
        elif 'LATE' in status_key:
            late_count += 1
        elif 'ABSENT' in status_key:
            absent_count += 1
        elif 'HALF_DAY' in status_key:
            half_day_count += 1
    
    print(f"出勤(PRESENT): {present_count}")
    print(f"迟到(LATE): {late_count}")
    print(f"缺勤(ABSENT): {absent_count}")
    print(f"半天(HALF_DAY): {half_day_count}")
    print(f"完整统计: {status_count}")
    
    # 显示活跃员工总数
    all_employees = await Employee.find(Employee.is_deactivated == False).to_list()
    print(f"\n活跃员工总数: {len(all_employees)}")
    
    # 计算缺勤人数
    recorded_emp_ids = set(r.employee_id for r in today_records)
    absent_by_no_record = len(all_employees) - len(recorded_emp_ids)
    print(f"有记录的员工: {len(recorded_emp_ids)}")
    print(f"完全没记录的员工(缺勤): {absent_by_no_record}")

asyncio.run(debug())
