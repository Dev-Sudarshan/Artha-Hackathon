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
                <div className="profile-header card overflow-hidden p-0 border-0 shadow-premium mb-12" style={{ borderRadius: 'var(--radius-xl)' }}>
                    <div className="h-48 bg-gradient-to-r from-primary to-primary-dark relative">
                        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '24px 24px' }}></div>
                    </div>
                    <div className="px-12 pb-12 relative">
                        <div className="flex justify-between items-end -translate-y-12">
                            <div className="flex items-end gap-8">
                                <div className="w-40 h-40 rounded-3xl border-8 border-white shadow-xl overflow-hidden bg-white">
                                    <img src={user.avatar} alt={user.name} className="w-full h-full object-cover" />
                                </div>
                                <div className="pb-4">
                                    <h1 className="text-4xl font-black text-slate-900 mb-2">{user.name}</h1>
                                    <div className="flex items-center gap-3">
                                        <div className={`badge ${user.kycStatus === 'verified' ? 'badge-success' : 'badge-warning'} flex items-center gap-2 py-2 px-4 shadow-sm`}>
                                            {user.kycStatus === 'verified' ? <BadgeCheck size={16} /> : <AlertCircle size={16} />}
                                            {user.kycStatus === 'verified' ? 'Verified Member' : `KYC ${user.kycStatus}`}
                                        </div>
                                        <span className="text-sm font-bold text-slate-400">ID: ART-2025-{user.id || '99'}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="pb-4 flex gap-4">
                                {user.kycStatus !== 'verified' ? (
                                    <Link to="/kyc" className="btn btn-primary px-8 py-4 shadow-lg shadow-blue-500/30">
                                        <BadgeCheck size={18} /> Verify Identity
                                    </Link>
                                ) : (
                                    <button className="btn btn-outline px-8 py-4 shadow-sm hover:border-primary transition-all">
                                        <User size={18} /> Edit Profile
                                    </button>
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
                            <div className="grid grid-2 gap-x-12 gap-y-10">
                                <div className="group transition-all">
                                    <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-2">Phone Primary</p>
                                    <div className="flex items-center gap-3">
                                        <Phone size={18} className="text-slate-300 group-hover:text-primary transition-colors" />
                                        <p className="text-lg font-bold text-slate-700">{user.phone}</p>
                                    </div>
                                </div>
                                <div className="group transition-all">
                                    <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-2">Official Email</p>
                                    <div className="flex items-center gap-3">
                                        <Mail size={18} className="text-slate-300 group-hover:text-primary transition-colors" />
                                        <p className="text-lg font-bold text-slate-700">{user.email || 'not_linked@artha.com'}</p>
                                    </div>
                                </div>
                                <div className="group transition-all">
                                    <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-2">Home Address</p>
                                    <div className="flex items-center gap-3">
                                        <MapPin size={18} className="text-slate-300 group-hover:text-primary transition-colors" />
                                        <p className="text-lg font-bold text-slate-700">Kathmandu, Nepal</p>
                                    </div>
                                </div>
                                <div className="group transition-all">
                                    <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-2">Nepal Citizenship ID</p>
                                    <div className="flex items-center gap-3">
                                        <BadgeCheck size={18} className="text-slate-300 group-hover:text-primary transition-colors" />
                                        <p className="text-lg font-bold text-slate-700">{user.citizenshipNo || 'Verified Online'}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Recent Activity Mini-Card */}

                    </div>

                    {/* Sidebar Stats */}
                    <div className="space-y-8">
                        <div className="card p-10 bg-slate-900 text-white shadow-premium border-0 overflow-hidden relative">
                            <div className="relative z-10">
                                <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest mb-6">Financial Level</p>
                                <div className="flex items-end gap-2 mb-8">
                                    <h2 className="text-5xl font-black text-white">Tier {user.kycStatus === 'verified' ? 'II' : 'I'}</h2>
                                </div>
                                <div className="space-y-4">
                                    <div className="flex justify-between text-xs">
                                        <span className="text-slate-500 font-bold uppercase">Borrowing Limit</span>
                                        <span className="font-black">Rs. {(user.bankDetailsAdded ? 100000 : 50000).toLocaleString()}</span>
                                    </div>
                                    <div className="h-1 bg-slate-800 rounded-full">
                                        <div className="h-full bg-primary w-2/3"></div>
                                    </div>
                                </div>
                            </div>
                            <div className="absolute -bottom-8 -right-8 opacity-10">
                                <BadgeCheck size={160} />
                            </div>
                        </div>

                        <div className="card p-8 border-slate-100 text-center">
                            <h4 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-4">Member Longevity</h4>
                            <p className="text-3xl font-black text-slate-800">12 Days</p>
                            <p className="text-xs font-medium text-muted mt-2">Joined: Dec 2025</p>
                        </div>

                        <div className="text-center px-4">
                            <p className="text-xs font-bold text-slate-400 italic leading-relaxed">
                                "Artha helps millions of Nepalese people find financial freedom through community support."
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
