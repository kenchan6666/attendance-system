from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Query
from typing import List, Optional
from datetime import date, timedelta, datetime
from pydantic import BaseModel, Field, ConfigDict
from beanie.odm.fields import PydanticObjectId

from attendance_system.models import LeaveRequest, LeaveCreate, Employee, AttendanceRecord, LeaveRequestWithEmployee, ApproveLeaveRequest
from attendance_system.utils import calculate_leave_days, is_weekend, get_active_employee_by_code, get_active_employee_by_id
from attendance_system.enums import AttendanceStatus, LeaveType


router = APIRouter(prefix="", tags=["Leave Management"])

@router.post("/leaves", response_model=LeaveRequest, status_code=201)
async def create_leave_request(request: LeaveCreate):
    # employee_code
    if request.employee_code:
        employee = await get_active_employee_by_code(request.employee_code.upper())
    elif request.employee_id:
        employee = await Employee.get(request.employee_id)
    else:
        raise HTTPException(status_code=400, detail="必须提供 employee_code 或 employee_id")

    if not employee or employee.is_deactivated:
        raise HTTPException(status_code=404, detail="员工不存在或已离职")

    employee_id = employee.id

    # 计算请假天数
    total_days = calculate_leave_days(request.start_date, request.end_date)

    # 创建请假请求
    leave = LeaveRequest(
        employee_id=employee_id,
        leave_type=request.leave_type,
        start_date=request.start_date,
        end_date=request.end_date,
        total_days=total_days,
        reason=request.reason.strip(),
        status="Pending",
        requested_at=datetime.now()
    )
    await leave.insert()

    return leave


@router.get("/leaves", response_model=List[LeaveRequestWithEmployee])
async def list_leaves(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    leave_type: Optional[LeaveType] = None,
    skip: int = 0,
    limit: int = 10
):
    query = LeaveRequest.find_all()
    if employee_id:
        emp_obj_id = PydanticObjectId(employee_id)
        query = query.find(LeaveRequest.employee_id == emp_obj_id)
    if status:
        query = query.find(LeaveRequest.status == status)
    if leave_type:
        query = query.find(LeaveRequest.leave_type == leave_type)
    
    leaves = await query.skip(skip).limit(limit).to_list()
    
    # 获取所有员工
    all_employees = await Employee.find().to_list()
    emp_map = {str(emp.id): emp for emp in all_employees}
    
    # 转换格式
    result = []
    for leave in leaves:
        emp = emp_map.get(str(leave.employee_id))
        if emp:
            result.append(LeaveRequestWithEmployee(
                id=str(leave.id),
                employee_id=str(leave.employee_id),
                employee_code=emp.employee_code,
                employee_name=emp.full_name,
                leave_type=leave.leave_type,
                start_date=leave.start_date,
                end_date=leave.end_date,
                total_days=leave.total_days,
                reason=leave.reason,
                status=leave.status,
                requested_at=leave.requested_at,
                approved_by=str(leave.approved_by) if leave.approved_by else None,
                approved_at=leave.approved_at
            ))
    
    return result


@router.get("/leaves/{leave_id}", response_model=LeaveRequest)
async def get_leave(leave_id: str):
    try:
        leave = await LeaveRequest.get(PydanticObjectId(leave_id))
    except:
        raise HTTPException(404, "Leave request not found")
    if not leave:
        raise HTTPException(404, "Leave request not found")
    return leave


@router.patch("/leaves/{leave_id}/approve", response_model=LeaveRequestWithEmployee)
async def approve_leave(leave_id: str, request: ApproveLeaveRequest, background_tasks: BackgroundTasks):
    try:
        leave = await LeaveRequest.get(PydanticObjectId(leave_id))
    except:
        raise HTTPException(404, "Leave request not found")
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.status != "Pending":
        raise HTTPException(400, "Leave already processed")
    
    leave.status = "Approved"
    leave.approved_by = request.approved_by
    leave.approved_at = datetime.now()
    await leave.save()
    
    # 生成 ON_LEAVE 记录
    current = leave.start_date
    while current <= leave.end_date:
        if not is_weekend(current):
            existing = await AttendanceRecord.find(
                AttendanceRecord.employee_id == leave.employee_id,
                AttendanceRecord.date == current
            ).first_or_none()
            if not existing:
                record = AttendanceRecord(
                    employee_id=leave.employee_id,
                    date=current,
                    status=AttendanceStatus.ON_LEAVE
                )
                await record.insert()
        current += timedelta(days=1)
    
    # 获取员工
    employee = await Employee.get(leave.employee_id)
    
    background_tasks.add_task(print, f"[NOTIFICATION] Leave {leave_id} approved for employee {leave.employee_id}")
    
    return LeaveRequestWithEmployee(
        id=str(leave.id),
        employee_id=str(leave.employee_id),
        employee_code=employee.employee_code,
        employee_name=employee.full_name,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        total_days=leave.total_days,
        reason=leave.reason,
        status=leave.status,
        requested_at=leave.requested_at,
        approved_by=str(leave.approved_by) if leave.approved_by else None,
        approved_at=leave.approved_at
    )


@router.patch("/leaves/{leave_id}/reject", response_model=LeaveRequestWithEmployee)
async def reject_leave(leave_id: str):
    try:
        leave = await LeaveRequest.get(PydanticObjectId(leave_id))
    except:
        raise HTTPException(404, "Leave request not found")
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.status != "Pending":
        raise HTTPException(400, "Leave already processed")
    
    leave.status = "Rejected"
    await leave.save()
    
    # 获取员工
    employee = await Employee.get(leave.employee_id)
    
    return LeaveRequestWithEmployee(
        id=str(leave.id),
        employee_id=str(leave.employee_id),
        employee_code=employee.employee_code,
        employee_name=employee.full_name,
        leave_type=leave.leave_type,
        start_date=leave.start_date,
        end_date=leave.end_date,
        total_days=leave.total_days,
        reason=leave.reason,
        status=leave.status,
        requested_at=leave.requested_at,
        approved_by=str(leave.approved_by) if leave.approved_by else None,
        approved_at=leave.approved_at
    )


@router.delete("/leaves/{leave_id}", status_code=204)
async def delete_leave(leave_id: str):
    try:
        leave = await LeaveRequest.get(PydanticObjectId(leave_id))
    except:
        raise HTTPException(404, "Leave request not found")
    if not leave:
        raise HTTPException(404, "Leave request not found")
    if leave.status != "Pending":
        raise HTTPException(409, "Cannot cancel non-pending leave request")
    
    await leave.delete()
    return None