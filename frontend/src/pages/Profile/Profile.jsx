import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import { User, MapPin, Phone, Mail, BadgeCheck, AlertCircle, TrendingUp, Wallet, ArrowUpRight, ArrowDownRight, Calendar, Award } from 'lucide-react';
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
            <div className="max-w-6xl mx-auto">
                {/* Premium Profile Header */}
                <div className="card overflow-hidden p-0 border-0 shadow-xl mb-6" style={{ borderRadius: '24px' }}>
                    <div className="h-40 bg-gradient-to-br from-blue-600 via-primary to-primary-dark relative">
                        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '32px 32px' }}></div>
                    </div>
                    <div className="px-8 pb-6 relative">
                        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4" style={{ marginTop: '-60px' }}>
                            <div className="flex items-end gap-5">
                                <div className="w-28 h-28 rounded-2xl border-4 border-white shadow-2xl overflow-hidden bg-white flex items-center justify-center">
                                    <span className="text-5xl font-black bg-gradient-to-br from-primary to-primary-dark bg-clip-text text-transparent">{user.firstName?.charAt(0)}{user.lastName?.charAt(0)}</span>
                                </div>
                                <div className="pb-1">
                                    <h1 className="text-3xl font-black text-slate-900 mb-2 tracking-tight">{user.firstName} {user.lastName}</h1>
                                    <div className="flex items-center gap-3">
                                        <div className={`badge ${user.kycStatus === 'verified' ? 'badge-success' : user.kycStatus === 'rejected' ? 'badge-error' : 'badge-warning'} flex items-center gap-1.5 py-1.5 px-4 text-sm font-bold`}>
                                            {user.kycStatus === 'verified' ? <BadgeCheck size={16} /> : <AlertCircle size={16} />}
                                            {user.kycStatus === 'verified'
                                                ? 'VERIFIED'
                                                : user.kycStatus === 'pending_admin_review' || user.kycStatus === 'processing'
                                                    ? 'PENDING'
                                                    : user.kycStatus === 'rejected'
                                                        ? 'REJECTED'
                                                        : 'INCOMPLETE'}
                                        </div>
                                        <span className="text-sm font-semibold text-slate-400">ID: ART-2025-{user.phone?.slice(-4) || '1111'}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex gap-3 sm:pb-1">
                                {user.kycStatus === 'verified' ? (
                                    <button className="btn btn-outline px-6 py-2.5 text-sm font-bold shadow-md hover:shadow-lg hover:border-primary transition-all">
                                        <User size={18} /> Edit Profile
                                    </button>
                                ) : user.kycStatus === 'pending_admin_review' || user.kycStatus === 'processing' ? (
                                    <button className="btn btn-outline px-6 py-2.5 text-sm font-bold shadow-md cursor-default opacity-60" disabled>
                                        <AlertCircle size={18} /> KYC Pending
                                    </button>
                                ) : user.kycStatus === 'rejected' ? (
                                    <Link to="/kyc" className="btn btn-error px-6 py-2.5 text-sm font-bold shadow-lg">
                                        <AlertCircle size={18} /> Retry KYC
                                    </Link>
                                ) : (
                                    <Link to="/kyc" className="btn btn-primary px-6 py-2.5 text-sm font-bold shadow-lg">
                                        <BadgeCheck size={18} /> Complete KYC
                                    </Link>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Stats Overview Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                    {/* Credit Score */}
                    <div className="card p-6 border-0 shadow-lg hover:shadow-xl transition-all bg-gradient-to-br from-green-50 to-emerald-50">
                        <div className="flex items-center justify-between mb-4">
                            <div className="p-3 rounded-2xl bg-white shadow-sm">
                                <Award size={28} className="text-green-600" />
                            </div>
                            <TrendingUp size={20} className="text-green-500" />
                        </div>
                        <p className="text-sm font-bold text-slate-500 mb-1 uppercase tracking-wide">Credit Score</p>
                        <h3 className="text-4xl font-black text-slate-900 mb-1">{user.creditScore || 'N/A'}</h3>
                        <p className="text-xs font-semibold text-green-600">
                            {(user.creditScore || 0) >= 750 ? 'Excellent' : (user.creditScore || 0) >= 600 ? 'Good' : 'Building'}
                        </p>
                    </div>

                    {/* Total Lended */}
                    <div className="card p-6 border-0 shadow-lg hover:shadow-xl transition-all bg-gradient-to-br from-blue-50 to-cyan-50">
                        <div className="flex items-center justify-between mb-4">
                            <div className="p-3 rounded-2xl bg-white shadow-sm">
                                <ArrowUpRight size={28} className="text-blue-600" />
                            </div>
                            <Wallet size={20} className="text-blue-500" />
                        </div>
                        <p className="text-sm font-bold text-slate-500 mb-1 uppercase tracking-wide">Total Lended</p>
                        <h3 className="text-4xl font-black text-slate-900 mb-1">Rs. {(user.totalLended || 0).toLocaleString()}</h3>
                        <p className="text-xs font-semibold text-blue-600">As Lender</p>
                    </div>

                    {/* Total Borrowed */}
                    <div className="card p-6 border-0 shadow-lg hover:shadow-xl transition-all bg-gradient-to-br from-purple-50 to-pink-50">
                        <div className="flex items-center justify-between mb-4">
                            <div className="p-3 rounded-2xl bg-white shadow-sm">
                                <ArrowDownRight size={28} className="text-purple-600" />
                            </div>
                            <Wallet size={20} className="text-purple-500" />
                        </div>
                        <p className="text-sm font-bold text-slate-500 mb-1 uppercase tracking-wide">Total Borrowed</p>
                        <h3 className="text-4xl font-black text-slate-900 mb-1">Rs. {(user.totalBorrowed || 0).toLocaleString()}</h3>
                        <p className="text-xs font-semibold text-purple-600">As Borrower</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Personal Information */}
                    <div className="lg:col-span-2 space-y-6">
                        <div className="card p-8 border-0 shadow-lg">
                            <div className="flex items-center gap-3 mb-6">
                                <div className="p-3 rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5">
                                    <User size={24} className="text-primary" />
                                </div>
                                <h3 className="text-2xl font-black text-slate-900">Personal Information</h3>
                            </div>
                            <div className="space-y-4">
                                <div className="flex items-center gap-5 p-5 rounded-2xl bg-slate-50 hover:bg-slate-100 transition-all group">
                                    <div className="p-3.5 rounded-xl bg-white shadow-sm group-hover:shadow-md transition-all">
                                        <Phone size={22} className="text-primary" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-1">Phone Number</p>
                                        <p className="text-lg font-bold text-slate-800">{user.phone}</p>
                                    </div>
                                </div>
                                
                                <div className="flex items-center gap-5 p-5 rounded-2xl bg-slate-50 hover:bg-slate-100 transition-all group">
                                    <div className="p-3.5 rounded-xl bg-white shadow-sm group-hover:shadow-md transition-all">
                                        <Mail size={22} className="text-primary" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-1">Email Address</p>
                                        <p className="text-lg font-bold text-slate-800">{user.email || 'not_linked@artha.com'}</p>
                                    </div>
                                </div>
                                
                                <div className="flex items-center gap-5 p-5 rounded-2xl bg-slate-50 hover:bg-slate-100 transition-all group">
                                    <div className="p-3.5 rounded-xl bg-white shadow-sm group-hover:shadow-md transition-all">
                                        <MapPin size={22} className="text-primary" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-1">Location</p>
                                        <p className="text-lg font-bold text-slate-800">Kathmandu, Nepal</p>
                                    </div>
                                </div>

                                <div className="flex items-center gap-5 p-5 rounded-2xl bg-slate-50 hover:bg-slate-100 transition-all group">
                                    <div className="p-3.5 rounded-xl bg-white shadow-sm group-hover:shadow-md transition-all">
                                        <Calendar size={22} className="text-primary" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-xs font-bold uppercase text-slate-400 tracking-wider mb-1">Member Since</p>
                                        <p className="text-lg font-bold text-slate-800">{user.createdAt ? new Date(user.createdAt).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : 'January 2025'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Financial Level Sidebar */}
                    <div className="space-y-6">
                        <div className="card p-8 bg-gradient-to-br from-slate-900 via-slate-800 to-primary-dark text-white shadow-2xl border-0 relative overflow-hidden">
                            <div className="absolute top-0 right-0 w-40 h-40 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2"></div>
                            <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2"></div>
                            
                            <div className="relative z-10">
                                <p className="text-slate-400 text-xs font-black uppercase tracking-widest mb-3">Financial Level</p>
                                <div className="flex items-baseline gap-3 mb-6">
                                    <h2 className="text-6xl font-black text-white">
                                        {(user.borrowingLimit || 50000) >= 100000 ? 'III' :
                                         (user.borrowingLimit || 50000) >= 50000 ? 'II' : 'I'}
                                    </h2>
                                    <span className="text-2xl font-bold text-slate-400">
                                        {(user.borrowingLimit || 50000) >= 100000 ? 'Elite' :
                                         (user.borrowingLimit || 50000) >= 50000 ? 'Premier' : 'Standard'}
                                    </span>
                                </div>
                                
                                <div className="space-y-4 mb-6">
                                    <div>
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="text-sm text-slate-300 font-bold">Borrowing Limit</span>
                                            <span className="text-xs text-slate-400 font-bold">{Math.min(((user.borrowingLimit || 50000) / 100000) * 100, 100).toFixed(0)}%</span>
                                        </div>
                                        <div className="h-3 bg-slate-700/50 rounded-full overflow-hidden">
                                            <div 
                                                className="h-full bg-gradient-to-r from-primary via-blue-400 to-cyan-400 shadow-lg transition-all duration-1000 ease-out"
                                                style={{ width: `${Math.min(((user.borrowingLimit || 50000) / 100000) * 100, 100)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                    <div className="pt-2">
                                        <span className="text-3xl font-black text-white">Rs. {(user.borrowingLimit || 50000).toLocaleString()}</span>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-white/10">
                                    <p className="text-xs text-slate-300 font-medium leading-relaxed">
                                        {user.kycStatus === 'verified' 
                                            ? 'Your borrowing limit is based on credit score and activity.'
                                            : 'Complete KYC verification to unlock higher limits.'
                                        }
                                    </p>
                                </div>
                            </div>
                        </div>

                        <div className="card p-6 border-2 border-primary/20 bg-gradient-to-br from-primary/5 to-transparent">
                            <div className="text-center">
                                <div className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 mb-4">
                                    <Award size={32} className="text-primary" />
                                </div>
                                <p className="text-sm font-bold text-slate-600 leading-relaxed italic">
                                    "Building financial freedom through community-powered lending."
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
