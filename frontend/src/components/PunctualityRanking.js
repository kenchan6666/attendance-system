import React, { useState } from 'react';
import axios from 'axios';

function PunctualityRanking({ API }) {
  const [dateFrom, setDateFrom] = useState('2025-12-01');
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);
  const [limit, setLimit] = useState(10);
  const [rankings, setRankings] = useState([]);
  const [loading, setLoading] = useState(false);

  const loadRankings = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/punctuality-ranking`, {
        params: { date_from: dateFrom, date_to: dateTo, limit }
      });
      setRankings(res.data.rankings || []);
    } catch (err) {
      alert('加载失败: ' + err.message);
      setRankings([]);
    }
    setLoading(false);
  };

  return (
    <div className="section">
      <h2>🏆 准时率排行榜</h2>
      <div className="form-group">
        <label>起始日期:</label>
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
      </div>
      <div className="form-group">
        <label>结束日期:</label>
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
      </div>
      <div className="form-group">
        <label>显示前几名:</label>
        <input
          type="number"
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value))}
          min={1}
          max={50}
        />
      </div>
      <button onClick={loadRankings} className="btn-primary">加载排行</button>

      {loading && <p>加载中...</p>}
      {rankings.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>排名</th>
              <th>员工编号</th>
              <th>姓名</th>
              <th>出勤率(%)</th>
              <th>迟到次数</th>
              <th>工作日</th>
            </tr>
          </thead>
          <tbody>
            {rankings.map((r, idx) => (
              <tr key={r.employee_code}>
                <td>{idx + 1}</td>
                <td>{r.employee_code}</td>
                <td>{r.employee_name}</td>
                <td>{r.attendance_rate}</td>
                <td>{r.late_count}</td>
                <td>{r.working_days}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {rankings.length === 0 && !loading && (
        <p style={{ color: '#999' }}>暂无排行数据</p>
      )}
    </div>
  );
}

export default PunctualityRanking;
