import React, { useState, useEffect } from 'react';
import { approveLoan, getLoans, rejectLoan } from '../../services/adminApi';
import './Loans.css';

// Backend URL for serving static files (PDFs, videos, etc.)
const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

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

  // Filter out draft loans (incomplete applications)
  const completedLoans = loans.filter(l => l.status && l.status.toUpperCase() !== 'DRAFT');
  const draftCount = loans.length - completedLoans.length;

  return (
    <div className="loans-page">
      <div className="loans-header">
        <h1>Loans Management</h1>
        <div className="loans-subtitle">
          Total loans: <b>{completedLoans.length}</b>
          {draftCount > 0 && <span style={{ color: '#94a3b8', marginLeft: '8px' }}>({draftCount} incomplete)</span>}
        </div>
      </div>

      {actionError ? <div className="loans-error">{actionError}</div> : null}

      <div className="loans-list">
        {completedLoans.map((l) => {
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
                
                {/* Document Links */}
                <div className="loan-documents" style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {l.agreement_pdf_unsigned && (
                    <a 
                      href={`${BACKEND_BASE_URL}${l.agreement_pdf_unsigned}`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="doc-link"
                      style={{ 
                        padding: '6px 12px', 
                        background: '#EFF6FF', 
                        color: '#2563EB', 
                        borderRadius: '6px', 
                        fontSize: '12px',
                        fontWeight: '600',
                        textDecoration: 'none',
                        display: 'inline-block'
                      }}
                    >
                      📄 View Unsigned PDF
                    </a>
                  )}
                  {l.agreement_pdf_signed && (
                    <a 
                      href={`${BACKEND_BASE_URL}${l.agreement_pdf_signed}`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="doc-link"
                      style={{ 
                        padding: '6px 12px', 
                        background: '#DCFCE7', 
                        color: '#16A34A', 
                        borderRadius: '6px', 
                        fontSize: '12px',
                        fontWeight: '600',
                        textDecoration: 'none',
                        display: 'inline-block'
                      }}
                    >
                      📝 View Signed PDF
                    </a>
                  )}
                  {l.video_verification_ref && (
                    <a 
                      href={`${BACKEND_BASE_URL}${l.video_verification_ref}`} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="doc-link"
                      style={{ 
                        padding: '6px 12px', 
                        background: '#FEF3C7', 
                        color: '#D97706', 
                        borderRadius: '6px', 
                        fontSize: '12px',
                        fontWeight: '600',
                        textDecoration: 'none',
                        display: 'inline-block'
                      }}
                    >
                      🎥 View Video
                    </a>
                  )}
                  {!l.agreement_pdf_unsigned && !l.agreement_pdf_signed && !l.video_verification_ref && (
                    <span style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic' }}>No documents uploaded</span>
                  )}
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
