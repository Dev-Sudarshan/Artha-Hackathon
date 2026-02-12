import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import loanService from '../../services/loanService';
import { ArrowRight, Calculator, Upload, Video, AlertTriangle, ShieldCheck } from 'lucide-react';
import '../../styles/Auth.css';
import './LoanRequest.css';

// Backend URL for serving PDFs
const BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const LoanRequest = () => {
    const { user, setUserRole } = useAuth();
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [agreementPdf, setAgreementPdf] = useState(null);
    const [loanId, setLoanId] = useState(null);

    // Limits
    const BORROW_LIMIT_NO_BANK = 50000;
    const BORROW_LIMIT_WITH_BANK = 100000;
    const maxAmount = user?.bankDetailsAdded ? BORROW_LIMIT_WITH_BANK : BORROW_LIMIT_NO_BANK;

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }
        // Rule 1: Role Exclusivity
        if (user.activeRole === 'lender') {
            alert("You have an active lending status. You cannot borrow until all your investments are closed.");
            navigate('/portfolio');
        }
    }, [user, navigate]);

    const [formData, setFormData] = useState({
        amount: '',
        tenure: 12,
        purpose: '',
        guarantorName: '',
        guarantorPhone: '',
        guarantorRelation: '',
        guarantorCard: '',
        guarantorFront: null,
        guarantorBack: null,
        videoStatement: null,
        agreeRules: false
    });

    // ... same EMI logic ...
    const [emi, setEmi] = useState(0);
    const [proceeds, setProceeds] = useState(0);
    const INTEREST = 13;
    const FEES_PERCENT = 3;

    useEffect(() => {
        const principal = parseFloat(formData.amount) || 0;
        const months = parseFloat(formData.tenure) || 12;

        const r = INTEREST / 12 / 100;

        if (principal > 0) {
            const emiCalc = principal * r * Math.pow(1 + r, months) / (Math.pow(1 + r, months) - 1);
            setEmi(Math.round(emiCalc));

            const fees = principal * (FEES_PERCENT / 100);
            setProceeds(principal - fees);
        } else {
            setEmi(0);
            setProceeds(0);
        }
    }, [formData.amount, formData.tenure]);

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleFile = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.files[0] });
    };

    const handleNext = async (e) => {
        e.preventDefault();
        if (parseFloat(formData.amount) > maxAmount) {
            alert(`Your current borrowing limit is NPR ${maxAmount.toLocaleString()}. ${!user.bankDetailsAdded ? 'Add bank details to increase limit to 1 Lakh.' : ''}`);
            return;
        }

        setLoading(true);
        try {
            const loanData = {
                amount: parseInt(formData.amount),
                tenure: parseInt(formData.tenure),
                purpose: formData.purpose,
                agreed_to_rules: true // Pass this as default for step 1
            };
            const guarantorData = {
                name: formData.guarantorName,
                phone: formData.guarantorPhone,
                relation: formData.guarantorRelation,
                citizenshipNo: formData.guarantorCard
            };
            const guarantorFiles = {
                front: formData.guarantorFront,
                back: formData.guarantorBack
            };

            const result = await loanService.createBorrowRequest(null, loanData, guarantorData, guarantorFiles, {});
            setUserRole('borrower');
            setLoanId(result.loan_id);
            setAgreementPdf(result.agreement_pdf);
            setStep(2);
        } catch (error) {
            alert("Failed to create loan draft: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!formData.signedDoc || !formData.videoStatement) {
            alert("Please upload both the signed document and video statement");
            return;
        }

        setLoading(true);
        try {
            const loanData = {
                amount: formData.amount,
                tenure: formData.tenure,
                purpose: formData.purpose
            };
            const guarantorData = {
                name: formData.guarantorName,
                phone: formData.guarantorPhone,
                relation: formData.guarantorRelation,
                citizenshipNo: formData.guarantorCard
            };
            const guarantorFiles = {
                front: formData.guarantorFront,
                back: formData.guarantorBack
            };
            const legalFiles = {
                signedDoc: formData.signedDoc,
                videoStatement: formData.videoStatement
            };

            await loanService.createBorrowRequest(loanId, loanData, guarantorData, guarantorFiles, legalFiles);

            navigate('/', { state: { loanSubmitted: true } });
        } catch (error) {
            alert("Verification failed: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mt-8 mb-16 animate-fade">
            <div className="max-w-4xl mx-auto">
                {/* Step Indicator */}
                <div className="card p-12 shadow-premium border-slate-100" style={{ borderRadius: 'var(--radius-xl)' }}>
                    {/* Step Indicator - Moved Inside Card */}
                    <div className="flex justify-between items-center mb-12 relative px-4">
                        <div className="absolute top-1/2 left-0 w-full h-1 bg-slate-100 -z-10 translate-y-[-50%] rounded-full"></div>
                        <div className="absolute top-1/2 left-0 h-1 bg-primary -z-10 translate-y-[-50%] transition-all duration-500 rounded-full" style={{ width: step === 1 ? '50%' : '100%' }}></div>

                        {[1, 2].map((s) => (
                            <div key={s} className="flex flex-col items-center bg-white px-2">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-black transition-all duration-300 ${step >= s ? 'bg-primary text-white shadow-lg ring-4 ring-primary/10' : 'bg-white text-slate-300 border-2 border-slate-200'}`}>
                                    {s}
                                </div>
                                <span className={`text-[10px] font-bold uppercase mt-2 tracking-widest ${step >= s ? 'text-primary' : 'text-slate-300'}`}>
                                    {s === 1 ? 'Details' : 'Legal'}
                                </span>
                            </div>
                        ))}
                    </div>

                    <div className="text-center mb-10">
                        <h1 className="text-3xl font-black text-slate-900 mb-2">Apply for a Community Loan</h1>
                        <p className="text-muted text-lg">Your request will be visible to verified local lenders.</p>
                    </div>

                    {step === 1 ? (
                        <form onSubmit={handleNext} className="animate-fade">
                            <div className="grid grid-2 gap-8 mb-10">
                                <div className="form-group">
                                    <label className="text-sm font-black text-slate-700 uppercase tracking-wider mb-3 block">Requested Amount (NPR)</label>
                                    <input
                                        type="number"
                                        name="amount"
                                        value={formData.amount}
                                        onChange={handleChange}
                                        className="w-full px-6 py-4 rounded-2xl border-2 border-slate-100 focus:border-primary focus:outline-none text-lg font-bold transition-all"
                                        placeholder="e.g. 50000"
                                        required
                                        min="1000"
                                    />
                                    <div className="flex justify-between mt-2">
                                        <p className="text-xs font-bold text-primary">Target: 13% Fixed Interest Rate</p>
                                        <p className="text-xs font-bold text-slate-400">Max: Rs. {maxAmount.toLocaleString()}</p>
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label className="text-sm font-black text-slate-700 uppercase tracking-wider mb-3 block">Tenure Period</label>
                                    <div className="input-wrapper">
                                        <select
                                            name="tenure"
                                            value={formData.tenure}
                                            onChange={handleChange}
                                            className="w-full px-6 py-4 rounded-2xl border-2 border-slate-100 focus:border-primary focus:outline-none text-lg font-bold transition-all bg-white cursor-pointer appearance-none"
                                        >
                                            {[6, 12, 18, 24].map(m => <option key={m} value={m}>{m} Months</option>)}
                                        </select>
                                    </div>
                                </div>
                            </div>

                            <div className="emi-calculator-box mb-10 p-8 rounded-3xl bg-blue-50/50 border border-blue-100 relative overflow-hidden">
                                <div className="absolute top-0 right-0 p-4 opacity-5"><Calculator size={64} /></div>
                                <h4 className="flex items-center gap-3 text-primary font-black uppercase tracking-widest text-sm mb-8">
                                    <div className="w-8 h-8 rounded-lg bg-primary text-white flex items-center justify-center"><Calculator size={16} /></div>
                                    Repayment Estimator
                                </h4>
                                <div className="grid grid-3 gap-8 text-center bg-white p-8 rounded-2xl shadow-sm border border-blue-50">
                                    <div>
                                        <p className="text-xs font-black text-slate-400 uppercase tracking-tighter mb-2">Monthly Installment</p>
                                        <h2 className="text-3xl font-black text-primary">NPR {emi.toLocaleString()}</h2>
                                    </div>
                                    <div className="border-x border-slate-50">
                                        <p className="text-xs font-black text-slate-400 uppercase tracking-tighter mb-2">Nepal Fixed Rate</p>
                                        <h2 className="text-3xl font-black text-slate-800">13%</h2>
                                    </div>
                                    <div>
                                        <p className="text-xs font-black text-slate-400 uppercase tracking-tighter mb-2">You Receive (97%)</p>
                                        <h2 className="text-3xl font-black text-success">NPR {proceeds.toLocaleString()}</h2>
                                    </div>
                                </div>
                                <div className="mt-6 flex justify-center gap-6 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                    <span>3% Platform Fee</span>
                                    <span>•</span>
                                    <span>1% Insurance Coverage</span>
                                </div>
                            </div>

                            <div className="form-group mb-12">
                                <label className="text-sm font-black text-slate-700 uppercase tracking-wider mb-3 block">Purpose of Loan</label>
                                <textarea
                                    name="purpose"
                                    value={formData.purpose}
                                    onChange={handleChange}
                                    rows="3"
                                    required
                                    className="w-full px-6 py-4 rounded-2xl border-2 border-slate-100 focus:border-primary focus:outline-none text-lg font-medium transition-all"
                                    placeholder="Briefly explain how this loan will help your business or personal growth..."
                                ></textarea>
                            </div>

                            <div className="form-section-header mb-8 flex items-center gap-4">
                                <h4 className="text-lg font-black text-slate-900">Guarantor Verification</h4>
                                <div className="h-px flex-1 bg-slate-100"></div>
                            </div>

                            <div className="grid grid-2 gap-8 mb-10">
                                <div className="form-group">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-wider mb-2 block">Guarantor Name</label>
                                    <input
                                        type="text"
                                        name="guarantorName"
                                        value={formData.guarantorName}
                                        onChange={handleChange}
                                        required
                                        className="w-full px-6 py-4 rounded-2xl border-2 border-slate-100 focus:border-primary focus:outline-none font-bold transition-all"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-wider mb-2 block">Guarantor Phone</label>
                                    <input
                                        type="tel"
                                        name="guarantorPhone"
                                        value={formData.guarantorPhone}
                                        onChange={handleChange}
                                        required
                                        className="w-full px-6 py-4 rounded-2xl border-2 border-slate-100 focus:border-primary focus:outline-none font-bold transition-all"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-wider mb-2 block">Relationship</label>
                                    <input
                                        type="text"
                                        name="guarantorRelation"
                                        value={formData.guarantorRelation}
                                        onChange={handleChange}
                                        required
                                        className="w-full px-6 py-4 rounded-2xl border-2 border-slate-100 focus:border-primary focus:outline-none font-bold transition-all"
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="text-xs font-black text-slate-400 uppercase tracking-wider mb-2 block">Guarantor Citizenship No</label>
                                    <input
                                        type="text"
                                        name="guarantorCard"
                                        value={formData.guarantorCard}
                                        onChange={handleChange}
                                        required
                                        className="w-full px-6 py-4 rounded-2xl border-2 border-slate-100 focus:border-primary focus:outline-none font-bold transition-all"
                                    />
                                </div>
                                <div className="grid grid-2 gap-4">
                                    <div className="relative">
                                        <label className="upload-tile upload-tile-sm flex flex-col items-center justify-center p-4 rounded-2xl transition-all cursor-pointer h-full">
                                            <Upload size={20} className="text-slate-400 mb-2" />
                                            <span className="text-[10px] font-black uppercase text-slate-500">Front Copy</span>
                                            <input type="file" name="guarantorFront" onChange={handleFile} accept="image/*" className="hidden" />
                                            {formData.guarantorFront && <ShieldCheck className="text-success mt-2" size={16} />}
                                        </label>
                                    </div>
                                    <div className="relative">
                                        <label className="upload-tile upload-tile-sm flex flex-col items-center justify-center p-4 rounded-2xl transition-all cursor-pointer h-full">
                                            <Upload size={20} className="text-slate-400 mb-2" />
                                            <span className="text-[10px] font-black uppercase text-slate-500">Back Copy</span>
                                            <input type="file" name="guarantorBack" onChange={handleFile} accept="image/*" className="hidden" />
                                            {formData.guarantorBack && <ShieldCheck className="text-success mt-2" size={16} />}
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <button type="submit" className="btn btn-primary w-100 py-5 text-lg shadow-xl shadow-blue-500/20" disabled={loading}>
                                {loading ? 'Processing...' : <><span>Continue to Verification</span> <ArrowRight size={20} /></>}
                            </button>
                        </form>
                    ) : (
                        <form onSubmit={handleSubmit} className="animate-fade">
                            {/* Info Alert - Draft Status */}
                            <div className="alert p-6 rounded-2xl bg-blue-50 border-2 border-blue-200 mb-8">
                                <div className="flex items-start gap-3">
                                    <div className="w-8 h-8 rounded-lg bg-blue-200 text-blue-800 flex items-center justify-center flex-shrink-0 mt-1">
                                        <AlertTriangle size={18} />
                                    </div>
                                    <div>
                                        <h4 className="font-black text-blue-900 mb-1">Complete This Step to Submit Your Loan</h4>
                                        <p className="text-sm text-blue-700 leading-relaxed">
                                            Your loan details have been saved as a <strong>DRAFT</strong>. To submit for admin approval and make it visible in the marketplace, you must upload both the signed agreement and video verification below.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            {/* ... (Alerts section same as before) ... */}
                            <div className="alert p-8 rounded-3xl bg-amber-50 border border-amber-100 mb-10">
                                <div className="flex items-center gap-3 text-amber-700 font-black uppercase tracking-widest text-sm mb-4">
                                    <div className="w-8 h-8 rounded-lg bg-amber-200 text-amber-800 flex items-center justify-center"><AlertTriangle size={16} /></div>
                                    Strict Platform Regulations
                                </div>
                                <ul className="space-y-3">
                                    {['Late repayments incur a 2.5% penalty monthly.', 'Legal action will be initiated against the guarantor in case of default.', 'Platform and insurance fees are non-refundable upon disbursement.'].map((rule, ri) => (
                                        <li key={ri} className="flex gap-3 text-sm font-medium text-amber-800/80">
                                            <span className="text-amber-500">•</span> {rule}
                                        </li>
                                    ))}
                                </ul>
                            </div>

                            <div className="form-group mb-12 flex items-center gap-4 bg-slate-50 p-6 rounded-2xl border border-slate-100">
                                <input
                                    type="checkbox"
                                    id="agreeRules"
                                    name="agreeRules"
                                    checked={formData.agreeRules}
                                    onChange={(e) => setFormData({ ...formData, agreeRules: e.target.checked })}
                                    required
                                    className="w-6 h-6 rounded-lg border-2 border-slate-200 text-primary focus:ring-primary cursor-pointer"
                                />
                                <label htmlFor="agreeRules" className="text-sm font-black text-slate-700 select-none cursor-pointer">
                                    I fully understand and agree to the Artha Lending & Borrowing policies.
                                </label>
                            </div>

                            <div className="form-section-header mb-8 flex items-center gap-4">
                                <h4 className="text-lg font-black text-slate-900">Legal Document & Identity Verification</h4>
                                <div className="h-px flex-1 bg-slate-100"></div>
                            </div>

                            {/* Policy Acceptance Section */}
                            <div className="p-8 rounded-3xl bg-gradient-to-br from-blue-50 to-blue-100/50 border-2 border-blue-200 mb-6">
                                <div className="flex items-start gap-4 mb-4">
                                    <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center font-black text-lg flex-shrink-0">1</div>
                                    <div className="flex-1">
                                        <h5 className="font-black text-slate-900 text-base mb-2">Policy Acceptance</h5>
                                        <p className="text-sm text-slate-600 leading-relaxed">Download, print, sign, and fingerprint the policy document.</p>
                                    </div>
                                </div>
                                
                                <div className="ml-14">
                                    <a 
                                        href={agreementPdf ? `${BACKEND_BASE_URL}${agreementPdf}` : '#'} 
                                        target="_blank" 
                                        rel="noopener noreferrer" 
                                        className="inline-flex items-center gap-2 text-sm font-bold text-blue-600 hover:text-blue-700 hover:underline mb-6 transition-colors"
                                    >
                                        <Upload size={16} style={{ transform: 'rotate(180deg)' }} /> 
                                        Download Official Policy (PDF)
                                    </a>
                                    
                                    <label className="block">
                                        <div className="upload-tile upload-tile-md w-full text-center py-6 rounded-2xl transition-all cursor-pointer hover:scale-[1.02] active:scale-[0.98]">
                                            <Upload size={24} className="mx-auto mb-2 text-slate-400" />
                                            <span className="text-sm font-bold text-slate-700 block mb-1">Upload Signed Copy</span>
                                            <span className="text-xs text-slate-500">PDF or Image</span>
                                            {formData.signedDoc && (
                                                <div className="mt-3 px-4 py-2 bg-green-100 text-green-700 text-xs font-black uppercase tracking-tight rounded-full inline-block">
                                                    ✓ File Ready
                                                </div>
                                            )}
                                        </div>
                                        <input type="file" name="signedDoc" onChange={handleFile} accept=".pdf,image/*" className="hidden" />
                                    </label>
                                </div>
                            </div>

                            {/* Video Statement Section */}
                            <div className="p-8 rounded-3xl bg-gradient-to-br from-amber-50 to-amber-100/50 border-2 border-amber-200 mb-12">
                                <div className="flex items-start gap-4 mb-4">
                                    <div className="w-10 h-10 rounded-full bg-amber-600 text-white flex items-center justify-center font-black text-lg flex-shrink-0">2</div>
                                    <div className="flex-1">
                                        <h5 className="font-black text-slate-900 text-base mb-2">Video Statement</h5>
                                        <div className="bg-white/80 backdrop-blur p-4 rounded-xl border border-amber-200 mb-4">
                                            <p className="text-xs font-bold text-slate-600 mb-2">Please record yourself saying:</p>
                                            <p className="text-sm font-medium text-slate-900 italic leading-relaxed">
                                                "म मेरो ऋणको सबै नियम र सर्तहरू स्वीकार गर्दछु र समयमै चुक्ता गर्ने वाचा गर्दछु।"
                                            </p>
                                        </div>
                                    </div>
                                </div>
                                
                                <div className="ml-14">
                                    <label className="block">
                                        <div className="upload-tile upload-tile-lg w-full text-center py-10 rounded-2xl transition-all cursor-pointer group hover:scale-[1.02] active:scale-[0.98]">
                                            <div className="w-16 h-16 rounded-full bg-white shadow-lg flex items-center justify-center mx-auto mb-4 group-hover:bg-amber-600 group-hover:text-white transition-all">
                                                <Video size={32} />
                                            </div>
                                            <span className="text-sm font-bold text-slate-700 block mb-1">Record or Upload Video</span>
                                            <span className="text-xs text-slate-500">Click to select video file</span>
                                            {formData.videoStatement && (
                                                <div className="mt-4 px-4 py-2 bg-green-100 text-green-700 text-xs font-black uppercase tracking-tight rounded-full inline-block">
                                                    ✓ Statement Saved
                                                </div>
                                            )}
                                        </div>
                                        <input type="file" name="videoStatement" onChange={handleFile} accept="video/*" className="hidden" />
                                    </label>
                                </div>
                            </div>

                            <div className="flex gap-6">
                                <button type="button" onClick={() => setStep(1)} className="btn btn-outline flex-1 py-5" disabled={loading}>
                                    Previous
                                </button>
                                <button type="submit" className="btn btn-primary flex-[2] py-5 shadow-xl shadow-blue-500/20 font-black" disabled={loading}>
                                    {loading ? 'Submitting Application...' : 'Submit Loan Application'}
                                </button>
                            </div>
                        </form>
                    )}
                </div>
            </div>
        </div>
    );
};

export default LoanRequest;
