from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Path, status, Depends

from attendance_system.database import next_employee_id
from attendance_system.models import Employee
from attendance_system.models import EmployeeCreate
from attendance_system.enums import Department

router = APIRouter()


# 验证依赖函数
async def validate_employee_id(employee_id: str) -> Employee:
    """验证员工 ID 是否存在"""
    employees = await Employee.get(employee_id)
    emp = next((e for e in employees if str(e.id) == str(employee_id) and not e.is_deactivated), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.post("/", response_model=Employee, status_code=status.HTTP_201_CREATED)
async def create_employee(employee: EmployeeCreate):
    """
    创建新员工
    """
    # 检查员工编号唯一性
    existing = await Employee.find_one(Employee.employee_code == employee.employee_code)
    if existing:
        raise HTTPException(status_code=409, detail="Employee code already exists")
    
    # 创建新员工对象并插入数据库
    new_employee = Employee(**employee.model_dump())
    await new_employee.insert() #保存到数据库

    new_employee.id = str(new_employee.id) if new_employee.id else None
    
    return new_employee


@router.get("/", response_model=List[Employee])
async def get_employees(
    department: Optional[Department] = None,
    is_active: Optional[bool] = Query(True, description="是否在职"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    获取员工列表，支持过滤和分页
    """
    # 构建查询
    query = Employee.find(Employee.is_deactivated == False) if is_active else Employee.find(Employee.is_deactivated == True)
    if department:
        query = query.find(Employee.department == department)
    
    # 执行查询 + 分页
    employees = await query.skip(skip).limit(limit).to_list()
    return employees


@router.get("/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str):
    """
    获取单个员工详情
    """
    employee = await Employee.get(employee_id)
    if not employee or employee.is_deactivated:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.get("/code/{employee_code}", response_model=Employee)
async def get_employee_by_code(employee_code: str):
    """
    按员工编号查询
    """
    employee = await Employee.find_one(Employee.employee_code == employee_code)
    if not employee or employee.is_deactivated:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@router.put("/{employee_id}", response_model=Employee)
async def update_employee(employee_id: str, updated: EmployeeCreate):
    """
    更新员工信息（不能修改 employee_code）
    """
    employee = await Employee.get(employee_id)
    if not employee or employee.is_deactivated:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    if updated.employee_code != employee.employee_code:
        raise HTTPException(status_code=400, detail="Cannot change employee_code")
    
    # 更新字段
    update_data = updated.model_dump(exclude_unset=True)
    await employee.set(update_data)
    return employee


@router.patch("/{employee_id}/deactivate", response_model=Employee)
async def deactivate_employee(employee_id: str):
    """
    停用员工
    """
    employee = await Employee.get(employee_id)
    if not employee or employee.is_deactivated:
        raise HTTPException(status_code=404, detail="Employee not found or already deactivated")
    
    await employee.set({"is_deactivated": True})
    return employee



@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(employee_id: str):
    """
    软删除员工
    """
    employee = await Employee.get(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    await employee.set({"is_deactivated": True})
    return None