from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Path, status, Depends

from attendance_system.database import employees, next_employee_id
from attendance_system.models import Employee
from attendance_system.models import EmployeeCreate

router = APIRouter()


# 验证依赖函数
def validate_employee_id(employee_id: int) -> Employee:
    """验证员工 ID 是否存在"""
    emp = next((e for e in employees if e.id == employee_id and not e.is_deactivated), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.post("/", response_model=Employee, status_code=status.HTTP_201_CREATED)
def create_employee(employee: EmployeeCreate):
    """
    创建新员工
    
    - **name**: 员工姓名 (必填)
    - **employee_code**: 员工代码，格式 EMP\\d{3} (必填)
    - **email**: 电子邮箱 (必填)
    - **department**: 部门 (必填)
    - **position**: 职位 (可选)
    
    返回: 201 Created - 新员工对象
    """
    if any(e.employee_code == employee.employee_code for e in employees):
        raise HTTPException(status_code=409, detail="Employee code already exists")
    
    global next_employee_id
    new_employee = Employee(
        **employee.model_dump(),
        id=next_employee_id,
        created_at=datetime.now()
    )
    employees.append(new_employee)
    next_employee_id += 1
    return new_employee


@router.get("/", response_model=List[Employee])
def get_employees(
    department: Optional[str] = Query(None, description="按部门过滤"),
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的最大记录数"),
):
    """
    获取员工列表
    
    支持按部门过滤和分页查询。
    
    - **department**: 可选部门名称过滤
    - **skip**: 分页偏移
    - **limit**: 分页大小 (最多 100)
    
    返回: 员工列表
    """
    result = [
        e
        for e in employees
        if (department is None or e.department == department)
        and not e.is_deactivated
    ]
    return result[skip : skip + limit]


@router.get("/{employee_id}", response_model=Employee)
def get_employee(employee: Employee = Depends(validate_employee_id)):
    """
    获取指定员工详情
    
    - **employee_id**: 员工 ID
    
    返回: 员工对象；404 如果员工不存在
    """
    return employee


@router.get("/code/{employee_code}", response_model=Employee)
def get_employee_by_code(
    employee_code: str = Path(..., description="员工代码，格式 EMP\\d{3}")
):
    """
    按员工代码获取员工
    
    - **employee_code**: 员工代码 (格式: EMP001, EMP002 等)
    
    返回: 员工对象；404 如果不存在
    """
    emp = next((e for e in employees if e.employee_code == employee_code and not e.is_deactivated), None)
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.put("/{employee_id}", response_model=Employee)
def update_employee(
    employee_id: int,
    updated: Employee,
    _emp: Employee = Depends(validate_employee_id)
):
    """
    更新员工信息
    
    - **employee_id**: 员工 ID
    - **updated**: 更新的员工数据
    
    返回: 更新后的员工对象；404 如果员工不存在
    """
    if updated.employee_code != _emp.employee_code:
        raise HTTPException(status_code=400, detail="Cannot change employee_code")

    index = employees.index(_emp)
    updated_dict = updated.model_copy(
        update={"id": employee_id, "created_at": _emp.created_at}
    )
    employees[index] = updated_dict
    return updated_dict


@router.patch("/{employee_id}/deactivate", response_model=Employee)
def deactivate_employee(
    employee_id: int,
    _emp: Employee = Depends(validate_employee_id)
):
    """
    停用员工（不删除数据，只标记为已停用）
    
    - **employee_id**: 员工 ID
    
    返回: 更新后的员工对象（is_deactivated=true）
    """
    index = employees.index(_emp)
    updated = _emp.model_copy(update={"is_deactivated": True})
    employees[index] = updated
    return updated


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee(
    employee_id: int,
    _emp: Employee = Depends(validate_employee_id)
):
    """
    删除员工（逻辑删除，标记为已停用）
    
    - **employee_id**: 员工 ID
    
    返回: 204 No Content；404 如果员工不存在
    """
    index = employees.index(_emp)
    employees[index] = _emp.model_copy(update={"is_deactivated": True})
    return None
