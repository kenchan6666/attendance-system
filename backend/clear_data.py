"""
clear_data.py

Safe helper to clear attendance database collections.

Usage:
  python clear_data.py

This script will print current document counts for `employees`,
`attendance_records`, and `leave_requests`, then ask for confirmation.
Type exactly "YES" to proceed with deletion.
"""
import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from attendance_system.models import Employee, AttendanceRecord, LeaveRequest


async def clear_all(mongodb_url: str):
    client = AsyncIOMotorClient(mongodb_url)
    db = client.attendance_db

    # initialize Beanie so models are registered (some codepaths expect this)
    await init_beanie(database=db, document_models=[Employee, AttendanceRecord, LeaveRequest])

    emp_col = db.get_collection("employees")
    att_col = db.get_collection("attendance_records")
    leave_col = db.get_collection("leave_requests")

    emp_count = await emp_col.count_documents({})
    att_count = await att_col.count_documents({})
    leave_count = await leave_col.count_documents({})

    print("Current counts:")
    print(f"  employees: {emp_count}")
    print(f"  attendance_records: {att_count}")
    print(f"  leave_requests: {leave_count}")

    confirm = input('\nType YES to delete ALL documents in these collections: ')
    if confirm != 'YES':
        print('Aborted. No changes made.')
        client.close()
        return

    # perform deletions
    emp_res = await emp_col.delete_many({})
    att_res = await att_col.delete_many({})
    leave_res = await leave_col.delete_many({})

    print('\nDeletion results:')
    print(f"  employees deleted: {getattr(emp_res, 'deleted_count', 'unknown')}")
    print(f"  attendance_records deleted: {getattr(att_res, 'deleted_count', 'unknown')}")
    print(f"  leave_requests deleted: {getattr(leave_res, 'deleted_count', 'unknown')}")

    client.close()


if __name__ == '__main__':
    mongodb_url = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/attendance_db')
    try:
        asyncio.run(clear_all(mongodb_url))
    except KeyboardInterrupt:
        print('\nInterrupted by user.')