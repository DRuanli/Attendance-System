// frontend/src/pages/Reports/Reports.js
import React, { useState } from 'react';
import { reportAPI } from '../../services/api';
import { format } from 'date-fns';
import { FiDownload } from 'react-icons/fi';

const Reports = () => {
  const [reportType, setReportType] = useState('attendance');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const classroomId = 1; // Default classroom

  const handleGenerateReport = async () => {
    if (!startDate || !endDate) {
      return;
    }

    try {
      const response = await reportAPI.getClassroomReport(classroomId, {
        start_date: startDate,
        end_date: endDate,
        format: 'csv'
      });

      // Download CSV
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `attendance_report_${startDate}_${endDate}.csv`;
      a.click();
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };

  return (
    <div className="reports-page">
      <h1>Reports</h1>

      <div className="report-form">
        <div className="form-group">
          <label>Report Type</label>
          <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
            <option value="attendance">Attendance Report</option>
            <option value="summary">Summary Report</option>
          </select>
        </div>

        <div className="form-group">
          <label>Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
          />
        </div>

        <div className="form-group">
          <label>End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
          />
        </div>

        <button onClick={handleGenerateReport} className="btn btn-primary">
          <FiDownload /> Generate Report
        </button>
      </div>
    </div>
  );
};

export default Reports;
