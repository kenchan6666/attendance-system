from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from pydantic import BaseModel, model_validator, Field, field_validator
from typing import List, Optional
from datetime import datetime, date, timedelta
from beanie.odm.fields import PydanticObjectId
from attendance_system.models import AttendanceRecord, LeaveRequest, Employee, CheckInRequest, CheckOutRequest, MarkAbsentRequest, AttendanceRecordWithEmployee
from attendance_system.database import next_attendance_id, next_leave_id
from attendance_system.utils import calculate_working_hours, determine_status, is_weekend, get_active_employee_by_code
from attendance_system.enums import AttendanceStatus, LeaveType, Department

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

@router.post("/check-in/{employee_id}", response_model=AttendanceRecord, status_code=201)
async def check_in(employee_id: str, background_tasks: BackgroundTasks, check_in_time: Optional[datetime] = None):
    await get_employee(employee_id)
    today = (check_in_time or datetime.now()).date()
    if is_weekend(today):
        raise HTTPException(400, "Cannot check in on weekend")
    
    emp_obj_id = PydanticObjectId(employee_id)
    existing = await AttendanceRecord.find(AttendanceRecord.employee_id == emp_obj_id, AttendanceRecord.date == today).first_or_none()
    if existing:
        raise HTTPException(409, "Already checked in today")
    
    record = AttendanceRecord(
        employee_id=emp_obj_id,
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
    employee = await get_active_employee_by_code(request.employee_code)
    return await check_in(employee_id=str(employee.id), background_tasks=background_tasks)


@router.patch("/check-out", response_model=AttendanceRecord)
async def check_out(request: CheckOutRequest, background_tasks: BackgroundTasks):
    """使用 employee_code 签退"""
    # 根据 employee_code 查找员工
    employee = await get_active_employee_by_code(request.employee_code)
    employee_id = PydanticObjectId(str(employee.id))
    
    today = datetime.now().date()
    
    # 查询今天的签到记录
    record = await AttendanceRecord.find(AttendanceRecord.employee_id == employee_id, AttendanceRecord.date == today).first_or_none()
    
    if not record or record.check_out_time:
        raise HTTPException(409, "No check-in record or already checked out")
    
    # 更新签退时间和工时
    record.check_out_time = datetime.now()
    record.working_hours = calculate_working_hours(record.check_in_time, record.check_out_time)
    record.status = determine_status(record.check_in_time, record.working_hours)
    await record.save()
    
    background_tasks.add_task(print, f"[LOG] Employee {request.employee_code} checked out, hours: {record.working_hours}")
    return record


@router.post("/mark-absent", response_model=AttendanceRecord, status_code=201)
async def mark_absent(request: MarkAbsentRequest):
    """接收employee_code，标记缺勤"""
    employee = await get_active_employee_by_code(request.employee_code)
    employee_id = PydanticObjectId(str(employee.id))
    
    try:
        d = datetime.strptime(request.date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(400, "date format must be YYYY-MM-DD")
    
    if is_weekend(d):
        raise HTTPException(400, "Cannot mark absent on weekend")
    
    existing = await AttendanceRecord.find(AttendanceRecord.employee_id == employee_id, AttendanceRecord.date == d).first_or_none()
    if existing:
        raise HTTPException(409, "Record already exists")
    
    record = AttendanceRecord(
        employee_id=employee_id,
        date=d,
        status=AttendanceStatus.ABSENT
    )
    await record.insert()
    return record

@router.get("/", response_model=List[AttendanceRecordWithEmployee])
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
    """获取考勤记录，包含员工信息"""
    query = AttendanceRecord.find_all()
    if employee_id:
        query = query.find(AttendanceRecord.employee_id == employee_id)
    if date:
        query = query.find(AttendanceRecord.date == date)
    if date_from:
        query = query.find(AttendanceRecord.date >= date_from)
    if date_to:
        query = query.find(AttendanceRecord.date <= date_to)
    if status:
        query = query.find(AttendanceRecord.status == status)
    if department:
        # 获取该部门员工 ID 列表
        dept_emps = await Employee.find(Employee.department == department, Employee.is_deactivated == False).to_list()
        dept_emp_ids = [emp.id for emp in dept_emps]
        query = query.find(AttendanceRecord.employee_id.in_(dept_emp_ids))
    
    records = await query.skip(skip).limit(limit).to_list()
    
    # 获取所有员工信息
    all_employees = await Employee.find().to_list()
    emp_map = {str(emp.id): emp for emp in all_employees}
    
    # 将记录转换为包含员工信息的格式
    result = []
    for record in records:
        emp = emp_map.get(str(record.employee_id))
        result.append(AttendanceRecordWithEmployee(
            id=str(record.id),
            employee_id=str(record.employee_id),
            employee_code=emp.employee_code if emp else "N/A",
            employee_name=emp.full_name if emp else "未知",
            date=record.date,
            check_in_time=record.check_in_time,
            check_out_time=record.check_out_time,
            status=record.status,
            working_hours=record.working_hours,
            notes=record.notes
        ))
    
    return result


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