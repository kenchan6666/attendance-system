import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [employees, setEmployees] = useState([]);
  const [deptName, setDeptName] = useState('Engineering');
  const [dateFrom, setDateFrom] = useState('2025-12-01');
  const [dateTo, setDateTo] = useState('2025-12-30');
  const [deptStats, setDeptStats] = useState(null);
  const [rankingLimit, setRankingLimit] = useState(5);
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // 从您的后端获取员工列表
    axios.get('http://127.0.0.1:8000/employees/')
      .then(res => {
        setEmployees(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error('API Error:', err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const fetchDeptStats = () => {
    setDeptStats(null);
    axios.get(`http://127.0.0.1:8000/reports/department/${encodeURIComponent(deptName)}/attendance`, {
      params: { date_from: dateFrom, date_to: dateTo }
    })
      .then(res => setDeptStats(res.data))
      .catch(err => setDeptStats({ error: err.message }));
  };

  const fetchRankings = () => {
    setRankings([]);
    axios.get('http://127.0.0.1:8000/reports/punctuality-ranking', {
      params: { date_from: dateFrom, date_to: dateTo, limit: rankingLimit }
    })
      .then(res => setRankings(res.data.rankings || []))
      .catch(err => setRankings([{ error: err.message }]));
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      <h1 style={{ color: '#333' }}>✅ Staff Attendance Record System</h1>
      <h2 style={{ color: '#666' }}>员工列表</h2>
      
      {loading ? (
        <p style={{ color: '#0066cc', fontSize: '16px' }}>⏳ 加载中...</p>
      ) : error ? (
        <div style={{ backgroundColor: '#fff3cd', padding: '15px', borderRadius: '5px', borderLeft: '4px solid #ff6600' }}>
          <p style={{ color: '#856404', margin: '0' }}>⚠️ API 错误: {error}</p>
          <p style={{ color: '#666', fontSize: '14px', marginTop: '10px' }}>确保后端在 http://127.0.0.1:8000 运行</p>
        </div>
      ) : employees.length === 0 ? (
        <div style={{ backgroundColor: '#fff3cd', padding: '15px', borderRadius: '5px', borderLeft: '4px solid #ff6600' }}>
          <p style={{ color: '#856404', margin: '0' }}>⚠️ 还没有员工！</p>
          <p style={{ color: '#666', fontSize: '14px', marginTop: '10px' }}>请先在 <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noopener noreferrer">Swagger UI</a> 创建几个员工（POST /employees/）</p>
        </div>
      ) : (
        <table border="1" cellPadding="10" style={{ borderCollapse: 'collapse', width: '100%', backgroundColor: 'white' }}>
          <thead>
            <tr style={{ backgroundColor: '#f0f0f0' }}>
              <th>ID</th>
              <th>员工编号</th>
              <th>姓名</th>
              <th>部门</th>
              <th>职位</th>
              <th>入职日期</th>
            </tr>
          </thead>
          <tbody>
            {employees.map(emp => (
              <tr key={emp.id}>
                <td>{emp.id}</td>
                <td>{emp.employee_code}</td>
                <td>{emp.full_name}</td>
                <td>{emp.department}</td>
                <td>{emp.position}</td>
                <td>{emp.hire_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      
      <div style={{ marginTop: '30px', padding: '15px', backgroundColor: 'white', borderRadius: '5px', border: '1px solid #ddd' }}>
        <p style={{ fontWeight: 'bold', color: '#333' }}>📝 操作提示：</p>
        <ol style={{ color: '#666' }}>
          <li>打开 <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noopener noreferrer">Swagger UI (http://127.0.0.1:8000/docs)</a></li>
          <li>用 POST /employees/ 创建员工（employee_code 必须是 EMP001 格式）</li>
          <li>刷新这个页面，就能看到员工列表！</li>
        </ol>
      </div>

      <div style={{ marginTop: '30px', display: 'flex', gap: '20px' }}>
        <div style={{ flex: 1, padding: '15px', backgroundColor: 'white', borderRadius: '5px', border: '1px solid #ddd' }}>
          <h3>📊 部门统计</h3>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
            <input value={deptName} onChange={e => setDeptName(e.target.value)} placeholder="Department" />
            <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
            <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
            <button onClick={fetchDeptStats}>查询</button>
          </div>
          {deptStats ? (
            deptStats.error ? (
              <div style={{ color: 'red' }}>错误: {deptStats.error}</div>
            ) : (
              <div>
                <p><strong>部门</strong>: {deptStats.department}</p>
                <p><strong>时间范围</strong>: {deptStats.date_from} → {deptStats.date_to}</p>
                <p><strong>员工总数</strong>: {deptStats.total_employees}</p>
                <p><strong>平均出勤率</strong>: {deptStats.avg_attendance_rate}%</p>
                <p><strong>迟到总数</strong>: {deptStats.total_late}</p>
                <p><strong>缺勤总数</strong>: {deptStats.total_absent}</p>
              </div>
            )
          ) : (
            <p style={{ color: '#666' }}>未查询</p>
          )}
        </div>

        <div style={{ flex: 1, padding: '15px', backgroundColor: 'white', borderRadius: '5px', border: '1px solid #ddd' }}>
          <h3>🏆 准时率排行</h3>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '10px' }}>
            <input type="number" value={rankingLimit} onChange={e => setRankingLimit(Number(e.target.value))} min={1} max={50} />
            <input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
            <input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
            <button onClick={fetchRankings}>加载排行</button>
          </div>
          {rankings.length > 0 ? (
            rankings[0].error ? (
              <div style={{ color: 'red' }}>错误: {rankings[0].error}</div>
            ) : (
              <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse', width: '100%' }}>
                <thead style={{ backgroundColor: '#f0f0f0' }}>
                  <tr>
                    <th>排名</th>
                    <th>员工</th>
                    <th>出勤率</th>
                    <th>迟到次数</th>
                  </tr>
                </thead>
                <tbody>
                  {rankings.map((r, idx) => (
                    <tr key={r.employee_id}>
                      <td>{idx + 1}</td>
                      <td>{r.employee_name} (ID: {r.employee_id})</td>
                      <td>{r.attendance_rate}%</td>
                      <td>{r.late_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )
          ) : (
            <p style={{ color: '#666' }}>未加载排行</p>
          )}
        </div>
      </div>

      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#e8f4f8', borderRadius: '5px', fontSize: '12px', color: '#0066cc' }}>
        <strong>🎉 前端已成功加载！</strong> 如果看到这条消息，说明 React 正在正常运行。
      </div>
    </div>
  );
}

export default App;