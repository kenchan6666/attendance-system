import React, { useState } from 'react';
import axios from 'axios';

function DailyReport({ API }) {
  const [reportDate, setReportDate] = useState(new Date().toISOString().split('T')[0]);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadReport = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/reports/daily-summary?report_date=${reportDate}`);
      setReport(res.data);
    } catch (err) {
      alert('加载失败: ' + err.message);
    }
    setLoading(false);
  };

  return (
    <div className="section">
      <h2>📊 日报</h2>
      <div className="form-group">
        <label>选择日期:</label>
        <input
          type="date"
          value={reportDate}
          onChange={(e) => setReportDate(e.target.value)}
        />
        <button onClick={loadReport} className="btn-primary">查看日报</button>
      </div>

      {loading && <p>加载中...</p>}
      {report && (
        <div className="report">
          <h3>{report.date} 出勤报告</h3>
          <p>
            <strong>总人数:</strong> {report.total_active} | 
            <strong> 出勤:</strong> {report.present} | 
            <strong> 在岗:</strong> {report.on_duty} | 
            <strong> 缺勤:</strong> {report.absent} | 
            <strong> 迟到:</strong> {report.late} | 
            <strong> 请假:</strong> {report.on_leave}
          </p>
          {report.present_employees && report.present_employees.length > 0 && (
            <p><strong>出勤名单:</strong> {report.present_employees.join(', ')}</p>
          )}
          {report.absent_employees && report.absent_employees.length > 0 && (
            <p><strong>缺勤名单:</strong> {report.absent_employees.join(', ')}</p>
          )}
          {report.late_employees && report.late_employees.length > 0 && (
            <p><strong>迟到名单:</strong> {report.late_employees.join(', ')}</p>
          )}
        </div>
      )}
    </div>
  );
}

export default DailyReport;
