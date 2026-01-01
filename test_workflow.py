import requests
import random

# Create new employee
code = f"EMP{random.randint(1, 999):03d}"
r = requests.post('http://localhost:8000/employees', json={
    'full_name': 'Test',
    'employee_code': code,
    'email': 'test@test.com',
    'department': 'IT',
    'position': 'Dev',
    'hire_date': '2025-01-01'
})
emp_id = r.json()['_id']
print(f'Created: {emp_id}')

# Check in
r2 = requests.post('http://localhost:8000/attendance/check-in', json={'employee_id': emp_id})
print(f'Check-in: {r2.status_code}')

# Check out
r3 = requests.patch('http://localhost:8000/attendance/check-out', json={'employee_id': emp_id})
print(f'Check-out: {r3.status_code}')
if r3.status_code == 200:
    data = r3.json()
    print(f'Working hours: {data.get("working_hours")}')
    print(f'Status: {data.get("status")}')
else:
    print(f'Error: {r3.text}')
