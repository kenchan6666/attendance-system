from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Optional
from datetime import datetime, date
from attendance_system.models import AttendanceRecord, LeaveRequest, Employee
from attendance_system.database import attendance_records, leave_requests, next_attendance_id, next_leave_id, employees
from attendance_system.utils import calculate_working_hours, determine_status, calculate_leave_days, is_weekend
from attendance_system.enums import AttendanceStatus

router = APIRouter(prefix="/attendance", tags=["Attendance"])

def find_employee(employee_id: int):
    emp = next((e for e in employees if e.id == employee_id and not e.is_deactivated), None)
    if not emp:
        raise HTTPException(404, "Employee not found or inactive")
    return emp

@router.post("/check-in/{employee_id}", response_model=AttendanceRecord, status_code=201)
def check_in(employee_id: int, background_tasks: BackgroundTasks, check_in_time: Optional[datetime] = None):
    """
    员工签到
    
    创建今日出勤记录，自动计算是否迟到。
    
    - **employee_id**: 员工 ID (路径参数)
    - **check_in_time**: 签到时间 (可选，默认当前时间)
    
    返回: 201 Created - 新的出勤记录
    
    错误码:
    - 400: 周末不能签到
    - 404: 员工不存在或已停用
    - 409: 今日已签到
    """
    find_employee(employee_id)
    today = (check_in_time or datetime.now()).date()
    if is_weekend(today):
        raise HTTPException(400, "Cannot check in on weekend")
    
    if any(r.employee_id == employee_id and r.date == today for r in attendance_records):
        raise HTTPException(409, "Already checked in today")
    
    global next_attendance_id
    record = AttendanceRecord(
        id=next_attendance_id,
        employee_id=employee_id,
        date=today,
        check_in_time=check_in_time or datetime.now(),
        status=determine_status(check_in_time or datetime.now(), None)
    )
    attendance_records.append(record)
    next_attendance_id += 1
    
    background_tasks.add_task(print, f"[LOG] Employee {employee_id} checked in at {record.check_in_time}")
    return record


@router.post("/check-in", response_model=AttendanceRecord, status_code=201)
def check_in_body(payload: dict, background_tasks: BackgroundTasks):
    """
    员工签到 (JSON 体版本)
    
    支持前端通过 JSON 请求体发送签到请求。
    
    请求体:
    ```json
    {
      "employee_id": 1
    }
    ```
    
    返回: 201 Created - 新的出勤记录
    """
    employee_id = payload.get("employee_id")
    if employee_id is None:
        raise HTTPException(400, "employee_id is required in body")
    return check_in(employee_id=employee_id, background_tasks=background_tasks)

@router.patch("/check-out/{employee_id}", response_model=AttendanceRecord)
def check_out(employee_id: int, background_tasks: BackgroundTasks, check_out_time: Optional[datetime] = None):
    find_employee(employee_id)
    today = (check_out_time or datetime.now()).date()
    record = next((r for r in attendance_records if r.employee_id == employee_id and r.date == today), None)
    if not record or record.check_out_time:
        raise HTTPException(409, "No check-in record or already checked out")
    
    record.check_out_time = check_out_time or datetime.now()
    record.working_hours = calculate_working_hours(record.check_in_time, record.check_out_time)
    record.status = determine_status(record.check_in_time, record.working_hours)
    
    background_tasks.add_task(print, f"[LOG] Employee {employee_id} checked out at {record.check_out_time}, hours: {record.working_hours}")
    return record


# 兼容前端通过 JSON body 发送 {"employee_id": <id>} 的签退请求
@router.patch("/check-out", response_model=AttendanceRecord)
def check_out_body(payload: dict, background_tasks: BackgroundTasks):
    employee_id = payload.get("employee_id")
    if employee_id is None:
        raise HTTPException(400, "employee_id is required in body")
    return check_out(employee_id=employee_id, background_tasks=background_tasks)

# @router.post("/mark-absent/{employee_id}")
# def mark_absent(employee_id: int, date: date = Query(..., description="Format: YYYY-MM-DD")):
#     find_employee(employee_id)
#     if is_weekend(date):
#         raise HTTPException(400, "Cannot mark absent on weekend")
#     if any(r.employee_id == employee_id and r.date == date for r in attendance_records):
#         raise HTTPException(409, "Record already exists")
    
#     global next_attendance_id
#     record = AttendanceRecord(
#         id=next_attendance_id,
#         employee_id=employee_id,
#         date=date,
#         status=AttendanceStatus.ABSENT
#     )
#     attendance_records.append(record)
#     next_attendance_id += 1
#     return record


# 兼容前端通过 JSON body 发送 {"employee_id": <id>, "date": "YYYY-MM-DD"} 的请求
@router.post("/mark-absent")
def mark_absent_body(payload: dict):
    """支持前端发送 JSON: {"employee_id": 1, "date": "2025-01-01"} 的情况"""
    employee_id = payload.get("employee_id")
    date_str = payload.get("date")
    
    if employee_id is None or date_str is None:
        raise HTTPException(400, "employee_id and date are required")
    
    # 将字符串日期转换为 date 对象
    from datetime import datetime as dt
    try:
        date_obj = dt.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "date format must be YYYY-MM-DD")
    
    # 复用已有逻辑
    find_employee(employee_id)
    if is_weekend(date_obj):
        raise HTTPException(400, "Cannot mark absent on weekend")
    if any(r.employee_id == employee_id and r.date == date_obj for r in attendance_records):
        raise HTTPException(409, "Record already exists")
    
    global next_attendance_id
    record = AttendanceRecord(
        id=next_attendance_id,
        employee_id=employee_id,
        date=date_obj,
        status=AttendanceStatus.ABSENT
    )
    attendance_records.append(record)
    next_attendance_id += 1
    return record

@router.post("/leaves", response_model=LeaveRequest, status_code=201, tags=["Leaves"])
def create_leave_request(request: LeaveRequest):
    find_employee(request.employee_id)
    if request.start_date > request.end_date:
        raise HTTPException(400, "Start date cannot be after end date")
    
    request.total_days = calculate_leave_days(request.start_date, request.end_date)
    global next_leave_id
    new_request = request.model_copy(update={
        "id": next_leave_id,
        "requested_at": datetime.now()
    })
    leave_requests.append(new_request)
    next_leave_id += 1
    return new_request


@router.get("/leaves", response_model=List[LeaveRequest], tags=["Leaves"])
def list_leaves(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    leave_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    """List all leave requests with optional filters"""
    results = leave_requests
    if employee_id:
        results = [r for r in results if r.employee_id == employee_id]
    if status:
        results = [r for r in results if r.status == status]
    if leave_type:
        results = [r for r in results if r.leave_type == leave_type]
    return results[skip:skip + limit]


@router.get("/leaves/{leave_id}", response_model=LeaveRequest, tags=["Leaves"])
def get_leave(leave_id: int):
    """Get specific leave request"""
    leave = next((l for l in leave_requests if l.id == leave_id), None)
    if not leave:
        raise HTTPException(404, "Leave request not found")
    return leave


@router.patch("/leaves/{leave_id}/approve", response_model=LeaveRequest, tags=["Leaves"])
def approve_leave(leave_id: int, approved_by: int, background_tasks: BackgroundTasks):
    leave = next((l for l in leave_requests if l.id == leave_id), None)
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.status != "Pending":
        raise HTTPException(400, "Leave already processed")
    
    leave.status = "Approved"
    leave.approved_by = approved_by
    leave.approved_at = datetime.now()
    
    # 自动为请假期间的工作日生成 ON_LEAVE 记录
    current = leave.start_date
    while current <= leave.end_date:
        if not is_weekend(current):
            # 检查是否已有记录
            existing = next((r for r in attendance_records if r.employee_id == leave.employee_id and r.date == current), None)
            if not existing:
                global next_attendance_id
                record = AttendanceRecord(
                    id=next_attendance_id,
                    employee_id=leave.employee_id,
                    date=current,
                    status=AttendanceStatus.ON_LEAVE
                )
                attendance_records.append(record)
                next_attendance_id += 1
        current += timedelta(days=1)
    
    background_tasks.add_task(print, f"[NOTIFICATION] Leave {leave_id} approved for employee {leave.employee_id}")
    return leave


@router.patch("/leaves/{leave_id}/reject", response_model=LeaveRequest, tags=["Leaves"])
def reject_leave(leave_id: int):
    """Reject leave request"""
    leave = next((l for l in leave_requests if l.id == leave_id), None)
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.status != "Pending":
        raise HTTPException(400, "Leave already processed")
    
    leave.status = "Rejected"
    return leave


@router.delete("/leaves/{leave_id}", status_code=204, tags=["Leaves"])
def delete_leave(leave_id: int):
    """Cancel leave request (only if Pending)"""
    leave = next((l for l in leave_requests if l.id == leave_id), None)
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.status != "Pending":
        raise HTTPException(409, "Cannot cancel non-pending leave request")
    
    leave_requests.remove(leave)
    return None


def get_attendance(attendance_id: int) -> AttendanceRecord:
    record = next((r for r in attendance_records if r.id == attendance_id), None)
    if not record:
        raise HTTPException(404, "Attendance record not found")
    return record

@router.get("/", response_model=List[AttendanceRecord])
def list_attendance(
    employee_id: Optional[int] = None,
    date: Optional[date] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    status: Optional[AttendanceStatus] = None,
    department: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    results = attendance_records
    if employee_id:
        results = [r for r in results if r.employee_id == employee_id]
    if date:
        results = [r for r in results if r.date == date]
    if date_from:
        results = [r for r in results if r.date >= date_from]
    if date_to:
        results = [r for r in results if r.date <= date_to]
    if status:
        results = [r for r in results if r.status == status]
    if department:
        emp_ids = [e.id for e in employees if e.department == department and not e.is_deactivated]
        results = [r for r in results if r.employee_id in emp_ids]
    return results[skip:skip + limit]

@router.get("/{attendance_id}", response_model=AttendanceRecord)
def get_attendance_detail(attendance_id: int):
    return get_attendance(attendance_id)

@router.get("/employee/{employee_id}/today", response_model=AttendanceRecord)
def get_today_attendance(employee_id: int):
    find_employee(employee_id)
    today = date.today()
    record = next((r for r in attendance_records if r.employee_id == employee_id and r.date == today), None)
    if not record:
        raise HTTPException(404, "No attendance record for today")
    return record

@router.get("/employee/{employee_id}/month", response_model=List[AttendanceRecord])
def get_month_attendance(
    employee_id: int,
    year: Optional[int] = None,
    month: Optional[int] = None
):
    find_employee(employee_id)
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    records = [r for r in attendance_records if r.employee_id == employee_id and r.date.year == year and r.date.month == month]
    return records

@router.put("/{attendance_id}", response_model=AttendanceRecord)
def update_attendance(attendance_id: int, update_data: AttendanceRecord):
    record = get_attendance(attendance_id)
    if update_data.check_in_time or update_data.check_out_time:
        check_in = update_data.check_in_time or record.check_in_time
        check_out = update_data.check_out_time or record.check_out_time
        if check_in and check_out:
            update_data.working_hours = calculate_working_hours(check_in, check_out)
            update_data.status = determine_status(check_in, update_data.working_hours)
    index = attendance_records.index(record)
    updated = record.model_copy(update=update_data.model_dump(exclude_unset=True))
    attendance_records[index] = updated
    return updated


@router.delete("/{attendance_id}", status_code=204)
def delete_attendance(attendance_id: int):
    """Delete attendance record"""
    record = get_attendance(attendance_id)
    attendance_records.remove(record)
    return None