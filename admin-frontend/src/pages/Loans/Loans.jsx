import React, { useState, useEffect } from 'react';
import { approveLoan, getLoans, rejectLoan } from '../../services/adminApi';
import './Loans.css';

const Loans = () => {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');

  useEffect(() => {
    loadLoans();
  }, []);

  const loadLoans = async () => {
    try {
      setActionError('');
      const data = await getLoans();
      setLoans(data.items || []);
    } catch (err) {
      console.error('Failed to load loans', err);
      setActionError(err?.response?.data?.detail || err?.message || 'Failed to load loans');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (loanId) => {
    setActionLoading(true);
    setActionError('');
    try {
      await approveLoan(loanId);
      await loadLoans();
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || 'Approve failed';
      setActionError(message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (loanId) => {
    const reason = window.prompt('Reject reason (optional):') || null;
    setActionLoading(true);
    setActionError('');
    try {
      await rejectLoan(loanId, reason);
      await loadLoans();
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || 'Reject failed';
      setActionError(message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading loans...</div>;

  return (
    <div className="loans-page">
      <div className="loans-header">
        <h1>Loans Management</h1>
        <div className="loans-subtitle">Total loans: <b>{loans.length}</b></div>
      </div>

      {actionError ? <div className="loans-error">{actionError}</div> : null}

      <div className="loans-list">
        {loans.map((l) => {
          const statusText = String(l.status || '').trim();
          const isPending = statusText.toUpperCase() === 'PENDING_ADMIN_APPROVAL';
          return (
            <div key={l.loan_id} className="loan-card">
              <div className="loan-main">
                <div className="loan-top">
                  <div className="loan-id">{l.loan_id}</div>
                  <span className={`loan-badge ${isPending ? 'pending' : 'neutral'}`}>{statusText || '—'}</span>
                </div>
                <div className="loan-meta">Borrower: <b>{l.borrower_phone || '—'}</b></div>
                <div className="loan-meta">
                  Amount: <b>NPR {Number(l.amount || 0).toLocaleString()}</b> • Rate: <b>{l.interest_rate}%</b>
                </div>
              </div>

              <div className="loan-actions">
                <button className="btn btn-primary" disabled={!isPending || actionLoading} onClick={() => handleApprove(l.loan_id)}>
                  {actionLoading ? 'Working…' : 'Approve'}
                </button>
                <button className="btn btn-secondary" disabled={!isPending || actionLoading} onClick={() => handleReject(l.loan_id)}>
                  {actionLoading ? 'Working…' : 'Reject'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Loans;
