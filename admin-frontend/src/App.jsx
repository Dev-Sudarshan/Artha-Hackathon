import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AdminAuthProvider, useAdminAuth } from './context/AdminAuthContext';
import AdminLogin from './pages/AdminLogin/AdminLogin';
import Sidebar from './components/Sidebar/Sidebar';
import Header from './components/Header/Header';
import './App.css';

// Lazy load admin pages
const Dashboard = lazy(() => import('./pages/Dashboard/Dashboard'));
const Borrowers = lazy(() => import('./pages/Borrowers/Borrowers'));
const Lenders = lazy(() => import('./pages/Lenders/Lenders'));
const Loans = lazy(() => import('./pages/Loans/Loans'));
const KYC = lazy(() => import('./pages/KYC/KYC'));
const Transactions = lazy(() => import('./pages/Transactions/Transactions'));
const BlockchainExplorer = lazy(() => import('./pages/BlockchainExplorer/BlockchainExplorer'));

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
          <Suspense fallback={<div className="loading-screen">Loading...</div>}>
            {children}
          </Suspense>
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
          <Route
            path="/blockchain-explorer"
            element={
              <ProtectedRoute>
                <BlockchainExplorer />
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
