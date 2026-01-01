import React, { useState } from 'react';
import axios from 'axios';

function DepartmentStats({ API }) {
  const [dept, setDept] = useState('IT');
  const [dateFrom, setDateFrom] = useState('2025-12-01');
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadStats = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/department/${dept}/attendance`, {
        params: { date_from: dateFrom, date_to: dateTo }
      });
      setStats(res.data);
    } catch (err) {
      alert('加载失败: ' + err.message);
      setStats(null);
    }
    setLoading(false);
  };

  return (
    <div className="section">
      <h2>🏢 部门统计</h2>
      <div className="form-group">
        <label>部门:</label>
        <select value={dept} onChange={(e) => setDept(e.target.value)}>
          <option>IT</option>
          <option>HR</option>
          <option>Finance</option>
          <option>Operations</option>
          <option>Sales</option>
          <option>Marketing</option>
        </select>
      </div>
      <div className="form-group">
        <label>起始日期:</label>
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
      </div>
      <div className="form-group">
        <label>结束日期:</label>
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
      </div>
      <button onClick={loadStats} className="btn-primary">查看统计</button>

      {loading && <p>加载中...</p>}
      {stats && (
        <div className="report">
          <h3>{stats.department} 部门统计</h3>
          <p><strong>时间范围:</strong> {stats.date_from} ~ {stats.date_to}</p>
          <p><strong>部门总人数:</strong> {stats.total_employees}</p>
          <p><strong>平均出勤率:</strong> {stats.avg_attendance_rate}%</p>
          <p><strong>迟到总数:</strong> {stats.total_late}</p>
          <p><strong>缺勤总数:</strong> {stats.total_absent}</p>
        </div>
      )}
    </div>
  );
}

export default DepartmentStats;
