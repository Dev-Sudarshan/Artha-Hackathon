import React, { useState, useEffect } from 'react';
import { getDashboard } from '../../services/adminApi';
import './Dashboard.css';

const Dashboard = () => {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const data = await getDashboard();
      setDashboard(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error-box">{error}</div>;
  }

  return (
    <div className="dashboard-container">
      <h1>Dashboard Overview</h1>
      
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-icon">📊</div>
          <div className="kpi-content">
            <h3>Active Loans</h3>
            <p className="kpi-value">{dashboard?.kpis?.active_loans || 0}</p>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon">⚠️</div>
          <div className="kpi-content">
            <h3>Default Rate</h3>
            <p className="kpi-value">{dashboard?.kpis?.default_rate || '0%'}</p>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon">🔍</div>
          <div className="kpi-content">
            <h3>Pending KYC</h3>
            <p className="kpi-value">{dashboard?.kpis?.pending_kyc || 0}</p>
          </div>
        </div>

        <div className="kpi-card">
          <div className="kpi-icon">🚩</div>
          <div className="kpi-content">
            <h3>Flagged Accounts</h3>
            <p className="kpi-value">{dashboard?.kpis?.flagged_accounts || 0}</p>
          </div>
        </div>
      </div>

      {dashboard?.watchlist && dashboard.watchlist.length > 0 && (
        <div className="dashboard-section">
          <h2>Watchlist</h2>
          <div className="watchlist-grid">
            {dashboard.watchlist.map((item, index) => (
              <div key={index} className="watchlist-item">
                <p className="watchlist-name">{item.label}</p>
                <p className="watchlist-reason">
                  {item.risk_level} • Amount: {item.value}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {dashboard?.alerts && dashboard.alerts.length > 0 && (
        <div className="dashboard-section">
          <h2>Recent Alerts</h2>
          <div className="alerts-list">
            {dashboard.alerts.map((alert, index) => (
              <div key={index} className={`alert-item alert-${String(alert.status || '').toLowerCase()}`}>
                <span className="alert-severity">{alert.status}</span>
                <span className="alert-message">{alert.label}: {alert.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
