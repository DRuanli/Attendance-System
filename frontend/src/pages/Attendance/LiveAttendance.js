// frontend/src/pages/Attendance/LiveAttendance.js
import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Webcam from 'react-webcam';
import { attendanceAPI } from '../../services/api';
import { toast } from 'react-toastify';
import './LiveAttendance.css';

const LiveAttendance = () => {
  const { classroomId } = useParams();
  const webcamRef = useRef(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [attendanceList, setAttendanceList] = useState([]);
  const intervalRef = useRef(null);

  useEffect(() => {
    fetchTodayAttendance();
    startAttendanceSession();

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      stopAttendanceSession();
    };
  }, [classroomId]);

  const startAttendanceSession = async () => {
    try {
      await attendanceAPI.startSession(parseInt(classroomId));
    } catch (error) {
      console.error('Error starting session:', error);
    }
  };

  const stopAttendanceSession = async () => {
    try {
      await attendanceAPI.stopSession();
    } catch (error) {
      console.error('Error stopping session:', error);
    }
  };

  const fetchTodayAttendance = async () => {
    try {
      const response = await attendanceAPI.getTodayAttendance(classroomId);
      setAttendanceList(response.data);
    } catch (error) {
      console.error('Error fetching attendance:', error);
    }
  };

  const captureAndProcessFrame = useCallback(async () => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      if (imageSrc) {
        try {
          // Convert base64 to blob
          const base64Response = await fetch(imageSrc);
          const blob = await base64Response.blob();

          // Create FormData
          const formData = new FormData();
          formData.append('classroom_id', classroomId);
          formData.append('image', blob, 'frame.jpg');

          // Send to backend
          const response = await attendanceAPI.processFrame(formData);

          if (response.data.recognized_count > 0) {
            toast.success(`Recognized ${response.data.recognized_count} student(s)`);
            fetchTodayAttendance();
          }
        } catch (error) {
          console.error('Error processing frame:', error);
        }
      }
    }
  }, [classroomId]);

  const startCapturing = () => {
    setIsCapturing(true);
    // Capture frame every 3 seconds
    intervalRef.current = setInterval(() => {
      captureAndProcessFrame();
    }, 3000);
    toast.success('Live attendance started');
  };

  const stopCapturing = () => {
    setIsCapturing(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    toast.info('Live attendance stopped');
  };

  const webcamConstraints = {
    width: 640,
    height: 480,
    facingMode: "user"
  };

  return (
    <div className="live-attendance">
      <div className="camera-section">
        <h2>Live Camera Feed</h2>
        <div className="camera-container">
          <Webcam
            ref={webcamRef}
            audio={false}
            screenshotFormat="image/jpeg"
            videoConstraints={webcamConstraints}
            style={{ width: '100%', maxWidth: '640px' }}
          />
        </div>
        <div className="camera-controls">
          {!isCapturing ? (
            <button onClick={startCapturing} className="btn btn-primary">
              Start Live Attendance
            </button>
          ) : (
            <button onClick={stopCapturing} className="btn btn-danger">
              Stop Capturing
            </button>
          )}
        </div>
      </div>

      <div className="attendance-section">
        <h2>Today's Attendance</h2>
        <div className="attendance-stats">
          <div className="stat">
            <span>Present:</span>
            <strong>{attendanceList.filter(a => a.status === 'present').length}</strong>
          </div>
          <div className="stat">
            <span>Late:</span>
            <strong>{attendanceList.filter(a => a.status === 'late').length}</strong>
          </div>
          <div className="stat">
            <span>Total:</span>
            <strong>{attendanceList.length}</strong>
          </div>
        </div>

        <div className="attendance-table">
          <table>
            <thead>
              <tr>
                <th>Student ID</th>
                <th>Name</th>
                <th>Check-in Time</th>
                <th>Status</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {attendanceList.map((record) => (
                <tr key={record.id}>
                  <td>{record.student_id}</td>
                  <td>{record.student_name}</td>
                  <td>{new Date(record.check_in_time).toLocaleTimeString()}</td>
                  <td>
                    <span className={`status ${record.status}`}>{record.status}</span>
                  </td>
                  <td>{(record.confidence_score * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LiveAttendance;