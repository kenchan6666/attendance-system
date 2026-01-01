from enum import Enum


class Department(str, Enum):
    HR = "HR"
    IT = "IT"
    FINANCE = "Finance"
    OPERATIONS = "Operations"
    SALES = "Sales"
    MARKETING = "Marketing"


class AttendanceStatus(str, Enum):
    PRESENT = "Present"
    LATE = "Late"
    HALF_DAY = "Half Day"
    ABSENT = "Absent"
    ON_LEAVE = "On Leave"


class LeaveType(str, Enum):
    SICK_LEAVE = "Sick Leave"
    ANNUAL_LEAVE = "Annual Leave"
    PERSONAL_LEAVE = "Personal Leave"
    UNPAID_LEAVE = "Unpaid Leave"
    MATERNITY_LEAVE = "Maternity Leave"
