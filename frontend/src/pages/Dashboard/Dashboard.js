// frontend/src/pages/Dashboard/Dashboard.js
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FiUsers, FiCheckCircle, FiClock, FiAlertCircle } from 'react-icons/fi';
import { reportAPI, attendanceAPI, studentAPI } from '../../services/api';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalStudents: 0,
    todayAttendance: 0,
    lateArrivals: 0,
    absentees: 0,
  });
  const [recentAttendance, setRecentAttendance] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // For demo, using classroom ID 1
      const [statsRes, attendanceRes, studentsRes] = await Promise.all([
        reportAPI.getClassroomStats(1),
        attendanceAPI.getTodayAttendance(1),
        studentAPI.getAll({ limit: 100 })
      ]);

      setStats({
        totalStudents: studentsRes.data.length,
        todayAttendance: attendanceRes.data.filter(a => a.status === 'present').length,
        lateArrivals: attendanceRes.data.filter(a => a.status === 'late').length,
        absentees: studentsRes.data.length - attendanceRes.data.length,
      });

      setRecentAttendance(attendanceRes.data.slice(0, 5));
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card">
          <FiUsers className="stat-icon" />
          <div className="stat-content">
            <h3>Total Students</h3>
            <p className="stat-value">{stats.totalStudents}</p>
          </div>
        </div>
        <div className="stat-card success">
          <FiCheckCircle className="stat-icon" />
          <div className="stat-content">
            <h3>Present Today</h3>
            <p className="stat-value">{stats.todayAttendance}</p>
          </div>
        </div>
        <div className="stat-card warning">
          <FiClock className="stat-icon" />
          <div className="stat-content">
            <h3>Late Arrivals</h3>
            <p className="stat-value">{stats.lateArrivals}</p>
          </div>
        </div>
        <div className="stat-card danger">
          <FiAlertCircle className="stat-icon" />
          <div className="stat-content">
            <h3>Absent Today</h3>
            <p className="stat-value">{stats.absentees}</p>
          </div>
        </div>
      </div>

      <div className="dashboard-content">
        <div className="recent-attendance">
          <h2>Recent Attendance</h2>
          <div className="attendance-list">
            {recentAttendance.map((attendance) => (
              <div key={attendance.id} className="attendance-item">
                <div className="student-info">
                  <h4>{attendance.student_name}</h4>
                  <p>{attendance.student_id}</p>
                </div>
                <div className="attendance-info">
                  <span className={`status ${attendance.status}`}>{attendance.status}</span>
                  <span className="time">
                    {new Date(attendance.check_in_time).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="quick-actions">
          <h2>Quick Actions</h2>
          <div className="action-buttons">
            <Link to="/attendance/live/1" className="action-btn primary">
              Start Live Attendance
            </Link>
            <Link to="/students/register" className="action-btn secondary">
              Register New Student
            </Link>
            <Link to="/reports" className="action-btn info">
              View Reports
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;