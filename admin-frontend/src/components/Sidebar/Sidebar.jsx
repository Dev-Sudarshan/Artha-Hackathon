import React from 'react';
import { NavLink } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = () => {
  const menuItems = [
    { path: '/dashboard', icon: '📊', label: 'Dashboard' },
    { path: '/borrowers', icon: '👥', label: 'Borrowers' },
    { path: '/lenders', icon: '💰', label: 'Lenders' },
    { path: '/loans', icon: '📋', label: 'Loans' },
    { path: '/kyc', icon: '🔍', label: 'KYC' },
    { path: '/transactions', icon: '💳', label: 'Transactions' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Artha Admin</h2>
      </div>
      
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => 
              `sidebar-link ${isActive ? 'active' : ''}`
            }
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span className="sidebar-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
};

export default Sidebar;
