import React, { useState } from 'react';
import axios from 'axios';

function EmployeeList({ API, employees, onRefresh }) {
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    employee_code: 'EMP001',
    full_name: '',
    email: '',
    department: 'IT',
    position: '',
    hire_date: new Date().toISOString().split('T')[0]
  });
  const [message, setMessage] = useState('');

  const handleCreate = async () => {
    if (!formData.full_name || !formData.email || !formData.position) {
      setMessage('❌ 请填写所有字段');
      return;
    }
    try {
      await axios.post(`${API}/employees/`, formData);
      setMessage('✅ 创建成功');
      setFormData({
        employee_code: 'EMP' + (parseInt(formData.employee_code.slice(3)) + 1).toString().padStart(3, '0'),
        full_name: '',
        email: '',
        department: 'IT',
        position: '',
        hire_date: new Date().toISOString().split('T')[0]
      });
      onRefresh();
      setTimeout(() => setMessage(''), 3000);
    } catch (err) {
      setMessage('❌ 失败: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="section">
      <h2>👥 员工列表</h2>
      <button onClick={onRefresh} className="btn-primary">🔄 刷新列表</button>

      {employees.length === 0 ? (
        <p style={{ color: '#999' }}>暂无员工</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>员工编号</th>
              <th>姓名</th>
              <th>邮箱</th>
              <th>部门</th>
              <th>职位</th>
              <th>入职日期</th>
            </tr>
          </thead>
          <tbody>
            {employees.map((emp) => (
              <tr key={emp._id}>
                <td>{emp.employee_code}</td>
                <td>{emp.full_name}</td>
                <td>{emp.email}</td>
                <td>{emp.department}</td>
                <td>{emp.position}</td>
                <td>{emp.hire_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>➕ 创建新员工</h3>
      <button onClick={() => setShowForm(!showForm)} className="btn-primary">
        {showForm ? '❌ 隐藏表单' : '✏️ 显示表单'}
      </button>

      {showForm && (
        <div className="form-container">
          <div className="form-group">
            <label>员工编号:</label>
            <input
              value={formData.employee_code}
              onChange={(e) => setFormData({ ...formData, employee_code: e.target.value })}
              placeholder="EMP001"
            />
          </div>
          <div className="form-group">
            <label>姓名:</label>
            <input
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              placeholder="请输入姓名"
            />
          </div>
          <div className="form-group">
            <label>邮箱:</label>
            <input
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              placeholder="example@company.com"
            />
          </div>
          <div className="form-group">
            <label>部门:</label>
            <select
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
            >
              <option>IT</option>
              <option>HR</option>
              <option>Finance</option>
              <option>Operations</option>
              <option>Sales</option>
              <option>Marketing</option>
            </select>
          </div>
          <div className="form-group">
            <label>职位:</label>
            <input
              value={formData.position}
              onChange={(e) => setFormData({ ...formData, position: e.target.value })}
              placeholder="如 Developer, Manager"
            />
          </div>
          <div className="form-group">
            <label>入职日期:</label>
            <input
              type="date"
              value={formData.hire_date}
              onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
            />
          </div>
          <button onClick={handleCreate} className="btn-primary">创建员工</button>
          {message && (
            <div className={`status ${message.includes('✅') ? 'success' : 'error'}`}>
              {message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default EmployeeList;
