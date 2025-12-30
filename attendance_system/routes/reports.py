from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import date, datetime, timedelta
from attendance_system.database import employees, attendance_records
from attendance_system.models import AttendanceRecord
from attendance_system.enums import AttendanceStatus, Department
from fastapi.responses import StreamingResponse
import csv
from io import StringIO

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/daily-summary")
def daily_summary(report_date: date):
    active_emps = [e for e in employees if not e.is_deactivated]
    day_records = [r for r in attendance_records if r.date == report_date]
    
    present = len([r for r in day_records if r.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.HALF_DAY]])
    absent = len([r for r in day_records if r.status == AttendanceStatus.ABSENT])
    late = len([r for r in day_records if r.status == AttendanceStatus.LATE])
    on_leave = len([r for r in day_records if r.status == AttendanceStatus.ON_LEAVE])
    # 当前在岗：已签到但尚未签退的记录
    on_duty = len([r for r in day_records if r.check_in_time is not None and r.check_out_time is None])
    
    absent_names = [e.full_name for e in active_emps if not any(r.employee_id == e.id and r.date == report_date for r in day_records)]
    late_names = [e.full_name for e in active_emps if any(r.employee_id == e.id and r.date == report_date and r.status == AttendanceStatus.LATE for r in day_records)]
    
    return {
        "date": report_date,
        "total_active": len(active_emps),
        "present": present,
        "absent": absent,
        "late": late,
        "on_leave": on_leave,
        "on_duty": on_duty,
        "absent_employees": absent_names,
        "late_employees": late_names
    }

@router.get("/monthly-csv")
def monthly_csv(year: int, month: int):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee Code", "Name", "Date", "Check In", "Check Out", "Hours", "Status"])
    
    for emp in [e for e in employees if not e.is_deactivated]:
        records = [r for r in attendance_records if r.employee_id == emp.id and r.date.year == year and r.date.month == month]
        for r in records:
            writer.writerow([
                emp.employee_code,
                emp.full_name,
                r.date,
                r.check_in_time.strftime("%H:%M") if r.check_in_time else "",
                r.check_out_time.strftime("%H:%M") if r.check_out_time else "",
                round(r.working_hours, 2) if r.working_hours else "",
                r.status.value
            ])
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=attendance_{year}_{month:02d}.csv"}
    )


@router.get("/employee/{employee_id}/monthly-summary")
def get_employee_monthly_summary(
    employee_id: str,
    year: int = Query(None),
    month: int = Query(None)
):
    """获取员工月度统计：工作日数、出勤日、迟到日、缺勤日、请假日、总工时、平均签到时间、出勤率"""
    # 默认当前月
    today = date.today()
    target_year = year or today.year
    target_month = month or today.month
    
    # 找员工
    emp = next((e for e in employees if e.id == employee_id), None)
    if not emp:
        return {"error": "Employee not found"}, 404
    
    # 获取该月日期范围
    month_start = date(target_year, target_month, 1)
    if target_month == 12:
        month_end = date(target_year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(target_year, target_month + 1, 1) - timedelta(days=1)
    
    # 该员工该月所有记录
    records = [r for r in attendance_records if r.employee_id == employee_id and month_start <= r.date <= month_end]
    
    # 统计
    from attendance_system.utils import is_weekend
    working_days = 0
    present_days = 0
    late_days = 0
    absent_days = 0
    leave_days = 0
    total_hours = 0.0
    check_in_times = []
    
    current_date = month_start
    while current_date <= month_end:
        if not is_weekend(current_date):
            working_days += 1
            day_records = [r for r in records if r.date == current_date]
            
            if day_records:
                record = day_records[0]
                if record.status == AttendanceStatus.PRESENT:
                    present_days += 1
                elif record.status == AttendanceStatus.LATE:
                    late_days += 1
                    present_days += 1
                elif record.status == AttendanceStatus.ABSENT:
                    absent_days += 1
                elif record.status == AttendanceStatus.ON_LEAVE:
                    leave_days += 1
                
                # 累计工时
                if record.check_in and record.check_out:
                    hours = (record.check_out - record.check_in).total_seconds() / 3600
                    total_hours += hours
                
                # 收集签到时间
                if record.check_in:
                    check_in_times.append(record.check_in.time())
            else:
                absent_days += 1
        
        current_date += timedelta(days=1)
    
    # 计算平均签到时间
    avg_check_in = None
    if check_in_times:
        from datetime import time
        total_seconds = sum((datetime.combine(date.today(), t) - datetime.combine(date.today(), time(0, 0, 0))).total_seconds() for t in check_in_times)
        avg_seconds = total_seconds / len(check_in_times)
        avg_time = (datetime.combine(date.today(), time(0, 0, 0)) + timedelta(seconds=avg_seconds)).time()
        avg_check_in = avg_time.strftime("%H:%M:%S")
    
    # 出勤率
    attendance_rate = (present_days / working_days * 100) if working_days > 0 else 0
    
    return {
        "employee_id": employee_id,
        "employee_name": emp.full_name,
        "year": target_year,
        "month": target_month,
        "working_days": working_days,
        "present_days": present_days,
        "late_days": late_days,
        "absent_days": absent_days,
        "leave_days": leave_days,
        "total_hours": round(total_hours, 2),
        "avg_check_in_time": avg_check_in,
        "attendance_rate": round(attendance_rate, 2)
    }


@router.get("/department/{department}/attendance")
def get_department_attendance(
    department: str,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """获取部门统计：员工总数、平均出勤率、迟到总数、缺勤总数"""
    # 解析日期
    if date_from:
        start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
    else:
        start_date = date.today().replace(day=1)
    
    if date_to:
        end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
    else:
        end_date = date.today()
    
    # 获取该部门活跃员工
    dept_employees = [e for e in employees if e.department == department and not e.is_deactivated]
    
    if not dept_employees:
        return {"error": "Department not found or no active employees"}, 404
    
    total_employees = len(dept_employees)
    total_late = 0
    total_absent = 0
    attendance_rates = []
    
    from attendance_system.utils import is_weekend
    
    for emp in dept_employees:
        emp_records = [r for r in attendance_records if r.employee_id == emp.id and start_date <= r.date <= end_date]
        
        # 计算该员工出勤率
        working_days = 0
        present_days = 0
        
        current = start_date
        while current <= end_date:
            if not is_weekend(current):
                working_days += 1
                day_rec = next((r for r in emp_records if r.date == current), None)
                if day_rec and day_rec.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]:
                    present_days += 1
            current += timedelta(days=1)
        
        if working_days > 0:
            rate = present_days / working_days * 100
            attendance_rates.append(rate)
        
        # 累计迟到、缺勤
        late_count = len([r for r in emp_records if r.status == AttendanceStatus.LATE])
        absent_count = len([r for r in emp_records if r.status == AttendanceStatus.ABSENT])
        
        total_late += late_count
        total_absent += absent_count
    
    avg_attendance_rate = sum(attendance_rates) / len(attendance_rates) if attendance_rates else 0
    
    return {
        "department": department,
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "total_employees": total_employees,
        "avg_attendance_rate": round(avg_attendance_rate, 2),
        "total_late": total_late,
        "total_absent": total_absent
    }


@router.get("/punctuality-ranking")
def get_punctuality_ranking(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(10)
):
    """获取准时排名：按出勤率降序、迟到次数升序，返回前 limit 名"""
    # 解析日期
    if date_from:
        start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
    else:
        start_date = date.today().replace(day=1)
    
    if date_to:
        end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
    else:
        end_date = date.today()
    
    from attendance_system.utils import is_weekend
    
    rankings = []
    
    for emp in employees:
        if emp.is_deactivated:
            continue
        
        emp_records = [r for r in attendance_records if r.employee_id == emp.id and start_date <= r.date <= end_date]
        
        # 计算统计
        working_days = 0
        present_days = 0
        late_count = 0
        
        current = start_date
        while current <= end_date:
            if not is_weekend(current):
                working_days += 1
                day_rec = next((r for r in emp_records if r.date == current), None)
                if day_rec:
                    if day_rec.status == AttendanceStatus.LATE:
                        late_count += 1
                        present_days += 1
                    elif day_rec.status == AttendanceStatus.PRESENT:
                        present_days += 1
            current += timedelta(days=1)
        
        attendance_rate = (present_days / working_days * 100) if working_days > 0 else 0
        
        rankings.append({
            "employee_id": emp.id,
            "employee_name": emp.full_name,
            "attendance_rate": round(attendance_rate, 2),
            "late_count": late_count,
            "working_days": working_days
        })
    
    # 排序：出勤率降序、迟到升序
    rankings.sort(key=lambda x: (-x["attendance_rate"], x["late_count"]))
    
    return {
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "total_ranked": len(rankings),
        "rankings": rankings[:limit]
    }