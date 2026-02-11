import React, { useMemo, useState, useEffect } from 'react';
import { approveKyc, getKycRecord, getKycRecords, rejectKyc } from '../../services/adminApi';
import './KYC.css';

const KYC = () => {
  const [kycRecords, setKycRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPhone, setSelectedPhone] = useState(null);
  const [selectedDetails, setSelectedDetails] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');

  useEffect(() => {
    loadKycRecords();
  }, []);

  const loadKycRecords = async () => {
    try {
      const data = await getKycRecords();
      setKycRecords(data.items || []);
    } catch (err) {
      console.error('Failed to load KYC records', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDetails = async (phone) => {
    try {
      setActionError('');
      setSelectedPhone(phone);
      const data = await getKycRecord(phone);
      setSelectedDetails(data);
    } catch (err) {
      console.error('Failed to load KYC details', err);
      setSelectedDetails(null);
    }
  };

  const normalizeUrl = (url) => {
    if (!url) return null;
    const text = String(url).replaceAll('\\\\', '/').replaceAll('\\', '/');
    if (text.startsWith('/')) return `http://127.0.0.1:8000${text}`;
    if (text.startsWith('static/')) return `http://127.0.0.1:8000/${text}`;
    return text;
  };

  const canReview = useMemo(() => {
    if (!selectedDetails?.status) return false;
    return String(selectedDetails.status).trim().toUpperCase().includes('PENDING');
  }, [selectedDetails]);

  const statusTone = (status) => {
    const s = String(status || '').trim().toUpperCase();
    if (s.includes('PENDING')) return 'pending';
    if (s === 'APPROVED') return 'approved';
    if (s === 'REJECTED') return 'rejected';
    return 'neutral';
  };

  const handleApprove = async () => {
    if (!selectedPhone) return;
    setActionLoading(true);
    setActionError('');
    try {
      await approveKyc(selectedPhone);
      await loadDetails(selectedPhone);
      await loadKycRecords();
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || 'Approve failed';
      setActionError(message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedPhone) return;
    const reason = window.prompt('Reject reason (optional):') || null;
    setActionLoading(true);
    setActionError('');
    try {
      await rejectKyc(selectedPhone, reason);
      await loadDetails(selectedPhone);
      await loadKycRecords();
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || 'Reject failed';
      setActionError(message);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading KYC records...</div>;

  return (
    <div className="kyc-page">
      <div className="kyc-header">
        <h1>KYC Management</h1>
        <div className="kyc-subtitle">Total records: <b>{kycRecords.length}</b></div>
      </div>

      <div className="kyc-grid">
        <section className="kyc-panel">
          <div className="kyc-panel-title">Applicants</div>
          <div className="kyc-list">
            {kycRecords.map((r) => {
              const active = selectedPhone === r.user_phone;
              const tone = statusTone(r.status);
              return (
                <button
                  key={r.user_phone}
                  onClick={() => loadDetails(r.user_phone)}
                  className={`kyc-item ${active ? 'active' : ''}`}
                >
                  <div className="kyc-item-top">
                    <div className="kyc-name">{r.full_name || r.user_phone}</div>
                    <span className={`kyc-badge ${tone}`}>{r.status || '—'}</span>
                  </div>
                  <div className="kyc-meta">{r.user_phone}</div>
                  <div className="kyc-meta">
                    {r.ai_suggested_status ? <span>AI: <b>{r.ai_suggested_status}</b></span> : <span />}
                    <span className="kyc-dot" />
                    <span>{r.age ? `Age: ${r.age}` : 'Age: —'}</span>
                  </div>
                  <div className="kyc-meta">{r.location || 'Location: —'}</div>
                </button>
              );
            })}
          </div>
        </section>

        <section className="kyc-panel">
          <div className="kyc-panel-title">Review</div>
          {!selectedDetails ? (
            <div className="kyc-empty">Select a record to review.</div>
          ) : (
            <div className="kyc-details">
              <div className="kyc-details-grid">
                <div className="kyc-detail"><b>User:</b> {selectedDetails.full_name} ({selectedDetails.user_phone})</div>
                <div className="kyc-detail">
                  <b>Status:</b>{' '}
                  <span className={`kyc-badge ${statusTone(selectedDetails.status)}`}>{selectedDetails.status}</span>
                </div>
                {selectedDetails.age ? <div className="kyc-detail"><b>Age:</b> {selectedDetails.age}</div> : null}
                {selectedDetails.location ? <div className="kyc-detail"><b>Location:</b> {selectedDetails.location}</div> : null}
              </div>

              {actionError ? <div className="kyc-error">{actionError}</div> : null}

              {!canReview ? (
                <div className="kyc-hint">Approve/Reject is enabled only when status is pending.</div>
              ) : null}

              <div className="kyc-images">
                <div className="kyc-image-card">
                  <div className="kyc-image-title">ID Front</div>
                  {selectedDetails.doc_front_url ? (
                    <img alt="ID Front" src={normalizeUrl(selectedDetails.doc_front_url)} />
                  ) : (
                    <div className="kyc-image-empty">No file</div>
                  )}
                </div>
                <div className="kyc-image-card">
                  <div className="kyc-image-title">ID Back</div>
                  {selectedDetails.doc_back_url ? (
                    <img alt="ID Back" src={normalizeUrl(selectedDetails.doc_back_url)} />
                  ) : (
                    <div className="kyc-image-empty">No file</div>
                  )}
                </div>
                <div className="kyc-image-card wide">
                  <div className="kyc-image-title">Live Selfie</div>
                  {selectedDetails.selfie_url ? (
                    <img alt="Selfie" src={normalizeUrl(selectedDetails.selfie_url)} />
                  ) : (
                    <div className="kyc-image-empty">No file</div>
                  )}
                </div>
              </div>

              <div className="kyc-actions">
                <button className="btn btn-primary" disabled={!canReview || actionLoading} onClick={handleApprove}>
                  {actionLoading ? 'Working…' : 'Approve'}
                </button>
                <button className="btn btn-secondary" disabled={!canReview || actionLoading} onClick={handleReject}>
                  {actionLoading ? 'Working…' : 'Reject'}
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

export default KYC;
