import { useState, useEffect } from 'react';
import './index.css';

const API = 'http://127.0.0.1:8000';

function App() {
  const [activeTab, setActiveTab] = useState('attendance');
  const [statusMsg, setStatusMsg] = useState('');
  const [statusType, setStatusType] = useState('info');
  const [reportContent, setReportContent] = useState('');
  const [checkedOutContent, setCheckedOutContent] = useState('');
  const [employeeList, setEmployeeList] = useState([]);
  const [deptContent, setDeptContent] = useState('');
  const [rankContent, setRankContent] = useState('');
  const [leaveStatus, setLeaveStatus] = useState('');
  const [leaveStatusType, setLeaveStatusType] = useState('info');
  const [leaveRequestsContent, setLeaveRequestsContent] = useState('');
  const [employeeFormVisible, setEmployeeFormVisible] = useState(false);
  const [editEmployeeFormVisible, setEditEmployeeFormVisible] = useState(false);
  const [editEmpCode, setEditEmpCode] = useState('');
  const [editEmpName, setEditEmpName] = useState('');
  const [editEmpEmail, setEditEmpEmail] = useState('');
  const [editEmpDept, setEditEmpDept] = useState('');
  const [editEmpPosition, setEditEmpPosition] = useState('');
  const [editEmpHireDate, setEditEmpHireDate] = useState('');
  const [editStatus, setEditStatus] = useState('');
  const [editStatusType, setEditStatusType] = useState('info');

  // 初始化日期和加载员工列表
  useEffect(() => {
    const today = new Date().toISOString().split('T')[0];
    const setValue = (id, value) => {
      const el = document.getElementById(id);
      if (el) el.value = value;
    };

    setValue('reportDate', today);
    setValue('checkedOutDate', today);
    setValue('deptFromDate', '2025-12-01');
    setValue('deptToDate', today);
    setValue('rankFromDate', '2025-12-01');
    setValue('rankToDate', today);
    setValue('leaveStartDate', today);
    setValue('leaveEndDate', today);
    loadEmployeeList();
  }, []);

  // 显示状态消息
  const showStatus = (msg, type = 'info') => {
    setStatusMsg(msg);
    setStatusType(type);
    setTimeout(() => {
      setStatusMsg('');
    }, 3000);
  };

  // 员工编号转换
  const convertToEmployeeCode = (input) => {
    const trimmed = input.trim().toUpperCase();
    if (trimmed.startsWith('EMP')) return trimmed;
    if (/^\d+$/.test(trimmed)) return 'EMP' + trimmed.padStart(3, '0');
    return trimmed;
  };

  // 签到
  const checkIn = async () => {
    const code = convertToEmployeeCode(document.getElementById('empCode')?.value);
    if (!code || code === 'EMP') {
      showStatus('请输入员工编号', 'error');
      return;
    }
    try {
      const res = await fetch(`${API}/attendance/check-in`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_code: code })
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || '签到失败');
      }
      showStatus('签到成功！', 'success');
      document.getElementById('empCode').value = '';
    } catch (err) {
      showStatus(`签到失败: ${err.message}`, 'error');
    }
  };

  // 签退
  const checkOut = async () => {
    const code = convertToEmployeeCode(document.getElementById('empCode')?.value);
    if (!code || code === 'EMP') {
      showStatus('请输入员工编号', 'error');
      return;
    }
    try {
      const res = await fetch(`${API}/attendance/check-out`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_code: code })
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || '签退失败');
      }
      showStatus('签退成功', 'success');
      document.getElementById('empCode').value = '';
    } catch (err) {
      showStatus(`签退失败: ${err.message}`, 'error');
    }
  };

  // 标记请假
  const markAbsent = async () => {
    const code = convertToEmployeeCode(document.getElementById('empCode')?.value);
    if (!code || code === 'EMP') {
      showStatus('请输入员工编号', 'error');
      return;
    }
    try {
      const today = new Date().toISOString().split('T')[0];
      const res = await fetch(`${API}/attendance/mark-absent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ employee_code: code, date: today })
      });
      const data = await res.json();
      showStatus(`标记成功: ${data.message}`, 'success');
      document.getElementById('empCode').value = '';
    } catch (err) {
      showStatus(`标记失败: ${err.message}`, 'error');
    }
  };

  // 加载日报
  const loadDailyReport = async () => {
    const date = document.getElementById('reportDate')?.value;
    try {
      const res = await fetch(`${API}/reports/daily-summary?report_date=${date}`);
      const data = await res.json();
      let html = '<div class="report-stats">';
      html += `<div class="stat-box"><h3>总人数</h3><div class="value">${data.total_active || 0}</div></div>`;
      html += `<div class="stat-box"><h3>出勤</h3><div class="value">${data.present || 0}</div></div>`;
      html += `<div class="stat-box"><h3>缺勤</h3><div class="value">${data.absent || 0}</div></div>`;
      html += `<div class="stat-box"><h3>迟到</h3><div class="value">${data.late || 0}</div></div>`;
      html += `<div class="stat-box"><h3>请假</h3><div class="value">${data.on_leave || 0}</div></div>`;
      html += `<div class="stat-box"><h3>值班</h3><div class="value">${data.on_duty || 0}</div></div>`;
      html += '</div>';

      if (data.present_employees && data.present_employees.length > 0) {
        html += '<h3 style="margin-top:20px; margin-bottom:10px;">出勤员工:</h3><ul style="list-style:none;padding:0;">';
        data.present_employees.forEach(e => {
          const name = e.full_name || '未知';
          const code = e.employee_code || '';
          html += `<li style="padding:8px; border-bottom:1px solid #eee;">${name} ${code ? `(${code})` : ''}</li>`;
        });
        html += '</ul>';
      }

      if (data.late_employees && data.late_employees.length > 0) {
        html += '<h3 style="margin-top:20px; margin-bottom:10px;">迟到员工:</h3><ul style="list-style:none;padding:0;">';
        data.late_employees.forEach(e => {
          const name = e.full_name || '未知';
          const code = e.employee_code || '';
          html += `<li style="padding:8px; border-bottom:1px solid #eee;">${name} ${code ? `(${code})` : ''}</li>`;
        });
        html += '</ul>';
      }

      if (data.absent_employees && data.absent_employees.length > 0) {
        html += '<h3 style="margin-top:20px; margin-bottom:10px;">缺勤员工:</h3><ul style="list-style:none;padding:0;">';
        data.absent_employees.forEach(e => {
          const name = e.full_name || '未知';
          const code = e.employee_code || '';
          html += `<li style="padding:8px; border-bottom:1px solid #eee;">${name} ${code ? `(${code})` : ''}</li>`;
        });
        html += '</ul>';
      }

      if (data.on_leave_employees && data.on_leave_employees.length > 0) {
        html += '<h3 style="margin-top:20px; margin-bottom:10px;">请假员工:</h3><ul style="list-style:none;padding:0;">';
        data.on_leave_employees.forEach(e => {
          const name = e.full_name || '未知';
          const code = e.employee_code || '';
          html += `<li style="padding:8px; border-bottom:1px solid #eee;">${name} ${code ? `(${code})` : ''}</li>`;
        });
        html += '</ul>';
      }

      setReportContent(html);
    } catch (err) {
      showStatus(`加载失败: ${err.message}`, 'error');
    }
  };

  // 加载已签退员工
  const loadCheckedOutEmployees = async () => {
    const date = document.getElementById('checkedOutDate')?.value;
    if (!date) {
      showStatus('请选择日期', 'error');
      return;
    }
    try {
      const res = await fetch(`${API}/attendance/?date=${date}`);
      const records = await res.json();
      const checkedOut = records.filter(r => r.check_out_time !== null);
      let html = '<div class="report-stats">';
      html += `<div class="stat-box"><h3>已签退人数</h3><div class="value">${checkedOut.length}</div></div>`;
      html += '</div>';
      
      if (checkedOut.length > 0) {
        html += '<table>';
        html += '<thead><tr><th>员工编号</th><th>员工名字</th><th>签到时间</th><th>签退时间</th><th>工时</th></tr></thead>';
        html += '<tbody>';
        checkedOut.forEach(record => {
          const checkIn = record.check_in_time ? new Date(record.check_in_time).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'}) : '-';
          const checkOut = record.check_out_time ? new Date(record.check_out_time).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'}) : '-';
          const hours = record.working_hours ? record.working_hours.toFixed(2) : '-';
          html += `<tr><td>${record.employee_code}</td><td>${record.employee_name}</td><td>${checkIn}</td><td>${checkOut}</td><td>${hours}</td></tr>`;
        });
        html += '</tbody></table>';
      } else {
        html += '<p style="color: #999; text-align: center;">该日期暂无已签退的员工</p>';
      }
      setCheckedOutContent(html);
    } catch (err) {
      showStatus(`加载失败: ${err.message}`, 'error');
    }
  };

  // 加载员工列表
  const loadEmployeeList = async () => {
    try {
      const res = await fetch(`${API}/employees/`);
      const data = await res.json();
      setEmployeeList(data);
    } catch (err) {
      console.error(err);
    }
  };

  // 创建员工
  const createEmployee = async () => {
    const rawCode = document.getElementById('newEmpCode')?.value.trim();
    const name = document.getElementById('newEmpName')?.value.trim();
    const email = document.getElementById('newEmpEmail')?.value.trim();
    const dept = document.getElementById('newEmpDept')?.value;

    if (!rawCode || !name || !email) {
      showStatus('请填写员工编号、姓名和邮箱', 'error');
      return;
    }

    const employee_code = convertToEmployeeCode(rawCode);

    if (!/^EMP\d{3}$/.test(employee_code)) {
      showStatus('员工编号格式错误，请输入类似 EMP001 或 1~999 的数字', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/employees/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_code,
          full_name: name,
          email,
          department: dept,
          position: '员工',
          hire_date: new Date().toISOString().split('T')[0]
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        const errorMsg = errorData.detail 
          ? (Array.isArray(errorData.detail) ? errorData.detail.map(d => d.msg).join('; ') : errorData.detail)
          : '未知错误';
        throw new Error(errorMsg);
      }

      showStatus('员工创建成功！', 'success');
      document.getElementById('newEmpCode').value = '';
      document.getElementById('newEmpName').value = '';
      document.getElementById('newEmpEmail').value = '';
      loadEmployeeList();
    } catch (err) {
      showStatus(`创建失败: ${err.message}`, 'error');
    }
  };

  const toggleEmployeeForm = () => {
    setEmployeeFormVisible(!employeeFormVisible);
  };

  // 加载部门统计
  const loadDepartmentStats = async () => {
    const dept = document.getElementById('deptSelect')?.value;
    const from = document.getElementById('deptFromDate')?.value;
    const to = document.getElementById('deptToDate')?.value;

    try {
      const res = await fetch(`${API}/reports/department/${dept}/attendance?date_from=${from}&date_to=${to}`);
      const data = await res.json();
      let html = '<div class="report-stats">';
      html += `<div class="stat-box"><h3>员工总数</h3><div class="value">${data.total_employees}</div></div>`;
      html += `<div class="stat-box"><h3>平均出勤率</h3><div class="value">${data.avg_attendance_rate}%</div></div>`;
      html += `<div class="stat-box late"><h3>总迟到</h3><div class="value">${data.total_late}</div></div>`;
      html += `<div class="stat-box absent"><h3>总缺勤</h3><div class="value">${data.total_absent}</div></div>`;
      html += '</div>';
      setDeptContent(html);
    } catch (err) {
      showStatus(`加载失败: ${err.message}`, 'error');
    }
  };

  // 加载排行
  const loadRanking = async () => {
    const from = document.getElementById('rankFromDate')?.value;
    const to = document.getElementById('rankToDate')?.value;
    const limit = document.getElementById('rankLimit')?.value;

    try {
      const res = await fetch(`${API}/reports/punctuality-ranking?date_from=${from}&date_to=${to}&limit=${limit}`);
      const data = await res.json();
      let html = '<table><thead><tr><th>排名</th><th>编号</th><th>姓名</th><th>出勤率(%)</th><th>迟到次数</th></tr></thead><tbody>';
      data.rankings.forEach((r, idx) => {
        html += `<tr><td>${idx + 1}</td><td>${r.employee_code}</td><td>${r.employee_name}</td><td>${r.attendance_rate}</td><td>${r.late_count}</td></tr>`;
      });
      html += '</tbody></table>';
      setRankContent(html);
    } catch (err) {
      showStatus(`加载失败: ${err.message}`, 'error');
    }
  };

  // 提交请假申请
  const submitLeaveRequest = async () => {
    const rawCode = document.getElementById('leaveEmpCode')?.value.trim();
    if (!rawCode) {
      showLeaveStatus('请输入员工编号', 'error');
      return;
    }
    const employee_code = convertToEmployeeCode(rawCode);

    const leaveType = document.getElementById('leaveType')?.value;
    const startDate = document.getElementById('leaveStartDate')?.value;
    const endDate = document.getElementById('leaveEndDate')?.value;
    const reason = document.getElementById('leaveReason')?.value.trim();

    if (!startDate || !endDate) {
      showLeaveStatus('请选择开始和结束日期', 'error');
      return;
    }
    if (startDate > endDate) {
      showLeaveStatus('开始日期不能晚于结束日期', 'error');
      return;
    }
    if (!reason) {
      showLeaveStatus('请填写请假理由', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/leaves`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_code,
          leave_type: leaveType,
          start_date: startDate,
          end_date: endDate,
          reason
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || '未知错误');
      }

      showLeaveStatus('请假申请提交成功！等待审批', 'success');
      document.getElementById('leaveEmpCode').value = '';
      document.getElementById('leaveStartDate').value = '';
      document.getElementById('leaveEndDate').value = '';
      document.getElementById('leaveReason').value = '';
    } catch (err) {
      showLeaveStatus(`提交失败: ${err.message}`, 'error');
    }
  };

  // 加载请假申请列表
  const loadLeaveRequests = async () => {
    const statusFilter = document.getElementById('leaveStatusFilter')?.value;
    try {
      let url = `${API}/leaves`;
      if (statusFilter) url += `?status=${statusFilter}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('加载失败');
      const leaves = await res.json();

      let html = '';
      if (leaves.length === 0) {
        html = '<p style="color: #999; text-align: center;">暂无请假申请</p>';
      } else {
        html = '<table>';
        html += '<thead><tr><th>员工编号</th><th>员工名字</th><th>请假类型</th><th>开始日期</th><th>结束日期</th><th>天数</th><th>状态</th><th>操作</th></tr></thead>';
        html += '<tbody>';
        leaves.forEach(leave => {
          const leaveId = leave.id;
          if (!leaveId) return;

          const statusBadge = {
            'Pending': '<span style="color: #ff9800; font-weight: bold;">待审批</span>',
            'Approved': '<span style="color: #4caf50; font-weight: bold;">已批准</span>',
            'Rejected': '<span style="color: #f44336; font-weight: bold;">已驳回</span>'
          }[leave.status] || leave.status;

          let actions = '';
          if (leave.status === 'Pending') {
            actions += `<button onClick={() => approveLeaveRequest(${leaveId})} class="btn-small btn-success">批准</button> `;
            actions += `<button onClick={() => rejectLeaveRequest(${leaveId})} class="btn-small btn-danger">驳回</button> `;
            actions += `<button onClick={() => deleteLeaveRequest(${leaveId})} class="btn-small" style="background-color: #999;">删除</button>`;
          } else {
            actions = '-';
          }

          html += `<tr><td>${leave.employee_code}</td><td>${leave.employee_name}</td><td>${getLeaveTypeLabel(leave.leave_type)}</td><td>${leave.start_date}</td><td>${leave.end_date}</td><td>${leave.total_days}</td><td>${statusBadge}</td><td>${actions}</td></tr>`;
        });
        html += '</tbody></table>';
      }
      setLeaveRequestsContent(html);
    } catch (err) {
      showLeaveStatus(`加载失败: ${err.message}`, 'error');
    }
  };

  const getLeaveTypeLabel = (leaveType) => {
    const labels = {
      'Sick Leave': '病假',
      'Annual Leave': '年假',
      'Personal Leave': '事假',
      'Unpaid Leave': '无薪假',
      'Maternity Leave': '产假'
    };
    return labels[leaveType] || leaveType;
  };

  // 批准请假
  const approveLeaveRequest = async (leaveId) => {
    if (!window.confirm('确认批准该请假申请吗？')) return;
    try {
      const res = await fetch(`${API}/leaves/${encodeURIComponent(leaveId)}/approve`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved_by: 1 })
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail ? (Array.isArray(error.detail) ? error.detail[0].msg : error.detail) : '批准失败');
      }
      const approvedLeave = await res.json();
      showLeaveStatus(`✓ 请假申请已批准，自动生成 ON_LEAVE 记录（${approvedLeave.start_date} ~ ${approvedLeave.end_date}）`, 'success');
      setTimeout(loadLeaveRequests, 1500);
    } catch (err) {
      showLeaveStatus(`批准失败: ${err.message}`, 'error');
    }
  };

  // 驳回请假
  const rejectLeaveRequest = async (leaveId) => {
    if (!window.confirm('确认驳回该请假申请吗？')) return;
    try {
      const res = await fetch(`${API}/leaves/${encodeURIComponent(leaveId)}/reject`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail ? (Array.isArray(error.detail) ? error.detail[0].msg : error.detail) : '驳回失败');
      }
      const rejectedLeave = await res.json();
      showLeaveStatus(`✗ 请假申请已驳回，状态已更新为 ${rejectedLeave.status}`, 'success');
      setTimeout(loadLeaveRequests, 1500);
    } catch (err) {
      showLeaveStatus(`驳回失败: ${err.message}`, 'error');
    }
  };

  // 删除请假
  const deleteLeaveRequest = async (leaveId) => {
    if (!window.confirm('确认删除该请假申请吗？此操作不可撤销。')) return;
    try {
      const res = await fetch(`${API}/leaves/${encodeURIComponent(leaveId)}`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail ? (Array.isArray(error.detail) ? error.detail[0].msg : error.detail) : '删除失败');
      }
      showLeaveStatus('✓ 请假申请已删除', 'success');
      setTimeout(loadLeaveRequests, 1500);
    } catch (err) {
      showLeaveStatus(`删除失败: ${err.message}`, 'error');
    }
  };

  // 请假状态提示
  const showLeaveStatus = (msg, type = 'info') => {
    setLeaveStatus(msg);
    setLeaveStatusType(type);
    setTimeout(() => setLeaveStatus(''), 4000);
  };

  // 编辑员工填充
  const editEmployeeByCode = (e) => {
    setEditEmployeeFormVisible(true);
    setEditEmpCode(e.employee_code);
    setEditEmpName(e.full_name);
    setEditEmpEmail(e.email);
    setEditEmpDept(e.department);
    setEditEmpPosition(e.position || '');
    setEditEmpHireDate(e.hire_date);
  };

  // 取消编辑
  const cancelEmployeeEdit = () => {
    setEditEmployeeFormVisible(false);
    setEditStatus('');
  };

  // 保存员工编辑
  const saveEmployeeEdit = async () => {
    if (!editEmpCode || !editEmpName || !editEmpEmail || !editEmpHireDate) {
      showEditStatus('请填写完整信息', 'error');
      return;
    }

    try {
      const res = await fetch(`${API}/employees/code/${editEmpCode}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: editEmpName,
          email: editEmpEmail,
          department: editEmpDept,
          position: editEmpPosition,
          hire_date: editEmpHireDate
        })
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || '更新失败');
      }

      showEditStatus('员工信息更新成功！', 'success');
      setTimeout(() => {
        cancelEmployeeEdit();
        loadEmployeeList();
      }, 1500);
    } catch (err) {
      showEditStatus(`更新失败: ${err.message}`, 'error');
    }
  };

  // 编辑状态提示
  const showEditStatus = (msg, type = 'info') => {
    setEditStatus(msg);
    setEditStatusType(type);
  };

  // 离职员工
  const deactivateEmployeeByCode = async (code, name) => {
    if (!window.confirm(`确认将员工【${name}】(${code}) 标记为离职？此操作不可逆！`)) return;

    try {
      const res = await fetch(`${API}/employees/code/${code}/deactivate`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' }
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || '离职失败');
      }
      alert(`${name} (${code}) 已标记为离职`);
      loadEmployeeList();
    } catch (err) {
      alert(`操作失败: ${err.message}`);
    }
  };

  return (
    <div className="container">
      <div className="header">
        <h1>员工考勤记录系统</h1>
      </div>

      <nav className="nav-tabs">
        <button className={`tab-btn ${activeTab === 'attendance' ? 'active' : ''}`} onClick={() => setActiveTab('attendance')}>出勤操作</button>
        <button className={`tab-btn ${activeTab === 'checked-out' ? 'active' : ''}`} onClick={() => setActiveTab('checked-out')}>已签退</button>
        <button className={`tab-btn ${activeTab === 'daily-report' ? 'active' : ''}`} onClick={() => setActiveTab('daily-report')}>日报</button>
        <button className={`tab-btn ${activeTab === 'employees' ? 'active' : ''}`} onClick={() => setActiveTab('employees')}>员工列表</button>
        <button className={`tab-btn ${activeTab === 'department' ? 'active' : ''}`} onClick={() => setActiveTab('department')}>部门统计</button>
        <button className={`tab-btn ${activeTab === 'ranking' ? 'active' : ''}`} onClick={() => setActiveTab('ranking')}>准时率排行</button>
        <button className={`tab-btn ${activeTab === 'leave-request' ? 'active' : ''}`} onClick={() => setActiveTab('leave-request')}>请假申请</button>
      </nav>

      <main className="main-content">
        {activeTab === 'attendance' && (
          <div id="attendance" className="tab-content">
            <div className="section">
              <h2>出勤操作</h2>
              {statusMsg && <div className={`status ${statusType}`}>{statusMsg}</div>}
              <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '6px', marginBottom: '20px', border: '1px solid #e0e0e0' }}>
                <div className="form-group">
                  <label>员工编号 (输入 "1" 或 "EMP001"):</label>
                  <input type="text" id="empCode" placeholder="输入员工编号或序号" />
                </div>
                <div className="button-group">
                  <button onClick={checkIn} className="btn-primary">签到</button>
                  <button onClick={checkOut} className="btn-success">签退</button>
                  <button onClick={markAbsent} className="btn-danger">标记请假</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'daily-report' && (
          <div id="daily-report" className="tab-content">
            <div className="section">
              <h2>日报</h2>
              <div className="form-group">
                <label>选择日期:</label>
                <input type="date" id="reportDate" />
              </div>
              <button onClick={loadDailyReport} className="btn-primary">加载报表</button>
              <div id="reportContent" style={{ marginTop: '20px' }} dangerouslySetInnerHTML={{ __html: reportContent }} />
            </div>
          </div>
        )}

        {activeTab === 'checked-out' && (
          <div id="checked-out" className="tab-content">
            <div className="section">
              <h2>已签退员工</h2>
              <div className="form-group">
                <label>选择日期:</label>
                <input type="date" id="checkedOutDate" />
              </div>
              <button onClick={loadCheckedOutEmployees} className="btn-primary">加载已签退员工</button>
              <div id="checkedOutContent" style={{ marginTop: '20px' }} dangerouslySetInnerHTML={{ __html: checkedOutContent }} />
            </div>
          </div>
        )}

        {activeTab === 'employees' && (
          <div id="employees" className="tab-content">
            <div className="section">
              <h2>员工列表</h2>
              <button onClick={toggleEmployeeForm} className="btn-primary toggle-form-btn">+ 创建员工</button>
              {employeeFormVisible && (
                <div id="employeeForm" style={{ backgroundColor: 'white', padding: '20px', borderRadius: '6px', marginBottom: '20px', border: '1px solid #e0e0e0' }}>
                  <div className="form-group">
                    <label>员工编号:</label>
                    <input type="text" id="newEmpCode" placeholder="EMP001" />
                  </div>
                  <div className="form-group">
                    <label>姓名:</label>
                    <input type="text" id="newEmpName" placeholder="输入姓名" />
                  </div>
                  <div className="form-group">
                    <label>邮箱:</label>
                    <input type="email" id="newEmpEmail" placeholder="example@company.com" />
                  </div>
                  <div className="form-group">
                    <label>部门:</label>
                    <select id="newEmpDept">
                      <option>IT</option>
                      <option>HR</option>
                      <option>Finance</option>
                      <option>Operations</option>
                      <option>Sales</option>
                      <option>Marketing</option>
                    </select>
                  </div>
                  <button onClick={createEmployee} className="btn-success">创建</button>
                </div>
              )}
              {editEmployeeFormVisible && (
                <div id="editEmployeeForm" style={{ backgroundColor: 'white', padding: '20px', borderRadius: '6px', margin: '20px 0', border: '1px solid #e0e0e0' }}>
                  <h3 style={{ marginBottom: '15px', color: '#333' }}>编辑员工信息</h3>
                  {editStatus && <div className={`status ${editStatusType}`} style={{ marginBottom: '15px' }}>{editStatus}</div>}
                  <div className="form-group">
                    <label>员工编号:</label>
                    <input type="text" id="editEmpCode" value={editEmpCode} readOnly style={{ background: '#f5f5f5' }} />
                  </div>
                  <div className="form-group">
                    <label>姓名:</label>
                    <input type="text" id="editEmpName" value={editEmpName} onChange={(e) => setEditEmpName(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label>邮箱:</label>
                    <input type="email" id="editEmpEmail" value={editEmpEmail} onChange={(e) => setEditEmpEmail(e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label>部门:</label>
                    <select id="editEmpDept" value={editEmpDept} onChange={(e) => setEditEmpDept(e.target.value)}>
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
                    <input type="text" id="editEmpPosition" value={editEmpPosition} onChange={(e) => setEditEmpPosition(e.target.value)} placeholder="可选" />
                  </div>
                  <div className="form-group">
                    <label>入职日期:</label>
                    <input type="date" id="editEmpHireDate" value={editEmpHireDate} onChange={(e) => setEditEmpHireDate(e.target.value)} />
                  </div>
                  <div className="button-group">
                    <button onClick={saveEmployeeEdit} className="btn-success">保存修改</button>
                    <button onClick={cancelEmployeeEdit} className="btn-danger">取消</button>
                  </div>
                </div>
              )}
              <div id="employeeList">
                <table>
                  <thead>
                    <tr>
                      <th>编号</th>
                      <th>姓名</th>
                      <th>邮箱</th>
                      <th>部门</th>
                      <th>操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {employeeList.map(e => {
                      const isDeactivated = e.is_deactivated ? { color: '#999', background: '#f9f9f9' } : {};
                      return (
                        <tr key={e.employee_code} style={isDeactivated}>
                          <td>{e.employee_code}</td>
                          <td>{e.full_name}</td>
                          <td>{e.email}</td>
                          <td>{e.department}</td>
                          <td>
                            <button onClick={() => editEmployeeByCode(e)} className="btn-primary" style={{ padding: '4px 8px', fontSize: '12px' }}>编辑</button>
                            <button onClick={() => deactivateEmployeeByCode(e.employee_code, e.full_name)} className="btn-danger" style={{ padding: '4px 8px', fontSize: '12px', marginLeft: '8px' }}>离职</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'department' && (
          <div id="department" className="tab-content">
            <div className="section">
              <h2>部门统计</h2>
              <div className="form-group">
                <label>选择部门:</label>
                <select id="deptSelect">
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
                <input type="date" id="deptFromDate" />
              </div>
              <div className="form-group">
                <label>结束日期:</label>
                <input type="date" id="deptToDate" />
              </div>
              <button onClick={loadDepartmentStats} className="btn-primary">加载统计</button>
              <div id="deptContent" style={{ marginTop: '20px' }} dangerouslySetInnerHTML={{ __html: deptContent }} />
            </div>
          </div>
        )}

        {activeTab === 'ranking' && (
          <div id="ranking" className="tab-content">
            <div className="section">
              <h2>准时率排行榜</h2>
              <div className="form-group">
                <label>起始日期:</label>
                <input type="date" id="rankFromDate" />
              </div>
              <div className="form-group">
                <label>结束日期:</label>
                <input type="date" id="rankToDate" />
              </div>
              <div className="form-group">
                <label>显示前几名:</label>
                <input type="number" id="rankLimit" defaultValue="10" min="1" max="50" />
              </div>
              <button onClick={loadRanking} className="btn-primary">加载排行</button>
              <div id="rankContent" style={{ marginTop: '20px' }} dangerouslySetInnerHTML={{ __html: rankContent }} />
            </div>
          </div>
        )}

        {activeTab === 'leave-request' && (
          <div id="leave-request" className="tab-content">
            <div className="section">
              <h2>提交请假申请</h2>
              {leaveStatus && <div className={`status ${leaveStatusType}`}>{leaveStatus}</div>}
              <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '6px', border: '1px solid #e0e0e0' }}>
                <div className="form-group">
                  <label>员工编号 (输入 "1" 或 "EMP001"):</label>
                  <input type="text" id="leaveEmpCode" placeholder="输入员工编号或序号" />
                </div>
                <div className="form-group">
                  <label>请假类型:</label>
                  <select id="leaveType">
                    <option value="Sick Leave">病假</option>
                    <option value="Annual Leave">年假</option>
                    <option value="Personal Leave">事假</option>
                    <option value="Unpaid Leave">无薪假</option>
                    <option value="Maternity Leave">产假</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>开始日期:</label>
                  <input type="date" id="leaveStartDate" />
                </div>
                <div className="form-group">
                  <label>结束日期:</label>
                  <input type="date" id="leaveEndDate" />
                </div>
                <div className="form-group">
                  <label>理由:</label>
                  <textarea id="leaveReason" rows="4" placeholder="请填写请假理由"></textarea>
                </div>
                <div className="button-group">
                  <button onClick={submitLeaveRequest} className="btn-primary">提交请假申请</button>
                </div>
              </div>
            </div>

            <div className="section" style={{ marginTop: '30px' }}>
              <h2>请假申请管理</h2>
              <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '6px', border: '1px solid #e0e0e0', marginBottom: '20px' }}>
                <div className="form-group">
                  <label>筛选状态:</label>
                  <select id="leaveStatusFilter">
                    <option value="">全部</option>
                    <option value="Pending">待审批</option>
                    <option value="Approved">已批准</option>
                    <option value="Rejected">已驳回</option>
                  </select>
                </div>
                <div className="button-group">
                  <button onClick={loadLeaveRequests} className="btn-primary">加载请假申请</button>
                </div>
              </div>
              <div id="leaveRequestsContent" style={{ backgroundColor: 'white', padding: '20px', borderRadius: '6px', border: '1px solid #e0e0e0' }} dangerouslySetInnerHTML={{ __html: leaveRequestsContent }} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;