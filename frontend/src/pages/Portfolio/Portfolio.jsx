import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import loanService from '../../services/loanService';
import { PieChart, TrendingUp, Calendar, CheckCircle, ShieldCheck } from 'lucide-react';
import './Portfolio.css';

const Portfolio = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [portfolioData, setPortfolioData] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPortfolio = async () => {
            if (!user) return;
            try {
                const data = await loanService.getUserPortfolio();
                setPortfolioData(data); // { active_loan, investment_stats }
            } catch (error) {
                console.error("Failed to fetch portfolio", error);
            } finally {
                setLoading(false);
            }
        };
        fetchPortfolio();
    }, [user?.id]);

    if (!user) {
        return (
            <div className="container mt-12 mb-12 text-center animate-fade">
                <div className="card glass p-12" style={{ maxWidth: '500px', margin: '0 auto' }}>
                    <TrendingUp size={48} className="text-muted mb-4 mx-auto" />
                    <h2 className="mb-4">My Portfolio</h2>
                    <p className="text-muted mb-6">Join Artha to track your loans and investments in one secure place.</p>
                    <button onClick={() => navigate('/login')} className="btn btn-primary">Login to Continue</button>
                </div>
            </div>
        );
    }

    if (loading) {
        return <div className="container mt-12 text-center">Loading Portfolio...</div>;
    }

    // Role-based views: Determine dynamically from data
    let activeView = 'none';
    if (portfolioData?.active_loan) activeView = 'borrower';
    else if (portfolioData?.investment_stats?.total_invested > 0) activeView = 'lender';

    // Map Backend Data to UI
    const activeLoan = portfolioData?.active_loan ? {
        id: portfolioData.active_loan.loan_id,
        amount: portfolioData.active_loan.amount,
        tenure: portfolioData.active_loan.tenure_months,
        rate: portfolioData.active_loan.interest_rate,
        startDate: portfolioData.active_loan.start_timestamp || portfolioData.active_loan.created_at,
        emi: portfolioData.active_loan.emi,
        paidEmis: portfolioData.active_loan.paid_emis || 0,
        totalEmis: portfolioData.active_loan.tenure_months,
        purpose: portfolioData.active_loan.purpose,
        status: portfolioData.active_loan.status
    } : null;

    const investments = portfolioData?.investment_stats ? {
        totalInvested: portfolioData.investment_stats.total_invested,
        interestEarned: portfolioData.investment_stats.interest_earned,
        activeLoans: portfolioData.investment_stats.active_loans_count
    } : { totalInvested: 0, interestEarned: 0, activeLoans: 0 };

    const handlePayEmi = async (loanId, amount) => {
        setLoading(true);
        try {
            await loanService.repayLoan(loanId, amount);
            alert("EMI Payment Successful!");
            // Refresh data
            const newData = await loanService.getUserPortfolio();
            setPortfolioData(newData);
        } catch (error) {
            alert("Payment failed: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mt-8 mb-16 animate-fade">
            <div className="portfolio-header mb-12 flex justify-between items-end">
                <div>
                    <h1 className="text-4xl font-extrabold tracking-tight">Financial Portfolio</h1>
                    <p className="text-muted text-lg mt-2">
                        {activeView === 'none'
                            ? 'Begin your financial journey with Artha.'
                            : `A comprehensive overview of your ${activeView} activities and growth.`}
                    </p>
                </div>
                {activeView !== 'none' && (
                    <div className="flex gap-4">
                        <span className="badge badge-primary">Active {activeView}</span>
                        <div className="flex items-center gap-2 text-sm font-semibold text-primary">
                            <ShieldCheck size={16} /> Identity Verified
                        </div>
                    </div>
                )}
            </div>

            {activeView === 'none' && (
                <div className="card glass p-16 text-center animate-slide-up" style={{ borderRadius: 'var(--radius-xl)' }}>
                    <div className="mb-8 p-6 rounded-full bg-blue-50 inline-block">
                        <TrendingUp size={64} className="text-primary mx-auto" />
                    </div>
                    <h2 className="text-3xl font-bold mb-4">Choose Your Financial Path</h2>
                    <p className="text-muted max-w-xl mx-auto mb-12 text-lg leading-relaxed">
                        To maintain economic stability and community trust, Artha requires users to focus on one primary role.
                        Whether you want to <strong>Lend & Earn</strong> or <strong>Borrow & grow</strong>, your journey starts here.
                    </p>
                    <div className="flex gap-8 justify-center flex-wrap">
                        <div className="card p-10 hover-lift cursor-pointer rounded-2xl border-2 border-transparent hover:border-primary/20" style={{ width: '340px' }} onClick={() => navigate('/marketplace')}>
                            <div className="flex justify-between items-start mb-6">
                                <PieChart className="text-primary" size={40} />
                                <span className="text-xs font-black text-primary uppercase tracking-widest">Lender</span>
                            </div>
                            <h3 className="text-xl mb-3">Community Investor</h3>
                            <p className="text-muted mb-8 leading-normal">Earn a fixed 13% p.a. returns by funding local Nepali businesses and individuals.</p>
                            <button className="btn btn-primary w-100">Explore Marketplace</button>
                        </div>

                        <div className="card p-10 hover-lift cursor-pointer rounded-2xl border-2 border-transparent hover:border-success/20" style={{ width: '340px' }} onClick={() => navigate('/request-loan')}>
                            <div className="flex justify-between items-start mb-6">
                                <Calendar className="text-success" size={40} />
                                <span className="text-xs font-black text-success uppercase tracking-widest">Borrower</span>
                            </div>
                            <h3 className="text-xl mb-3">Capital Access</h3>
                            <p className="text-muted mb-8 leading-normal">Get up to NPR 100,000 for your business startup or personal needs with local support.</p>
                            <button className="btn btn-outline w-100">Apply for Loan</button>
                        </div>
                    </div>
                    <p className="mt-12 text-sm text-muted italic">"Artha brings the community together for financial prosperity."</p>
                </div>
            )}

            {activeView === 'borrower' && (
                <div className="borrower-dash animate-slide-up">
                    {/* Handle LISTED vs ACTIVE states */}
                    {activeLoan.status === 'PENDING_ADMIN_APPROVAL' || activeLoan.status === 'LISTED' || activeLoan.status === 'AWAITING_SIGNATURE' ? (
                        <div className="card glass p-16 text-center shadow-premium mb-12" style={{ borderRadius: 'var(--radius-xl)' }}>
                            <div className="w-24 h-24 rounded-full bg-blue-50 flex items-center justify-center mx-auto mb-8 animate-pulse">
                                <Calendar size={48} className="text-primary" />
                            </div>
                            <h2 className="text-3xl font-black text-slate-900 mb-4">
                                {activeLoan.status === 'PENDING_ADMIN_APPROVAL' ? 'Loan Request Pending Admin Approval' : 'Loan Application Listed'}
                            </h2>
                            <p className="text-muted text-lg max-w-xl mx-auto mb-10">
                                {activeLoan.status === 'PENDING_ADMIN_APPROVAL' ? (
                                    <>Your loan request for <strong>"{activeLoan.purpose}"</strong> has been submitted and is awaiting admin approval before it goes live on the Marketplace.</>
                                ) : (
                                    <>Your loan request used for <strong>"{activeLoan.purpose}"</strong> has been verified and is now live on the Marketplace.</>
                                )}
                                <br /><br />
                                <span className="font-bold text-primary">
                                    Status: {activeLoan.status === 'PENDING_ADMIN_APPROVAL' ? 'Pending Admin Approval' : 'Awaiting Lender Funding'}
                                </span>
                            </p>
                            <div className="inline-flex gap-8 p-6 bg-white rounded-2xl border border-slate-100 shadow-sm">
                                <div className="text-center px-4 border-r border-slate-100">
                                    <p className="text-xs font-black uppercase text-slate-400 tracking-widest mb-1">Amount</p>
                                    <p className="text-xl font-black text-slate-800">NPR {activeLoan.amount.toLocaleString()}</p>
                                </div>
                                <div className="text-center px-4">
                                    <p className="text-xs font-black uppercase text-slate-400 tracking-widest mb-1">Tenure</p>
                                    <p className="text-xl font-black text-slate-800">{activeLoan.tenure} Months</p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <>
                            <div className="grid grid-4 gap-6 mb-12">
                                <div className="card p-8 bg-slate-900 text-white border-0 shadow-premium">
                                    <p className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-2">Total Debt</p>
                                    <h2 className="text-3xl font-black mb-1">NPR {activeLoan.amount.toLocaleString()}</h2>
                                    <span className="text-xs text-slate-500 font-medium">Original Principal</span>
                                </div>
                                <div className="card p-8 bg-white overflow-hidden relative">
                                    <div className="absolute top-0 right-0 p-4 opacity-10"><Calendar size={48} /></div>
                                    <p className="text-muted text-sm font-bold uppercase tracking-wider mb-2">Monthly EMI</p>
                                    <h2 className="text-3xl font-black text-slate-800 mb-1">NPR {activeLoan.emi.toLocaleString()}</h2>
                                    <span className="text-xs text-primary font-bold">Due in 12 days</span>
                                </div>
                                <div className="card p-8 bg-white">
                                    <p className="text-muted text-sm font-bold uppercase tracking-wider mb-2">Paid Term</p>
                                    <h2 className="text-3xl font-black text-slate-800 mb-1">{activeLoan.paidEmis} / {activeLoan.totalEmis}</h2>
                                    <span className="text-xs text-muted font-bold">Installments</span>
                                </div>
                                <div className="card p-8 bg-white border-2 border-primary/10">
                                    <p className="text-muted text-sm font-bold uppercase tracking-wider mb-2">Remaining</p>
                                    <h2 className="text-3xl font-black text-primary mb-1">NPR {((activeLoan.totalEmis - activeLoan.paidEmis) * activeLoan.emi).toLocaleString()}</h2>
                                    <span className="text-xs text-success font-bold">+ Interest Coverage</span>
                                </div>
                            </div>

                            <div className="card mb-12 p-10 bg-slate-50 border-slate-100 overflow-hidden relative">
                                <div className="flex justify-between items-center relative z-10">
                                    <div>
                                        <h3 className="text-2xl font-bold mb-2">Active Loan: "{activeLoan.purpose || 'Agricultural Stock'}"</h3>
                                        <p className="text-muted font-medium">Started on {new Date(activeLoan.startDate).toLocaleDateString('en-NP', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
                                    </div>
                                    <div className="flex flex-col items-end">
                                        <span className="badge badge-success mb-2">Repayment Phase</span>
                                        <p className="text-xs font-black text-slate-400">Fixed rate: 13%</p>
                                    </div>
                                </div>
                                <div className="mt-10 h-3 bg-slate-200 rounded-full overflow-hidden">
                                    <div className="h-full bg-primary transition-all duration-1000" style={{ width: `${(activeLoan.paidEmis / activeLoan.totalEmis) * 100}%` }}></div>
                                </div>
                                <div className="flex justify-between mt-3 text-xs font-black text-slate-400 uppercase tracking-widest">
                                    <span>0% Progress</span>
                                    <span>{Math.round((activeLoan.paidEmis / activeLoan.totalEmis) * 100)}% Repaid</span>
                                    <span>100% Fully Paid</span>
                                </div>
                            </div>

                            <div className="section-header flex justify-between items-end mb-8">
                                <div>
                                    <h3 className="text-2xl font-bold">Repayment Schedule</h3>
                                    <p className="text-muted mt-1">Automated installments and payment triggers.</p>
                                </div>
                                <p className="font-bold text-primary text-sm bg-blue-50 px-4 py-2 rounded-full">
                                    {activeLoan.totalEmis - activeLoan.paidEmis} Installments Outstanding
                                </p>
                            </div>

                            <div className="card p-4 overflow-hidden shadow-premium" style={{ border: 'none' }}>
                                <div className="emi-list" style={{ display: 'grid', gap: '0.75rem' }}>
                                    {[...Array(activeLoan.totalEmis)].map((_, i) => {
                                        const isPaid = i < activeLoan.paidEmis;
                                        const isNext = i === activeLoan.paidEmis;
                                        return (
                                            <div key={i} className={`emi-item flex items-center justify-between p-6 rounded-2xl transition-all ${isPaid ? 'bg-slate-50 opacity-60' : isNext ? 'bg-white border-2 border-primary shadow-lg ring-4 ring-primary/5' : 'bg-white border border-slate-100'}`}>
                                                <div className="flex items-center gap-6">
                                                    <div className={`w-12 h-12 rounded-full flex items-center justify-center font-black ${isPaid ? 'bg-success/10 text-success' : isNext ? 'bg-primary text-white' : 'bg-slate-100 text-slate-400'}`}>
                                                        {i + 1}
                                                    </div>
                                                    <div>
                                                        <div className="font-bold text-slate-800">Month {i + 1} Installment</div>
                                                        <div className="text-xs font-semibold text-muted flex items-center gap-1 mt-1">
                                                            <Calendar size={12} /> Due: {new Date(2024, i + 1, 1).toLocaleDateString('en-NP', { month: 'long', day: 'numeric', year: 'numeric' })}
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-8">
                                                    <div className="text-right">
                                                        <div className={`text-lg font-black ${isPaid ? 'text-slate-500' : 'text-slate-800'}`}>NPR {activeLoan.emi.toLocaleString()}</div>
                                                        <div className="text-[10px] font-black uppercase text-muted tracking-tighter">EMI Total (Principal + Int.)</div>
                                                    </div>
                                                    {isPaid ? (
                                                        <span className="flex items-center gap-2 px-4 py-2 bg-success/10 text-success rounded-full text-xs font-black uppercase tracking-wider">
                                                            <CheckCircle size={14} /> Received
                                                        </span>
                                                    ) : (
                                                        <button
                                                            onClick={() => handlePayEmi(activeLoan.id, activeLoan.emi)}
                                                            className={`btn ${isNext ? 'btn-primary' : 'btn-outline'} px-6 py-3 font-bold text-sm shadow-sm`}
                                                        >
                                                            {isNext ? 'Pay installment' : 'Pay Early'}
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}

            {activeView === 'lender' && (
                <div className="lender-dash animate-slide-up">
                    <div className="grid grid-3 gap-8 mb-12">
                        <div className="card p-10 bg-slate-900 text-white shadow-premium border-0 relative overflow-hidden underline-none">
                            <PieChart className="absolute top-0 right-0 p-4 opacity-10" size={64} />
                            <p className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-4">Total Portfolio Value</p>
                            <h2 className="text-4xl font-extrabold mb-2 text-white">NPR {investments.totalInvested.toLocaleString()}</h2>
                            <div className="flex items-center gap-2 text-primary-light text-sm font-bold mt-4">
                                <TrendingUp size={16} /> Diversified across {investments.activeLoans} loans
                            </div>
                        </div>
                        <div className="card p-10 bg-white shadow-lg border-slate-100 flex flex-col justify-between">
                            <div>
                                <p className="text-muted text-sm font-bold uppercase tracking-wider mb-4">Net Returns Earned</p>
                                <h2 className="text-4xl font-extrabold text-success mb-2">+ NPR {investments.interestEarned.toLocaleString()}</h2>
                            </div>
                            <div className="p-3 rounded-xl bg-success/5 border border-success/10 text-success text-xs font-bold w-fit">
                                Estimated 13% Unrealized Yield
                            </div>
                        </div>
                        <div className="card p-10 bg-white shadow-lg border-slate-100 flex flex-col justify-between text-right items-end">
                            <div className="w-16 h-16 rounded-full bg-warning/10 flex items-center justify-center text-warning mb-6">
                                <ShieldCheck size={32} />
                            </div>
                            <div>
                                <h2 className="text-4xl font-extrabold text-slate-800 mb-1">{investments.activeLoans}</h2>
                                <p className="text-muted text-sm font-bold uppercase tracking-wider">Verified Asset Groups</p>
                            </div>
                        </div>
                    </div>

                    <div className="card text-center p-20 glass shadow-premium" style={{ borderRadius: 'var(--radius-xl)' }}>
                        <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-8">
                            <TrendingUp size={40} className="text-primary" />
                        </div>
                        <h2 className="text-3xl font-bold mb-4">Your investments are performing well</h2>
                        <p className="text-muted text-lg max-w-2xl mx-auto mb-10 leading-relaxed">
                            Every investment you make powers a local vision. Your capital is currently funding agriculture, small businesses, and education across Nepal.
                        </p>
                        <div className="flex gap-4 justify-center">
                            <button onClick={() => navigate('/marketplace')} className="btn btn-primary px-10 py-4 shadow-xl shadow-blue-500/30">Grow Your Portfolio</button>
                            <button className="btn btn-outline px-10 py-4 shadow-sm">View Analytics</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Portfolio;
