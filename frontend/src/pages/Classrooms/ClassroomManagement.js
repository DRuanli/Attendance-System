// frontend/src/pages/Classrooms/ClassroomManagement.js
import React from 'react';

const ClassroomManagement = () => {
  const classrooms = [
    {
      id: 1,
      course_code: 'CS101',
      course_name: 'Introduction to Computer Science',
      instructor: 'Dr. Smith',
      room: 'A201',
      schedule: 'Mon 9:00-10:30'
    }
  ];

  return (
    <div className="classrooms-page">
      <h1>Classroom Management</h1>

      <div className="classrooms-grid">
        {classrooms.map(classroom => (
          <div key={classroom.id} className="classroom-card">
            <h3>{classroom.course_code}</h3>
            <p>{classroom.course_name}</p>
            <div className="classroom-details">
              <p><strong>Instructor:</strong> {classroom.instructor}</p>
              <p><strong>Room:</strong> {classroom.room}</p>
              <p><strong>Schedule:</strong> {classroom.schedule}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ClassroomManagement;