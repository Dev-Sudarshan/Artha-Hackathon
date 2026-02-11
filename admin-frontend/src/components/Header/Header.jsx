import React from 'react';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { useNavigate } from 'react-router-dom';
import './Header.css';

const Header = () => {
  const { admin, logout } = useAdminAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="admin-header">
      <div className="header-content">
        <div className="header-left">
          <h1>Admin Panel</h1>
        </div>
        
        <div className="header-right">
          <div className="admin-info">
            <span className="admin-email">{admin?.email}</span>
            <span className="admin-role">{admin?.role || 'Admin'}</span>
          </div>
          <button onClick={handleLogout} className="logout-button">
            Logout
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
