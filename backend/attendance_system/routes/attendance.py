from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date, timedelta
from attendance_system.models import AttendanceRecord, LeaveRequest, Employee
from attendance_system.database import next_attendance_id, next_leave_id
from attendance_system.utils import calculate_working_hours, determine_status, calculate_leave_days, is_weekend
from attendance_system.enums import AttendanceStatus, LeaveType, Department

# Request models
class CheckInRequest(BaseModel):
    employee_code: str

class CheckOutRequest(BaseModel):
    employee_code: str

class MarkAbsentRequest(BaseModel):
    employee_code: str
    date: str

class LeaveRequest_Schema(BaseModel):
    employee_id: str
    leave_type: str
    start_date: str
    end_date: str
    reason: Optional[str] = None

router = APIRouter(prefix="/attendance", tags=["Attendance"])

async def get_employee(employee_id: str) -> Employee:
    """获取活跃员工"""
    employee = await Employee.get(employee_id)
    if not employee or employee.is_deactivated:
        raise HTTPException(status_code=404, detail="Employee not found or inactive")
    return employee

async def get_attendance_record(attendance_id: int) -> AttendanceRecord:
    """获取出勤记录"""
    record = await AttendanceRecord.get(attendance_id)
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record

async def get_employee_by_code(employee_code: str) -> Employee:
    employee = await Employee.find_one(Employee.employee_code == employee_code.upper())
    if not employee or employee.is_deactivated:
        raise HTTPException(status_code=404, detail="Employee not found or inactive")
    return employee


@router.post("/check-in/{employee_id}", response_model=AttendanceRecord, status_code=201)
async def check_in(employee_id: str, background_tasks: BackgroundTasks, check_in_time: Optional[datetime] = None):
    await get_employee(employee_id)
    today = (check_in_time or datetime.now()).date()
    if is_weekend(today):
        raise HTTPException(400, "Cannot check in on weekend")
    
    existing = await AttendanceRecord.find_one({"employee_id": employee_id, "date": today})
    if existing:
        raise HTTPException(409, "Already checked in today")
    
    record = AttendanceRecord(
        employee_id=employee_id,
        date=today,
        check_in_time=check_in_time or datetime.now(),
        status=determine_status(check_in_time or datetime.now(), None)
    )
    await record.insert()
    
    background_tasks.add_task(print, f"[LOG] Employee {employee_id} checked in at {record.check_in_time}")
    return record


@router.post("/check-in", response_model=AttendanceRecord, status_code=201)
async def check_in_body(request: CheckInRequest, background_tasks: BackgroundTasks):
    """接收employee_code，查找员工后进行签到"""
    employee = await get_employee_by_code(request.employee_code)
    return await check_in(employee_id=str(employee.id), background_tasks=background_tasks)


@router.patch("/check-out/{employee_id}", response_model=AttendanceRecord)
async def check_out(employee_id: str, background_tasks: BackgroundTasks, check_out_time: Optional[datetime] = None):
    await get_employee(employee_id)
    today = (check_out_time or datetime.now()).date()
    record = await AttendanceRecord.find_one({"employee_id": employee_id, "date": today})
    if not record or record.check_out_time:
        raise HTTPException(409, "No check-in record or already checked out")
    
    record.check_out_time = check_out_time or datetime.now()
    record.working_hours = calculate_working_hours(record.check_in_time, record.check_out_time)
    record.status = determine_status(record.check_in_time, record.working_hours)
    await record.save()
    
    background_tasks.add_task(print, f"[LOG] Employee {employee_id} checked out, hours: {record.working_hours}")
    return record


@router.patch("/check-out", response_model=AttendanceRecord)
async def check_out_body(request: CheckOutRequest, background_tasks: BackgroundTasks):
    """接收employee_code，查找员工后进行签退"""
    employee = await get_employee_by_code(request.employee_code)
    return await check_out(employee_id=str(employee.id), background_tasks=background_tasks)


@router.post("/mark-absent", response_model=AttendanceRecord, status_code=201)
async def mark_absent(request: MarkAbsentRequest):
    """\u63a5收employee_code，标记缺勤"""
    employee = await get_employee_by_code(request.employee_code)
    employee_id = str(employee.id)
    
    try:
        d = datetime.strptime(request.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "date format must be YYYY-MM-DD")
    
    if is_weekend(d):
        raise HTTPException(400, "Cannot mark absent on weekend")
    
    existing = await AttendanceRecord.find_one({"employee_id": employee_id, "date": d})
    if existing:
        raise HTTPException(409, "Record already exists")
    
    record = AttendanceRecord(
        employee_id=employee_id,
        date=d,
        status=AttendanceStatus.ABSENT
    )
    await record.insert()
    return record


@router.post("/leaves", response_model=LeaveRequest, status_code=201)
async def create_leave_request(request: LeaveRequest_Schema):
    await get_employee(request.employee_id)
    if datetime.strptime(request.start_date, "%Y-%m-%d").date() > datetime.strptime(request.end_date, "%Y-%m-%d").date():
        raise HTTPException(400, "Start date cannot be after end date")
    
    start_d = datetime.strptime(request.start_date, "%Y-%m-%d").date()
    end_d = datetime.strptime(request.end_date, "%Y-%m-%d").date()
    total_days = calculate_leave_days(start_d, end_d)
    
    leave = LeaveRequest(
        employee_id=request.employee_id,
        leave_type=request.leave_type,
        start_date=start_d,
        end_date=end_d,
        reason=request.reason,
        total_days=total_days
    )
    await leave.insert()
    return request


@router.get("/leaves", response_model=List[LeaveRequest])
async def list_leaves(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    leave_type: Optional[LeaveType] = None,
    skip: int = 0,
    limit: int = 10
):
    query = LeaveRequest.find_all()
    if employee_id:
        query = query.find(LeaveRequest.employee_id == employee_id)
    if status:
        query = query.find(LeaveRequest.status == status)
    if leave_type:
        query = query.find(LeaveRequest.leave_type == leave_type)
    
    leaves = await query.skip(skip).limit(limit).to_list()
    return leaves


@router.get("/leaves/{leave_id}", response_model=LeaveRequest)
async def get_leave(leave_id: int):
    leave = await LeaveRequest.get(leave_id)
    if not leave:
        raise HTTPException(404, "Leave request not found")
    return leave


@router.patch("/leaves/{leave_id}/approve", response_model=LeaveRequest)
async def approve_leave(leave_id: int, approved_by: int, background_tasks: BackgroundTasks):
    leave = await LeaveRequest.get(leave_id)
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.status != "Pending":
        raise HTTPException(400, "Leave already processed")
    
    leave.status = "Approved"
    leave.approved_by = approved_by
    leave.approved_at = datetime.now()
    await leave.save()
    
    # 自动生成 ON_LEAVE 记录
    current = leave.start_date
    while current <= leave.end_date:
        if not is_weekend(current):
            existing = await AttendanceRecord.find_one(
                AttendanceRecord.employee_id == leave.employee_id,
                {"date": current}
            )
            if not existing:
                record = AttendanceRecord(
                    employee_id=leave.employee_id,
                    date=current,
                    status=AttendanceStatus.ON_LEAVE
                )
                await record.insert()
        current += timedelta(days=1)
    
    background_tasks.add_task(print, f"[NOTIFICATION] Leave {leave_id} approved for employee {leave.employee_id}")
    return leave


@router.patch("/leaves/{leave_id}/reject", response_model=LeaveRequest)
async def reject_leave(leave_id: int):
    leave = await LeaveRequest.get(leave_id)
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.status != "Pending":
        raise HTTPException(400, "Leave already processed")
    
    leave.status = "Rejected"
    await leave.save()
    return leave


@router.delete("/leaves/{leave_id}", status_code=204)
async def delete_leave(leave_id: int):
    leave = await LeaveRequest.get(leave_id)
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.status != "Pending":
        raise HTTPException(409, "Cannot cancel non-pending leave request")
    
    await leave.delete()
    return None


@router.get("/", response_model=List[AttendanceRecord])
async def list_attendance(
    employee_id: Optional[str] = None,
    date: Optional[date] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[AttendanceStatus] = None,
    department: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    query = AttendanceRecord.find_all()
    if employee_id:
        query = query.find(AttendanceRecord.employee_id == employee_id)
    if date:
        query = query.find({"date": date})
    if date_from:
        query = query.find({"date": {"$gte": date_from}})
    if date_to:
        query = query.find({"date": {"$lte": date_to}})
    if status:
        query = query.find(AttendanceRecord.status == status)
    if department:
        # 获取该部门员工 ID 列表
        dept_emp_ids = [emp.id async for emp in Employee.find(Employee.department == department, Employee.is_deactivated == False)]
        query = query.find(AttendanceRecord.employee_id.in_(dept_emp_ids))
    
    records = await query.skip(skip).limit(limit).to_list()
    return records


@router.get("/{attendance_id}", response_model=AttendanceRecord)
async def get_attendance_detail(attendance_id: int):
    return await get_attendance_record(attendance_id)


@router.get("/employee/{employee_id}/today", response_model=AttendanceRecord)
async def get_today_attendance(employee_id: str):
    await get_employee(employee_id)
    today = date.today()
    record = await AttendanceRecord.find_one(
        AttendanceRecord.employee_id == employee_id,
        {"date": today}
    )
    if not record:
        raise HTTPException(404, "No attendance record for today")
    return record


@router.get("/employee/{employee_id}/month", response_model=List[AttendanceRecord])
async def get_month_attendance(
    employee_id: str,
    year: Optional[int] = None,
    month: Optional[int] = None
):
    await get_employee(employee_id)
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    # 计算该月的开始和结束日期
    from calendar import monthrange
    last_day = monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)
    
    records = await AttendanceRecord.find(
        AttendanceRecord.employee_id == employee_id,
        {"date": {"$gte": start, "$lte": end}}
    ).to_list()
    return records


@router.put("/{attendance_id}", response_model=AttendanceRecord)
async def update_attendance(attendance_id: int, update_data: AttendanceRecord):
    record = await get_attendance_record(attendance_id)
    update_dict = update_data.model_dump(exclude_unset=True, exclude={"id"})
    
    if "check_in_time" in update_dict or "check_out_time" in update_dict:
        check_in = update_dict.get("check_in_time", record.check_in_time)
        check_out = update_dict.get("check_out_time", record.check_out_time)
        if check_in and check_out:
            update_dict["working_hours"] = calculate_working_hours(check_in, check_out)
            update_dict["status"] = determine_status(check_in, update_dict["working_hours"])
    
    await record.set(update_dict)
    return record


@router.delete("/{attendance_id}", status_code=204)
async def delete_attendance(attendance_id: int):
    record = await get_attendance_record(attendance_id)
    await record.delete()
    return None