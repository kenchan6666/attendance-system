"""
This module previously held in-memory data structures. The project
now uses MongoDB / Beanie. Keep legacy counters if any code still
references them, but prefer querying the database.
"""

# Legacy counters (not used by DB-backed implementation but kept
# for backward compatibility until callers are migrated).
next_employee_id: int = 1
next_attendance_id: int = 1
next_leave_id: int = 1