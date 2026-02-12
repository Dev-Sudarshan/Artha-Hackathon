import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import { User, Phone, Mail, MapPin, BadgeCheck, AlertCircle, Calendar, Shield } from 'lucide-react';
import './Profile.css';

const Profile = () => {
    const { user } = useAuth();

    if (!user) {
        return (
            <div className="profile-loading">
                <User size={40} />
                <h2>Loading Profile...</h2>
            </div>
        );
    }

    const kycLabel = user.kycStatus === 'verified' ? 'Verified'
        : user.kycStatus === 'pending_admin_review' || user.kycStatus === 'processing' ? 'Pending'
        : user.kycStatus === 'rejected' ? 'Rejected'
        : 'Incomplete';

    const kycClass = user.kycStatus === 'verified' ? 'success'
        : user.kycStatus === 'rejected' ? 'error'
        : 'warning';

    return (
        <div className="profile-page">
            {/* Header card */}
            <div className="profile-card profile-header-card">
                <div className="profile-avatar-wrap">
                    <div className="profile-initials">
                        {user.firstName?.charAt(0)}{user.lastName?.charAt(0)}
                    </div>
                </div>
                <div className="profile-identity">
                    <h1>{user.firstName} {user.lastName}</h1>
                    <span className={`kyc-badge kyc-${kycClass}`}>
                        {user.kycStatus === 'verified' ? <BadgeCheck size={14} /> : <AlertCircle size={14} />}
                        {kycLabel}
                    </span>
                </div>
                <div className="profile-header-action">
                    {user.kycStatus === 'verified' ? (
                        <button className="btn-profile-outline" disabled>
                            <User size={16} /> Profile Complete
                        </button>
                    ) : user.kycStatus === 'pending_admin_review' || user.kycStatus === 'processing' ? (
                        <button className="btn-profile-outline" disabled>
                            <AlertCircle size={16} /> Under Review
                        </button>
                    ) : (
                        <Link to="/kyc" className="btn-profile-primary">
                            <Shield size={16} /> {user.kycStatus === 'rejected' ? 'Retry KYC' : 'Complete KYC'}
                        </Link>
                    )}
                </div>
            </div>

            {/* Stats row */}
            <div className="profile-stats">
                <div className="stat-item">
                    <span className="stat-label">Credit Score</span>
                    <span className="stat-value">{user.creditScore || '—'}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Total Lent</span>
                    <span className="stat-value">Rs. {(user.totalLended || 0).toLocaleString()}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Total Borrowed</span>
                    <span className="stat-value">Rs. {(user.totalBorrowed || 0).toLocaleString()}</span>
                </div>
                <div className="stat-item">
                    <span className="stat-label">Borrowing Limit</span>
                    <span className="stat-value">Rs. {(user.borrowingLimit || 50000).toLocaleString()}</span>
                </div>
            </div>

            {/* Info section */}
            <div className="profile-card">
                <h2 className="section-title">Personal Information</h2>
                <div className="info-grid">
                    <div className="info-row">
                        <Phone size={18} className="info-icon" />
                        <div>
                            <span className="info-label">Phone</span>
                            <span className="info-value">{user.phone}</span>
                        </div>
                    </div>
                    <div className="info-row">
                        <Mail size={18} className="info-icon" />
                        <div>
                            <span className="info-label">Email</span>
                            <span className="info-value">{user.email || 'Not linked'}</span>
                        </div>
                    </div>
                    <div className="info-row">
                        <MapPin size={18} className="info-icon" />
                        <div>
                            <span className="info-label">Location</span>
                            <span className="info-value">Kathmandu, Nepal</span>
                        </div>
                    </div>
                    <div className="info-row">
                        <Calendar size={18} className="info-icon" />
                        <div>
                            <span className="info-label">Member Since</span>
                            <span className="info-value">
                                {user.createdAt
                                    ? new Date(user.createdAt).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
                                    : 'January 2025'}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
