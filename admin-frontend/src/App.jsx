import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AdminAuthProvider, useAdminAuth } from './context/AdminAuthContext';
import AdminLogin from './pages/AdminLogin/AdminLogin';
import Dashboard from './pages/Dashboard/Dashboard';
import Borrowers from './pages/Borrowers/Borrowers';
import Lenders from './pages/Lenders/Lenders';
import Loans from './pages/Loans/Loans';
import KYC from './pages/KYC/KYC';
import Transactions from './pages/Transactions/Transactions';
import Sidebar from './components/Sidebar/Sidebar';
import Header from './components/Header/Header';
import './App.css';

const ProtectedRoute = ({ children }) => {
  const { admin, loading } = useAdminAuth();

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (!admin) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="admin-layout">
      <Sidebar />
      <div className="admin-main">
        <Header />
        <main className="admin-content">
          {children}
        </main>
      </div>
    </div>
  );
};

const LoginRoute = () => {
  const { admin, loading } = useAdminAuth();

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  if (admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <AdminLogin />;
};

function App() {
  return (
    <AdminAuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LoginRoute />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/borrowers"
            element={
              <ProtectedRoute>
                <Borrowers />
              </ProtectedRoute>
            }
          />
          <Route
            path="/lenders"
            element={
              <ProtectedRoute>
                <Lenders />
              </ProtectedRoute>
            }
          />
          <Route
            path="/loans"
            element={
              <ProtectedRoute>
                <Loans />
              </ProtectedRoute>
            }
          />
          <Route
            path="/kyc"
            element={
              <ProtectedRoute>
                <KYC />
              </ProtectedRoute>
            }
          />
          <Route
            path="/transactions"
            element={
              <ProtectedRoute>
                <Transactions />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AdminAuthProvider>
  );
}

export default App;
