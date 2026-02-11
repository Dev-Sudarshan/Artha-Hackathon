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

  const getAiVerificationStatus = (record) => {
    const aiStatus = record.ai_suggested_status?.toUpperCase();
    if (aiStatus === 'APPROVED') return { text: 'AI Verified', class: 'verified' };
    if (aiStatus === 'REJECTED') return { text: 'AI Not Verified', class: 'not-verified' };
    return { text: 'AI Processing', class: 'processing' };
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

  const renderVerificationItem = (label, value, isMatch = null) => {
    return (
      <div className="verification-item">
        <span className="verification-label">{label}:</span>
        <span className="verification-value">{value || '—'}</span>
        {isMatch !== null && (
          <span className={`verification-badge ${isMatch ? 'match' : 'no-match'}`}>
            {isMatch ? '✓ Match' : '✗ No Match'}
          </span>
        )}
      </div>
    );
  };

  if (loading) return <div className="loading">Loading KYC records...</div>;

  return (
    <div className="kyc-page">
      <div className="kyc-header">
        <h1>KYC Management</h1>
        <div className="kyc-subtitle">Total records: <b>{kycRecords.length}</b></div>
      </div>

      <div className={`kyc-grid ${selectedDetails ? 'with-details' : 'list-only'}`}>
        <section className="kyc-panel">
          <div className="kyc-panel-title">Applicants</div>
          <div className="kyc-list">
            {kycRecords.map((r) => {
              const active = selectedPhone === r.user_phone;
              const aiStatus = getAiVerificationStatus(r);
              return (
                <button
                  key={r.user_phone}
                  onClick={() => loadDetails(r.user_phone)}
                  className={`kyc-item-compact ${active ? 'active' : ''}`}
                >
                  <div className="kyc-item-name">{r.full_name || r.user_phone}</div>
                  <span className={`ai-verification-badge ${aiStatus.class}`}>{aiStatus.text}</span>
                </button>
              );
            })}
          </div>
        </section>

        {selectedDetails && (
          <section className="kyc-panel kyc-details-panel">
            <div className="kyc-details-new">
              {/* Header Section */}
              <div className="detail-header">
                <div>
                  <h2>{selectedDetails.full_name}</h2>
                  <p className="detail-phone">{selectedDetails.user_phone}</p>
                </div>
                <span className={`kyc-badge ${statusTone(selectedDetails.status)}`}>
                  {selectedDetails.status}
                </span>
              </div>

              {actionError ? <div className="kyc-error">{actionError}</div> : null}

              {/* User Entered Data Section */}
              <div className="detail-section">
                <h3 className="section-title">User Entered Data (KYC Form)</h3>
                <div className="verification-grid">
                  {selectedDetails.kyc?.basic_info && (
                    <>
                      <div className="verification-item">
                        <span className="verification-label">First Name:</span>
                        <span className="verification-value">{selectedDetails.kyc.basic_info.first_name || '—'}</span>
                      </div>
                      <div className="verification-item">
                        <span className="verification-label">Middle Name:</span>
                        <span className="verification-value">{selectedDetails.kyc.basic_info.middle_name || '—'}</span>
                      </div>
                      <div className="verification-item">
                        <span className="verification-label">Last Name:</span>
                        <span className="verification-value">{selectedDetails.kyc.basic_info.last_name || '—'}</span>
                      </div>
                      <div className="verification-item">
                        <span className="verification-label">Date of Birth:</span>
                        <span className="verification-value">{selectedDetails.kyc.basic_info.date_of_birth || '—'}</span>
                      </div>
                      <div className="verification-item">
                        <span className="verification-label">Citizenship No:</span>
                        <span className="verification-value">{selectedDetails.kyc.id_documents?.id_details?.id_number || '—'}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* OCR Extracted Data Section */}
              <div className="detail-section">
                <h3 className="section-title">OCR Extracted Data (from Citizenship Card)</h3>
                <div className="verification-grid">
                  {selectedDetails.kyc?.id_documents?.ocr_extracted ? (
                    <>
                      {renderVerificationItem('Citizenship Certificate No', selectedDetails.kyc.id_documents.ocr_extracted.citizenship_certificate_number, selectedDetails.kyc.final_result?.citizenship_no_match)}
                      {renderVerificationItem('Full Name', selectedDetails.kyc.id_documents.ocr_extracted.full_name, selectedDetails.kyc.final_result?.name_match)}
                      {renderVerificationItem('Sex', selectedDetails.kyc.id_documents.ocr_extracted.sex)}
                      {renderVerificationItem('Date of Birth', selectedDetails.kyc.id_documents.ocr_extracted.date_of_birth, selectedDetails.kyc.final_result?.dob_match)}
                      {selectedDetails.kyc.id_documents.ocr_extracted.birth_place && (
                        <div className="verification-item full-width">
                          <span className="verification-label">Birth Place:</span>
                          <span className="verification-value">
                            {selectedDetails.kyc.id_documents.ocr_extracted.birth_place.district}, {selectedDetails.kyc.id_documents.ocr_extracted.birth_place.municipality}, Ward {selectedDetails.kyc.id_documents.ocr_extracted.birth_place.ward}
                          </span>
                        </div>
                      )}
                      {selectedDetails.kyc.id_documents.ocr_extracted.permanent_address && (
                        <div className="verification-item full-width">
                          <span className="verification-label">Permanent Address:</span>
                          <span className="verification-value">
                            {selectedDetails.kyc.id_documents.ocr_extracted.permanent_address.district}, {selectedDetails.kyc.id_documents.ocr_extracted.permanent_address.municipality}, Ward {selectedDetails.kyc.id_documents.ocr_extracted.permanent_address.ward}
                          </span>
                        </div>
                      )}
                    </>
                  ) : (
                    <div className="verification-item full-width">
                      <span className="verification-value">No OCR data available</span>
                    </div>
                  )}
                </div>
              </div>

              {/* AI Verification Results */}
              <div className="detail-section">
                <h3 className="section-title">AI Verification Results</h3>
                <div className="verification-grid">
                  {selectedDetails.kyc?.final_result && (
                    <>
                      <div className="verification-item">
                        <span className="verification-label">Gov ID Verified:</span>
                        <span className={`verification-badge ${selectedDetails.kyc.final_result.gov_id_verified ? 'match' : 'no-match'}`}>
                          {selectedDetails.kyc.final_result.gov_id_verified ? '✓ Verified' : '✗ Failed'}
                        </span>
                      </div>
                      <div className="verification-item">
                        <span className="verification-label">Face Match:</span>
                        <span className={`verification-badge ${selectedDetails.kyc.final_result.face_match_score < 0.6 ? 'match' : 'no-match'}`}>
                          {selectedDetails.kyc.final_result.face_match_score < 0.6 ? `✓ Match (${(1 - selectedDetails.kyc.final_result.face_match_score).toFixed(2)})` : '✗ No Match'}
                        </span>
                      </div>
                      <div className="verification-item">
                        <span className="verification-label">AI Suggestion:</span>
                        <span className={`kyc-badge ${selectedDetails.kyc.final_result.ai_suggested_status === 'APPROVED' ? 'approved' : 'rejected'}`}>
                          {selectedDetails.kyc.final_result.ai_suggested_status}
                        </span>
                      </div>
                      {selectedDetails.kyc.final_result.reason && (
                        <div className="verification-item full-width">
                          <span className="verification-label">Reason:</span>
                          <span className="verification-value">{selectedDetails.kyc.final_result.reason}</span>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>

              {/* Document Images */}
              <div className="detail-section">
                <h3 className="section-title">Uploaded Documents</h3>
                <div className="kyc-images">
                  <div className="kyc-image-card">
                    <div className="kyc-image-title">Citizenship Front</div>
                    {selectedDetails.doc_front_url ? (
                      <img alt="ID Front" src={normalizeUrl(selectedDetails.doc_front_url)} />
                    ) : (
                      <div className="kyc-image-empty">No file</div>
                    )}
                  </div>
                  <div className="kyc-image-card">
                    <div className="kyc-image-title">Citizenship Back</div>
                    {selectedDetails.doc_back_url ? (
                      <img alt="ID Back" src={normalizeUrl(selectedDetails.doc_back_url)} />
                    ) : (
                      <div className="kyc-image-empty">No file</div>
                    )}
                  </div>
                  <div className="kyc-image-card">
                    <div className="kyc-image-title">Live Photo</div>
                    {selectedDetails.selfie_url ? (
                      <img alt="Selfie" src={normalizeUrl(selectedDetails.selfie_url)} />
                    ) : (
                      <div className="kyc-image-empty">No file</div>
                    )}
                  </div>
                </div>
              </div>

              {!canReview ? (
                <div className="kyc-hint">Approve/Reject is enabled only when status is pending.</div>
              ) : null}

              <div className="kyc-actions">
                <button className="btn btn-primary" disabled={!canReview || actionLoading} onClick={handleApprove}>
                  {actionLoading ? 'Working…' : 'Approve'}
                </button>
                <button className="btn btn-secondary" disabled={!canReview || actionLoading} onClick={handleReject}>
                  {actionLoading ? 'Working…' : 'Reject'}
                </button>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default KYC;
