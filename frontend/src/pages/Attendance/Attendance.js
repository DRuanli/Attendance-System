// frontend/src/pages/Attendance/Attendance.js
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FiCamera, FiUser } from 'react-icons/fi';
import { attendanceAPI, studentAPI } from '../../services/api';
import { toast } from 'react-toastify';

const Attendance = () => {
  const [students, setStudents] = useState([]);
  const [selectedStudent, setSelectedStudent] = useState('');
  const classroomId = 1; // Default classroom

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      const response = await studentAPI.getAll({ limit: 100 });
      setStudents(response.data);
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  const handleManualAttendance = async () => {
    if (!selectedStudent) {
      toast.error('Please select a student');
      return;
    }

    try {
      await attendanceAPI.markManual({
        student_id: selectedStudent,
        classroom_id: classroomId
      });
      toast.success('Attendance marked successfully');
      setSelectedStudent('');
    } catch (error) {
      console.error('Error marking attendance:', error);
    }
  };

  return (
    <div className="attendance-page">
      <h1>Attendance Management</h1>

      <div className="attendance-options">
        <div className="option-card">
          <FiCamera size={48} />
          <h3>Live Camera Attendance</h3>
          <p>Use face recognition to automatically mark attendance</p>
          <Link to={`/attendance/live/${classroomId}`} className="btn btn-primary">
            Start Live Session
          </Link>
        </div>

        <div className="option-card">
          <FiUser size={48} />
          <h3>Manual Attendance</h3>
          <p>Mark attendance manually for individual students</p>
          <div className="manual-form">
            <select
              value={selectedStudent}
              onChange={(e) => setSelectedStudent(e.target.value)}
            >
              <option value="">Select Student</option>
              {students.map(student => (
                <option key={student.id} value={student.student_id}>
                  {student.full_name} ({student.student_id})
                </option>
              ))}
            </select>
            <button onClick={handleManualAttendance} className="btn btn-secondary">
              Mark Present
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Attendance;
