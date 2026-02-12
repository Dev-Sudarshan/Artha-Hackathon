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
          const isVerifying = statusText.toUpperCase() === 'PENDING_VERIFICATION';
          const isStoredOnChain = l.blockchain_tx_hash != null;
          const isRepaidOnChain = l.blockchain_repayment_tx_hash != null;
          
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
                  {!l.agreement_pdf_signed && !l.video_verification_ref && (
                    <span style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic' }}>No documents uploaded</span>
                  )}
                </div>

                {isStoredOnChain && (
                  <div className="blockchain-status">
                    <div className="blockchain-header">
                      <span className={`blockchain-badge ${isRepaidOnChain ? 'repaid' : 'stored'}`}>
                        {isRepaidOnChain ? 'Repaid on Chain' : 'On Blockchain'}
                      </span>
                    </div>
                    <div className="blockchain-info">
                      <div className="tx-hash">
                        <span>TX:</span>
                        <code>{l.blockchain_tx_hash?.substring(0, 24)}...</code>
                      </div>
                      {l.blockchain_loan_hash && (
                        <div className="tx-hash">
                          <span>Hash:</span>
                          <code>{l.blockchain_loan_hash?.substring(0, 24)}...</code>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* AI Suggestion Badge */}
                {l.ai_suggestion && (
                  <div style={{ 
                    marginTop: '12px', 
                    padding: '12px 16px', 
                    background: l.ai_suggestion === 'APPROVE' ? '#DCFCE7' : l.ai_suggestion === 'REJECT' ? '#FEE2E2' : '#FEF3C7',
                    borderRadius: '10px',
                    border: `2px solid ${l.ai_suggestion === 'APPROVE' ? '#16A34A' : l.ai_suggestion === 'REJECT' ? '#DC2626' : '#F59E0B'}`,
                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                      <span style={{ 
                        fontWeight: '800', 
                        fontSize: '13px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.5px',
                        color: l.ai_suggestion === 'APPROVE' ? '#16A34A' : l.ai_suggestion === 'REJECT' ? '#DC2626' : '#F59E0B'
                      }}>
                        🤖 AI Suggests: {l.ai_suggestion}
                      </span>
                    </div>
                    <div style={{ fontSize: '12px', color: '#64748b', fontWeight: '600' }}>
                      {l.video_verification_result?.face_match ? '✅ Image matches' : l.video_verification_result?.face_match === false ? '❌ Image does not match' : l.ai_suggestion_reason || 'Requires manual review'}
                    </div>
                  </div>
                )}

                {/* Verification Status or Results */}
                {isVerifying && !l.video_verification_result && (
                  <div style={{ 
                    marginTop: '12px', 
                    padding: '12px', 
                    background: '#F0F9FF',
                    borderRadius: '8px',
                    border: '1px solid #3B82F6'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ 
                        width: '16px', 
                        height: '16px', 
                        border: '2px solid #3B82F6', 
                        borderTopColor: 'transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }}></div>
                      <span style={{ 
                        fontWeight: '700', 
                        fontSize: '12px',
                        color: '#3B82F6'
                      }}>
                        AI Verification in Progress...
                      </span>
                    </div>
                  </div>
                )}

                {/* Face Verification Results with Photo Comparison */}
                {l.video_verification_result && (
                  <div style={{ 
                    marginTop: '12px', 
                    padding: '14px', 
                    background: l.video_verification_result.face_match ? '#F0FDF4' : '#FEF2F2',
                    borderRadius: '10px',
                    border: `2px solid ${l.video_verification_result.face_match ? '#16A34A' : '#DC2626'}`
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span style={{ 
                        fontWeight: '800', 
                        fontSize: '12px',
                        textTransform: 'uppercase',
                        color: l.video_verification_result.face_match ? '#16A34A' : '#DC2626'
                      }}>
                        {l.video_verification_result.face_match ? '✅ Face Matched' : '❌ Face Mismatch'}
                      </span>
                      {l.video_verification_result.face_distance && (
                        <span style={{ fontSize: '11px', color: '#64748b', fontWeight: '600' }}>
                          Score: {(1 - l.video_verification_result.face_distance).toFixed(3)}
                        </span>
                      )}
                    </div>
                    
                    {/* Photo Comparison */}
                    {l.kyc_selfie_ref && (
                      <div>
                        <div style={{ fontSize: '10px', color: '#64748b', marginBottom: '8px', fontWeight: '700', textTransform: 'uppercase' }}>
                          Photo Comparison:
                        </div>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', background: 'white', padding: '12px', borderRadius: '8px' }}>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '10px', color: '#64748b', marginBottom: '6px', fontWeight: '600' }}>KYC Live Photo</div>
                            <img 
                              src={`${BACKEND_BASE_URL}${l.kyc_selfie_ref}`} 
                              alt="KYC Selfie" 
                              style={{ 
                                width: '80px', 
                                height: '80px', 
                                objectFit: 'cover', 
                                borderRadius: '8px', 
                                border: '3px solid #3B82F6',
                                boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
                              }}
                            />
                          </div>
                          <div style={{ fontSize: '20px', color: '#94a3b8', fontWeight: 'bold' }}>⟷</div>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '10px', color: '#64748b', marginBottom: '6px', fontWeight: '600' }}>Video Extracted Frame</div>
                            {l.video_frame_ref ? (
                              <img 
                                src={`${BACKEND_BASE_URL}${l.video_frame_ref}`}
                                alt="Video Frame"
                                style={{ 
                                  width: '80px', 
                                  height: '80px', 
                                  objectFit: 'cover', 
                                  borderRadius: '8px', 
                                  border: '3px solid #F59E0B',
                                  boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
                                }}
                              />
                            ) : (
                              <div style={{ 
                                width: '80px', 
                                height: '80px', 
                                background: '#F3F4F6',
                                borderRadius: '8px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '10px',
                                color: '#9CA3AF'
                              }}>No Frame</div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>

              <div className="loan-actions">
                {isPending ? (
                  <>
                    <button className="btn btn-primary" disabled={actionLoading} onClick={() => handleApprove(l.loan_id)}>
                      {actionLoading ? 'Working…' : 'Approve'}
                    </button>
                    <button className="btn btn-secondary" disabled={actionLoading} onClick={() => handleReject(l.loan_id)}>
                      {actionLoading ? 'Working…' : 'Reject'}
                    </button>
                  </>
                ) : isVerifying ? (
                  <div style={{ 
                    padding: '12px 20px',
                    fontSize: '13px', 
                    color: '#3B82F6', 
                    fontWeight: '600',
                    textAlign: 'center',
                    background: '#F0F9FF',
                    borderRadius: '10px',
                    border: '2px solid #3B82F6'
                  }}>
                    🔄 AI Verification in Progress...
                  </div>
                ) : statusText.toUpperCase() === 'LISTED' ? (
                  <div style={{ 
                    padding: '12px 20px',
                    fontSize: '14px', 
                    color: '#16A34A', 
                    fontWeight: '700',
                    textAlign: 'center',
                    background: '#DCFCE7',
                    borderRadius: '10px',
                    border: '2px solid #16A34A'
                  }}>
                    ✅ Approved
                  </div>
                ) : statusText.toUpperCase() === 'REJECTED' ? (
                  <div style={{ 
                    padding: '12px 20px',
                    fontSize: '14px', 
                    color: '#DC2626', 
                    fontWeight: '700',
                    textAlign: 'center',
                    background: '#FEE2E2',
                    borderRadius: '10px',
                    border: '2px solid #DC2626'
                  }}>
                    ❌ Rejected
                  </div>
                ) : (
                  <div style={{ 
                    padding: '12px 20px',
                    fontSize: '13px', 
                    color: '#64748b', 
                    fontWeight: '600',
                    textAlign: 'center',
                    background: '#F8FAFC',
                    borderRadius: '10px',
                    border: '2px solid #E2E8F0'
                  }}>
                    {statusText}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Loans;
