from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import date, datetime, timedelta
from attendance_system.models import AttendanceRecord, Employee
from attendance_system.enums import AttendanceStatus, Department
from fastapi.responses import StreamingResponse
import csv
from io import StringIO

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/daily-summary")
async def daily_summary(report_date: date):
    active_emps = await Employee.find(Employee.is_deactivated == False).to_list()
    day_records = await AttendanceRecord.find({"date": report_date}).to_list()

    # 统计数量
    present = len([r for r in day_records if r.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]])
    absent = len([r for r in day_records if r.status == AttendanceStatus.ABSENT])
    late = len([r for r in day_records if r.status == AttendanceStatus.LATE])
    on_leave = len([r for r in day_records if r.status == AttendanceStatus.ON_LEAVE])
    on_duty = len([r for r in day_records if r.check_in_time is not None and r.check_out_time is None])

    # 各种员工ID集合（统一为字符串，便于与 Employee.id 比较）
    recorded_emp_ids = {str(r.employee_id) for r in day_records}  # 任何有记录的（签到/缺勤/请假）
    present_emp_ids = {str(r.employee_id) for r in day_records if r.status in [AttendanceStatus.PRESENT, AttendanceStatus.LATE]}
    late_emp_ids = {str(r.employee_id) for r in day_records if r.status == AttendanceStatus.LATE}
    on_leave_emp_ids = {str(r.employee_id) for r in day_records if r.status == AttendanceStatus.ON_LEAVE}

    # 缺勤名单：活跃员工中完全没有记录的（使用字符串ID）
    absent_emp_ids = {str(e.id) for e in active_emps} - recorded_emp_ids

    # 名单（返回对象而不是字符串，便于前端灵活展示）
    def get_emp_info(emp_id):
        emp = next((e for e in active_emps if str(e.id) == emp_id), None)
        if emp:
            return {
                "id": str(emp.id),
                "full_name": emp.full_name,
                "employee_code": emp.employee_code
            }
        return {"id": emp_id, "full_name": "未知员工", "employee_code": ""}

    return {
        "date": report_date.isoformat(),
        "total_active": len(active_emps),
        "present": present,
        "absent": len(absent_emp_ids),
        "late": late,
        "on_leave": on_leave,
        "on_duty": on_duty,
        "present_employees": [get_emp_info(eid) for eid in present_emp_ids],
        "absent_employees": [get_emp_info(eid) for eid in absent_emp_ids],
        "late_employees": [get_emp_info(eid) for eid in late_emp_ids],
        "on_leave_employees": [get_emp_info(eid) for eid in on_leave_emp_ids]
    }

@router.get("/monthly-csv")
async def monthly_csv(year: int, month: int):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Employee Code", "Name", "Date", "Check In", "Check Out", "Hours", "Status"])

    emps = await Employee.find(Employee.is_deactivated == False).to_list()
    for emp in emps:
        records = await AttendanceRecord.find(
            AttendanceRecord.employee_id == emp.id,
            {"date": {"$gte": date(year, month, 1), "$lt": date(year, month, 28) + timedelta(days=5)}}
        ).to_list()
        records = [r for r in records if r.date.year == year and r.date.month == month]
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
async def get_employee_monthly_summary(
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
    emp = await Employee.get(employee_id)
    if not emp:
        return {"error": "Employee not found"}, 404
    
    # 获取该月日期范围
    month_start = date(target_year, target_month, 1)
    if target_month == 12:
        month_end = date(target_year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = date(target_year, target_month + 1, 1) - timedelta(days=1)
    
    # 该员工该月所有记录
    records = await AttendanceRecord.find(
        AttendanceRecord.employee_id == emp.id,
        {"date": {"$gte": month_start, "$lte": month_end}}
    ).to_list()
    
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
                if record.check_in_time and record.check_out_time:
                    hours = (record.check_out_time - record.check_in_time).total_seconds() / 3600
                    total_hours += hours
                
                # 收集签到时间
                if record.check_in_time:
                    check_in_times.append(record.check_in_time.time())
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
async def get_department_attendance(
    department: str,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    # 解析日期
    if date_from:
        start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
    else:
        start_date = date.today().replace(day=1)
    
    if date_to:
        end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
    else:
        end_date = date.today()
    
    # 获取该部门员工
    dept_employees = await Employee.find(Employee.department == department, Employee.is_deactivated == False).to_list()

    if not dept_employees:
        return {"error": "Department not found or no active employees"}, 404

    total_employees = len(dept_employees)
    total_late = 0
    total_absent = 0
    attendance_rates = []
    
    from attendance_system.utils import is_weekend
    
    for emp in dept_employees:
        emp_records = await AttendanceRecord.find(
            AttendanceRecord.employee_id == emp.id,
            {"date": {"$gte": start_date, "$lte": end_date}}
        ).to_list()
        
        # 计算出勤率
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
async def get_punctuality_ranking(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(10)
):
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
    
    emps = await Employee.find().to_list()
    for emp in emps:
        if emp.is_deactivated:
            continue
        # Query records for this employee and date range (use dict filter)
        emp_records = await AttendanceRecord.find({
            "employee_id": emp.id,
            "date": {"$gte": start_date, "$lte": end_date}
        }).to_list()

        # Build a map date -> chosen record (deduplicate multiple records per date)
        records_by_date = {}
        for r in emp_records:
            d = r.date
            existing = records_by_date.get(d)
            if not existing:
                records_by_date[d] = r
                continue

            # Prefer records with a check_in_time. If both have check_in_time,
            # choose the earliest check_in_time (true first sign-in).
            if existing.check_in_time and r.check_in_time:
                if r.check_in_time < existing.check_in_time:
                    records_by_date[d] = r
                continue

            if r.check_in_time and not existing.check_in_time:
                records_by_date[d] = r
                continue

            if existing.check_in_time and not r.check_in_time:
                continue

            # If neither has check_in_time, prefer ON_LEAVE over others
            if r.status == AttendanceStatus.ON_LEAVE and existing.status != AttendanceStatus.ON_LEAVE:
                records_by_date[d] = r
                continue
            if existing.status == AttendanceStatus.ON_LEAVE and r.status != AttendanceStatus.ON_LEAVE:
                continue

            # Otherwise keep the existing record

        # 计算统计
        working_days = 0
        present_days = 0
        late_count = 0

        current = start_date
        while current <= end_date:
            if not is_weekend(current):
                working_days += 1
                day_rec = records_by_date.get(current)
                if day_rec:
                    if day_rec.status == AttendanceStatus.LATE:
                        late_count += 1
                        present_days += 1
                    elif day_rec.status in [AttendanceStatus.PRESENT, AttendanceStatus.HALF_DAY]:
                        present_days += 1
            current += timedelta(days=1)
        
        attendance_rate = (present_days / working_days * 100) if working_days > 0 else 0
        
        rankings.append({
            "employee_code": emp.employee_code,
            "employee_name": emp.full_name,
            "attendance_rate": round(attendance_rate, 2),
            "late_count": late_count,
            "working_days": working_days
        })
    
    # 出勤率降序、迟到升序
    rankings.sort(key=lambda x: (-x["attendance_rate"], x["late_count"]))
    
    return {
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "total_ranked": len(rankings),
        "rankings": rankings[:limit]
    }