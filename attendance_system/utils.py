from datetime import datetime, time, timedelta, date
from typing import Optional
from attendance_system.enums import AttendanceStatus

def calculate_working_hours(check_in: datetime, check_out: datetime) -> float:
    delta = check_out - check_in
    hours = delta.total_seconds() / 3600
    # 扣除午休（如果工作超过6小时）
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