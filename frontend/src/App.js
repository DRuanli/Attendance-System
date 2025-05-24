// frontend/src/App.js
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

// Layout
import Layout from './components/Layout/Layout';

// Pages
import Dashboard from './pages/Dashboard/Dashboard';
import Students from './pages/Students/Students';
import StudentRegistration from './pages/Students/StudentRegistration';
import Attendance from './pages/Attendance/Attendance';
import LiveAttendance from './pages/Attendance/LiveAttendance';
import Reports from './pages/Reports/Reports';
import ClassroomManagement from './pages/Classrooms/ClassroomManagement';

import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/students" element={<Students />} />
            <Route path="/students/register" element={<StudentRegistration />} />
            <Route path="/attendance" element={<Attendance />} />
            <Route path="/attendance/live/:classroomId" element={<LiveAttendance />} />
            <Route path="/reports" element={<Reports />} />
            <Route path="/classrooms" element={<ClassroomManagement />} />
          </Routes>
        </Layout>
        <ToastContainer position="top-right" autoClose={3000} />
      </div>
    </Router>
  );
}

export default App;