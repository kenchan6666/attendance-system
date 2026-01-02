from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from beanie import Document, Indexed, PydanticObjectId
from datetime import date, datetime
from typing import Optional
from attendance_system.enums import Department, AttendanceStatus, LeaveType
import re

# Employee 模型
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
    
    class Settings:
        name = "employees"

class EmployeeCreate(EmployeeBase):
    pass

class Employee(EmployeeBase, Document):
    is_deactivated: bool = False
    created_at: datetime = Field(default_factory=datetime.now)

    class Settings:
        name = "employees"

class EmployeeUpdate(BaseModel):
    employee_code: Optional[str] = Field(None, max_length=6)
    full_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    department: Optional[Department] = None
    position: Optional[str] = Field(None, max_length=50)
    hire_date: Optional[date] = None

    @field_validator('employee_code')
    @classmethod
    def validate_code(cls, v: Optional[str]):
        if v is not None:
            if not re.match(r'^EMP\d{3}$', v):
                raise ValueError('Employee code must be in format EMP001')
            return v.upper()
        return v

# AttendanceRecord 模型
class AttendanceRecord(Document):
    employee_id: PydanticObjectId
    date: Indexed(date)  # type: ignore
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: AttendanceStatus = AttendanceStatus.PRESENT
    working_hours: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=200)

    class Settings:
        name = "attendance_records"

class AttendanceRecordWithEmployee(BaseModel):
    id: str
    employee_id: str
    employee_code: str
    employee_name: str
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    status: AttendanceStatus
    working_hours: Optional[float] = None
    notes: Optional[str] = None


class LeaveRequest(Document):
    employee_id: PydanticObjectId
    leave_type: LeaveType
    start_date: date
    end_date: date
    total_days: int
    reason: str = Field(..., max_length=300)
    status: str = "Pending"
    requested_at: datetime = Field(default_factory=datetime.now)
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None

    class Settings:
        name = "leave_requests"


class LeaveCreate(BaseModel):
    employee_id: Optional[str] = Field(None)
    employee_code: Optional[str] = Field(None)
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(..., max_length=300, min_length=1)

    @field_validator("leave_type", mode="before")
    @classmethod
    def parse_leave_type(cls, v):
        if isinstance(v, str):
            try:
                return LeaveType(v.strip())
            except ValueError:
                raise ValueError(f"无效的请假类型: {v}")
        return v

    @model_validator(mode="after")
    def validate_request(self):
        if not self.employee_id and not self.employee_code:
            raise ValueError("必须提供 employee_id 或 employee_code 中的一个")
        if self.employee_id and self.employee_code:
            raise ValueError("不能同时提供 employee_id 和 employee_code")
        if self.start_date > self.end_date:
            raise ValueError("开始日期不能晚于结束日期")
        if not self.reason.strip():
            raise ValueError("请假理由不能为空")
        return self
    
class ApproveLeaveRequest(BaseModel):
    approved_by: int

class LeaveRequestWithEmployee(BaseModel):
    id: Optional[str] = None
    employee_id: str
    employee_code: str
    employee_name: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    total_days: int
    reason: str
    status: str
    requested_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
class CheckInRequest(BaseModel):
    employee_code: str

class CheckOutRequest(BaseModel):
    employee_code: str

class MarkAbsentRequest(BaseModel):
    employee_code: str
    date: str  # YYYY-MM-DD
