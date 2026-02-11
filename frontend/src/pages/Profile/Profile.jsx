import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import { User, MapPin, Phone, Mail, BadgeCheck, AlertCircle } from 'lucide-react';
import './Profile.css';

const Profile = () => {
    const { user } = useAuth();

    if (!user) {
        return (
            <div className="container mt-12 mb-12 text-center animate-fade">
                <div className="card glass p-12" style={{ maxWidth: '500px', margin: '0 auto' }}>
                    <User size={48} className="text-muted mb-4 mx-auto" />
                    <h2>Loading Profile...</h2>
                    <p className="text-muted">Fetching your secure data.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="container mt-12 mb-20 animate-fade">
            <div className="max-w-5xl mx-auto">
                {/* Premium Profile Header */}
                <div className="profile-header card overflow-hidden p-0 border-0 shadow-lg mb-8" style={{ borderRadius: '24px' }}>
                    <div className="h-32 bg-gradient-to-r from-primary to-primary-dark relative">
                        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '24px 24px' }}></div>
                    </div>
                    <div className="px-8 pb-8 relative">
                        <div className="flex justify-between items-end -translate-y-10">
                            <div className="flex items-end gap-6">
                                <div className="w-24 h-24 rounded-2xl border-4 border-white shadow-lg overflow-hidden bg-white">
                                    <img src={user.avatar} alt={user.name} className="w-full h-full object-cover" />
                                </div>
                                <div className="pb-2">
                                    <h1 className="text-2xl font-black text-slate-900 mb-1">{user.name}</h1>
                                    <div className="flex items-center gap-2">
                                        <div className={`badge ${user.kycStatus === 'verified' ? 'badge-success' : user.kycStatus === 'rejected' ? 'badge-error' : 'badge-warning'} flex items-center gap-1 py-1 px-3 text-xs`}>
                                            {user.kycStatus === 'verified' ? <BadgeCheck size={14} /> : <AlertCircle size={14} />}
                                            {user.kycStatus === 'verified'
                                                ? 'Verified'
                                                : user.kycStatus === 'pending_admin_review' || user.kycStatus === 'processing'
                                                    ? 'Pending'
                                                    : user.kycStatus === 'rejected'
                                                        ? 'Rejected'
                                                        : 'Incomplete'}
                                        </div>
                                        <span className="text-xs font-medium text-slate-400">ID: ART-2025-{user.phone?.slice(-4) || '9811'}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="pb-2 flex gap-3">
                                {user.kycStatus === 'verified' ? (
                                    <button className="btn btn-outline px-6 py-2 text-sm shadow-sm hover:border-primary transition-all">
                                        <User size={16} /> Edit Profile
                                    </button>
                                ) : user.kycStatus === 'pending_admin_review' || user.kycStatus === 'processing' ? (
                                    <button className="btn btn-outline px-6 py-2 text-sm shadow-sm cursor-default" disabled>
                                        <AlertCircle size={16} /> KYC Pending
                                    </button>
                                ) : user.kycStatus === 'rejected' ? (
                                    <Link to="/kyc" className="btn btn-primary px-6 py-2 text-sm shadow-lg shadow-red-500/30">
                                        <AlertCircle size={16} /> Retry KYC
                                    </Link>
                                ) : (
                                    <Link to="/kyc" className="btn btn-primary px-6 py-2 text-sm shadow-lg shadow-blue-500/30">
                                        <BadgeCheck size={16} /> Verify Identity
                                    </Link>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-3 gap-8">
                    {/* Primary Info */}
                    <div className="col-span-2 space-y-8">
                        <div className="card p-10 border-slate-100 shadow-lg">
                            <h3 className="text-xl font-black text-slate-900 mb-8 flex items-center gap-4">
                                <div className="p-3 rounded-xl bg-slate-50 text-primary"><User size={24} /></div>
                                Personal Information
                            </h3>
                            <div className="space-y-8">
                                <div className="flex items-center gap-6 p-6 rounded-2xl bg-slate-50 hover:bg-slate-100 transition-all">
                                    <div className="p-4 rounded-xl bg-white shadow-sm">
                                        <Phone size={24} className="text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-xs font-bold uppercase text-slate-400 tracking-wide mb-1">Phone Number</p>
                                        <p className="text-xl font-bold text-slate-800">{user.phone}</p>
                                    </div>
                                </div>
                                
                                <div className="flex items-center gap-6 p-6 rounded-2xl bg-slate-50 hover:bg-slate-100 transition-all">
                                    <div className="p-4 rounded-xl bg-white shadow-sm">
                                        <Mail size={24} className="text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-xs font-bold uppercase text-slate-400 tracking-wide mb-1">Email Address</p>
                                        <p className="text-xl font-bold text-slate-800">{user.email || 'not_linked@artha.com'}</p>
                                    </div>
                                </div>
                                
                                <div className="flex items-center gap-6 p-6 rounded-2xl bg-slate-50 hover:bg-slate-100 transition-all">
                                    <div className="p-4 rounded-xl bg-white shadow-sm">
                                        <MapPin size={24} className="text-primary" />
                                    </div>
                                    <div>
                                        <p className="text-xs font-bold uppercase text-slate-400 tracking-wide mb-1">Location</p>
                                        <p className="text-xl font-bold text-slate-800">Kathmandu, Nepal</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Sidebar Stats */}
                    <div className="space-y-8">
                        <div className="card p-10 bg-gradient-to-br from-slate-900 to-slate-800 text-white shadow-premium border-0">
                            <p className="text-slate-400 text-xs font-black uppercase tracking-widest mb-6">Financial Level</p>
                            <h2 className="text-6xl font-black text-white mb-8">
                                Tier {
                                    (user.borrowingLimit || 50000) >= 100000 ? 'III' :
                                    (user.borrowingLimit || 50000) >= 50000 ? 'II' : 'I'
                                }
                            </h2>
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-slate-400 font-bold">Borrowing Limit</span>
                                    <span className="text-2xl font-black text-white">Rs. {(user.borrowingLimit || 50000).toLocaleString()}</span>
                                </div>
                                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                                    <div 
                                        className="h-full bg-gradient-to-r from-primary to-blue-400 shadow-lg shadow-primary/30 transition-all duration-500"
                                        style={{ width: `${Math.min(((user.borrowingLimit || 50000) / 100000) * 100, 100)}%` }}
                                    ></div>
                                </div>
                            </div>
                        </div>

                        <div className="text-center px-6 py-8">
                            <p className="text-sm font-medium text-slate-500 italic leading-relaxed">
                                "Building financial freedom through community-powered lending."
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
