// frontend/src/components/Layout/Layout.js
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { FiHome, FiUsers, FiCheckCircle, FiFileText, FiGrid } from 'react-icons/fi';
import './Layout.css';

const Layout = ({ children }) => {
  const location = useLocation();

  const menuItems = [
    { path: '/dashboard', name: 'Dashboard', icon: <FiHome /> },
    { path: '/students', name: 'Students', icon: <FiUsers /> },
    { path: '/attendance', name: 'Attendance', icon: <FiCheckCircle /> },
    { path: '/classrooms', name: 'Classrooms', icon: <FiGrid /> },
    { path: '/reports', name: 'Reports', icon: <FiFileText /> },
  ];

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="logo">
          <h2>Attendance System</h2>
        </div>
        <nav className="nav-menu">
          {menuItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-item ${location.pathname.startsWith(item.path) ? 'active' : ''}`}
            >
              {item.icon}
              <span>{item.name}</span>
            </Link>
          ))}
        </nav>
      </aside>
      <main className="main-content">
        <header className="header">
          <h1>{menuItems.find(item => location.pathname.startsWith(item.path))?.name || 'Attendance System'}</h1>
        </header>
        <div className="content">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;