from datetime import datetime, time, timedelta, date
from typing import Optional

from fastapi import HTTPException
from attendance_system.enums import AttendanceStatus
from attendance_system.models import Employee

def calculate_working_hours(check_in: datetime, check_out: datetime) -> float:
    delta = check_out - check_in
    hours = delta.total_seconds() / 3600
    # 扣除午休时间
    if hours > 6:
        hours -= 1
    return round(hours, 2)

def determine_status(check_in: Optional[datetime], working_hours: Optional[float]) -> AttendanceStatus:
    if check_in and check_in.time() > time(9, 15):
        return AttendanceStatus.LATE
    if working_hours is not None and working_hours < 4:
        return AttendanceStatus.HALF_DAY
    return AttendanceStatus.PRESENT

def is_weekend(d: date) -> bool:
    return d.weekday() >= 5

def calculate_leave_days(start: date, end: date) -> int:
    days = 0
    current = start
    while current <= end:
        if not is_weekend(current):
            days += 1
        current += timedelta(days=1)
    return days

async def get_active_employee_by_code(employee_code: str) -> Employee:
    """根据员工编号查找员工"""
    employee = await Employee.find_one(Employee.employee_code == employee_code.upper())
    if not employee or employee.is_deactivated:
        raise HTTPException(status_code=404, detail="Employee not found or inactive")
    return employee

async def get_active_employee_by_id(employee_id: str) -> Employee:
    """根据 ObjectId 查找员工"""
    employee = await Employee.get(employee_id)
    if not employee or employee.is_deactivated:
        raise HTTPException(status_code=404, detail="Employee not found or inactive")
    return employee