// frontend/src/pages/Students/StudentRegistration.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { studentAPI } from '../../services/api';
import { toast } from 'react-toastify';
import './StudentRegistration.css';

const StudentRegistration = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    student_id: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: ''
  });
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(false);

  const { getRootProps, getInputProps } = useDropzone({
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png']
    },
    maxFiles: 5,
    onDrop: (acceptedFiles) => {
      setPhotos([...photos, ...acceptedFiles].slice(0, 5));
    }
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (photos.length < 3) {
      toast.error('Please upload at least 3 photos');
      return;
    }

    setLoading(true);
    const data = new FormData();

    Object.keys(formData).forEach(key => {
      data.append(key, formData[key]);
    });

    photos.forEach(photo => {
      data.append('photos', photo);
    });

    try {
      await studentAPI.register(data);
      toast.success('Student registered successfully!');
      navigate('/students');
    } catch (error) {
      console.error('Registration error:', error);
    } finally {
      setLoading(false);
    }
  };

  const removePhoto = (index) => {
    setPhotos(photos.filter((_, i) => i !== index));
  };

  return (
    <div className="registration-page">
      <h1>Register New Student</h1>

      <form onSubmit={handleSubmit} className="registration-form">
        <div className="form-grid">
          <div className="form-group">
            <label>Student ID*</label>
            <input
              type="text"
              name="student_id"
              value={formData.student_id}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>First Name*</label>
            <input
              type="text"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Last Name*</label>
            <input
              type="text"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Email*</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>

          <div className="form-group">
            <label>Phone</label>
            <input
              type="tel"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
            />
          </div>
        </div>

        <div className="photo-section">
          <h3>Upload Photos (Minimum 3 required)</h3>
          <div {...getRootProps()} className="dropzone">
            <input {...getInputProps()} />
            <p>Drag & drop photos here, or click to select</p>
          </div>

          <div className="photo-preview">
            {photos.map((photo, index) => (
              <div key={index} className="photo-item">
                <img src={URL.createObjectURL(photo)} alt={`Preview ${index}`} />
                <button type="button" onClick={() => removePhoto(index)}>×</button>
              </div>
            ))}
          </div>
        </div>

        <div className="form-actions">
          <button type="button" onClick={() => navigate('/students')} className="btn btn-secondary">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary">
            {loading ? 'Registering...' : 'Register Student'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default StudentRegistration;