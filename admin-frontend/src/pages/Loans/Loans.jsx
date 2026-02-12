import React, { useState, useEffect } from 'react';
import { approveLoan, getLoans, rejectLoan, storeOnBlockchain, verifyOnBlockchain, markRepaidOnBlockchain } from '../../services/adminApi';
import './Loans.css';

// Backend URL for serving static files (PDFs, videos, etc.)
const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const Loans = () => {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');
  const [blockchainLoading, setBlockchainLoading] = useState({});
  const [blockchainSuccess, setBlockchainSuccess] = useState('');

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

  const handleStoreBlockchain = async (loanId) => {
    setBlockchainLoading((prev) => ({ ...prev, [loanId]: true }));
    setActionError('');
    setBlockchainSuccess('');
    try {
      const result = await storeOnBlockchain(loanId);
      setBlockchainSuccess(`Stored on blockchain. TX: ${result.txid?.substring(0, 16)}...`);
      await loadLoans();
    } catch (err) {
      setActionError(err?.response?.data?.detail || err?.message || 'Blockchain store failed');
    } finally {
      setBlockchainLoading((prev) => ({ ...prev, [loanId]: false }));
    }
  };

  const handleVerifyBlockchain = async (loanId) => {
    setBlockchainLoading((prev) => ({ ...prev, [loanId]: true }));
    setActionError('');
    setBlockchainSuccess('');
    try {
      const result = await verifyOnBlockchain(loanId);
      if (result.verified) {
        setBlockchainSuccess('Verified. Data integrity confirmed.');
      } else {
        setActionError('Verification failed: Data mismatch detected.');
      }
    } catch (err) {
      setActionError(err?.response?.data?.detail || err?.message || 'Blockchain verify failed');
    } finally {
      setBlockchainLoading((prev) => ({ ...prev, [loanId]: false }));
    }
  };

  const handleMarkRepaidOnBlockchain = async (loanId) => {
    setBlockchainLoading((prev) => ({ ...prev, [loanId]: true }));
    setActionError('');
    setBlockchainSuccess('');
    try {
      const result = await markRepaidOnBlockchain(loanId);
      setBlockchainSuccess(`Marked as repaid on blockchain. TX: ${result.txid?.substring(0, 16)}...`);
      await loadLoans();
    } catch (err) {
      setActionError(err?.response?.data?.detail || err?.message || 'Mark repaid failed');
    } finally {
      setBlockchainLoading((prev) => ({ ...prev, [loanId]: false }));
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
      {blockchainSuccess ? <div className="loans-success">{blockchainSuccess}</div> : null}

      <div className="loans-list">
        {completedLoans.map((l) => {
          const statusText = String(l.status || '').trim();
          const isPending = statusText.toUpperCase() === 'PENDING_ADMIN_APPROVAL';
          const isListedOrActive = ['LISTED', 'ACTIVE', 'AWAITING_SIGNATURE', 'REPAID'].includes(statusText.toUpperCase());
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
              </div>

              <div className="loan-actions">
                <button className="btn btn-primary" disabled={!isPending || actionLoading} onClick={() => handleApprove(l.loan_id)}>
                  {actionLoading ? 'Working…' : 'Approve'}
                </button>
                <button className="btn btn-secondary" disabled={!isPending || actionLoading} onClick={() => handleReject(l.loan_id)}>
                  {actionLoading ? 'Working…' : 'Reject'}
                </button>

                {isListedOrActive && !isStoredOnChain && (
                  <button 
                    className="btn btn-blockchain" 
                    disabled={blockchainLoading[l.loan_id]} 
                    onClick={() => handleStoreBlockchain(l.loan_id)}
                    title="Store loan data on blockchain"
                  >
                    {blockchainLoading[l.loan_id] ? 'Working...' : 'Store on Chain'}
                  </button>
                )}

                {isStoredOnChain && (
                  <>
                    <button 
                      className="btn btn-verify" 
                      disabled={blockchainLoading[l.loan_id]} 
                      onClick={() => handleVerifyBlockchain(l.loan_id)}
                      title="Verify data integrity with blockchain"
                    >
                      {blockchainLoading[l.loan_id] ? 'Working...' : 'Verify'}
                    </button>

                    <button 
                      className="btn btn-certificate" 
                      onClick={() => window.open(`http://localhost:8000/api/blockchain/certificate/${l.loan_id}`, '_blank')}
                      title="Download blockchain certificate PDF"
                    >
                      Certificate
                    </button>
                    
                    {!isRepaidOnChain && (
                      <button 
                        className="btn btn-repaid" 
                        disabled={blockchainLoading[l.loan_id]} 
                        onClick={() => handleMarkRepaidOnBlockchain(l.loan_id)}
                        title="Mark loan as repaid on blockchain"
                      >
                        {blockchainLoading[l.loan_id] ? 'Working...' : 'Mark Repaid'}
                      </button>
                    )}
                  </>
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
