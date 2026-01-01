import React, { useState } from 'react';
import axios from 'axios';

function convertToEmployeeCode(input) {
  const trimmed = input.trim().toUpperCase();
  if (trimmed.startsWith('EMP')) {
    return trimmed;
  }
  if (/^\d+$/.test(trimmed)) {
    return 'EMP' + trimmed.padStart(3, '0');
  }
  return trimmed;
}

function AttendanceOps({ API }) {
  const [employeeCode, setEmployeeCode] = useState('');
  const [absentDate, setAbsentDate] = useState(new Date().toISOString().split('T')[0]);
  const [status, setStatus] = useState('');

  const handleCheckIn = async () => {
    if (!employeeCode) {
      alert('请输入员工编号');
      return;
    }
    const code = convertToEmployeeCode(employeeCode);
    try {
      await axios.post(`${API}/attendance/check-in`, { employee_code: code });
      setStatus('✅ 签到成功');
      setEmployeeCode('');
      setTimeout(() => setStatus(''), 3000);
    } catch (err) {
      setStatus(`❌ 失败: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleCheckOut = async () => {
    if (!employeeCode) {
      alert('请输入员工编号');
      return;
    }
    const code = convertToEmployeeCode(employeeCode);
    try {
      const res = await axios.patch(`${API}/attendance/check-out`, { employee_code: code });
      setStatus(`✅ 签退成功! 工时: ${res.data.working_hours} 小时`);
      setEmployeeCode('');
      setTimeout(() => setStatus(''), 3000);
    } catch (err) {
      setStatus(`❌ 失败: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleMarkAbsent = async () => {
    if (!employeeCode) {
      alert('请输入员工编号');
      return;
    }
    const code = convertToEmployeeCode(employeeCode);
    try {
      await axios.post(`${API}/attendance/mark-absent`, { employee_code: code, date: absentDate });
      setStatus('✅ 标记缺勤成功');
      setEmployeeCode('');
      setTimeout(() => setStatus(''), 3000);
    } catch (err) {
      setStatus(`❌ 失败: ${err.response?.data?.detail || err.message}`);
    }
  };

  return (
    <div className="section">
      <h2>📋 出勤操作</h2>
      <div className="form-group">
        <label>员工编号（如 1, 2, 3 或 EMP001）:</label>
        <input
          type="text"
          value={employeeCode}
          onChange={(e) => setEmployeeCode(e.target.value)}
          placeholder="输入数字或员工编号"
        />
      </div>

      <div className="form-group">
        <label>日期（标记缺勤）:</label>
        <input
          type="date"
          value={absentDate}
          onChange={(e) => setAbsentDate(e.target.value)}
        />
      </div>

      <div className="button-group">
        <button onClick={handleCheckIn} className="btn-primary">✅ 签到</button>
        <button onClick={handleCheckOut} className="btn-primary">🔚 签退</button>
        <button onClick={handleMarkAbsent} className="btn-danger">✘ 标记缺勤</button>
      </div>

      {status && (
        <div className={`status ${status.includes('✅') ? 'success' : 'error'}`}>
          {status}
        </div>
      )}
    </div>
  );
}

export default AttendanceOps;
