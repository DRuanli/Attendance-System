// frontend/src/services/api.js
import axios from 'axios';
import { toast } from 'react-toastify';

const API_BASE_URL = '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      toast.error(error.response.data.detail || 'An error occurred');
    } else if (error.request) {
      toast.error('Network error. Please check your connection.');
    } else {
      toast.error('An unexpected error occurred');
    }
    return Promise.reject(error);
  }
);

// Student APIs
export const studentAPI = {
  getAll: (params) => api.get('/students', { params }),
  getById: (studentId) => api.get(`/students/${studentId}`),
  register: (formData) => api.post('/students/register', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deactivate: (studentId) => api.put(`/students/${studentId}/deactivate`),
};

// Attendance APIs
export const attendanceAPI = {
  markManual: (data) => api.post('/attendance/mark', data),
  processFrame: (classroomId) => api.post('/attendance/process-frame', { classroom_id: classroomId }),
  getTodayAttendance: (classroomId) => api.get(`/attendance/classroom/${classroomId}/today`),
  getStudentHistory: (studentId, params) => api.get(`/attendance/student/${studentId}/history`, { params }),
};

// Reports APIs
export const reportAPI = {
  getClassroomReport: (classroomId, params) =>
    api.get(`/reports/classroom/${classroomId}/attendance-report`, { params }),
  getClassroomStats: (classroomId) =>
    api.get(`/reports/statistics/classroom/${classroomId}`),
};

export default api;