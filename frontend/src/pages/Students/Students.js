// frontend/src/pages/Students/Students.js
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FiPlus, FiEdit, FiTrash2 } from 'react-icons/fi';
import { studentAPI } from '../../services/api';
import { toast } from 'react-toastify';
import './Students.css';

const Students = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      const response = await studentAPI.getAll({ limit: 100 });
      setStudents(response.data);
    } catch (error) {
      console.error('Error fetching students:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeactivate = async (studentId) => {
    if (window.confirm('Are you sure you want to deactivate this student?')) {
      try {
        await studentAPI.deactivate(studentId);
        toast.success('Student deactivated successfully');
        fetchStudents();
      } catch (error) {
        console.error('Error deactivating student:', error);
      }
    }
  };

  if (loading) return <div className="loading">Loading...</div>;

  return (
    <div className="students-page">
      <div className="page-header">
        <h1>Students</h1>
        <Link to="/students/register" className="btn btn-primary">
          <FiPlus /> Register New Student
        </Link>
      </div>

      <div className="students-table">
        <table>
          <thead>
            <tr>
              <th>Student ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Status</th>
              <th>Registered</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {students.map((student) => (
              <tr key={student.id}>
                <td>{student.student_id}</td>
                <td>{student.full_name}</td>
                <td>{student.email}</td>
                <td>
                  <span className={`status ${student.is_active ? 'active' : 'inactive'}`}>
                    {student.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td>{new Date(student.created_at).toLocaleDateString()}</td>
                <td>
                  <button
                    className="btn-icon"
                    onClick={() => handleDeactivate(student.student_id)}
                  >
                    <FiTrash2 />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Students;