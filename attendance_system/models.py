from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from typing import Optional
from attendance_system.enums import Department, AttendanceStatus, LeaveType
import re

# Employee 相关模型
class EmployeeBase(BaseModel):
    employee_code: str = Field(..., max_length=6)
    full_name: str = Field(..., max_length=100)
    email: EmailStr
    department: Department
    position: str = Field(..., max_length=50)
    hire_date: date

    @field_validator('employee_code')
    @classmethod
    def validate_code(cls, v: str):
        if not re.match(r'^EMP\d{3}$', v):
            raise ValueError('Employee code must be in format EMP001')
        return v.upper()

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase):
    id: int
    is_deactivated: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

# Attendance 相关模型
class AttendanceRecord(BaseModel):
    id: int
    employee_id: int
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    working_hours: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=200)

# Leave 相关模型
class LeaveRequest(BaseModel):
    id: int
    employee_id: int
    leave_type: LeaveType
    start_date: date
    end_date: date
    total_days: int
    reason: str = Field(..., max_length=300)
    status: str = "Pending"
    requested_at: datetime = Field(default_factory=datetime.now)
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None