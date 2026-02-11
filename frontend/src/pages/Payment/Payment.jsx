import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
    Smartphone,
    Lock,
    CheckCircle,
    ArrowLeft,
    ChevronRight,
    ShieldCheck,
    AlertCircle
} from 'lucide-react';
import './Payment.css';
import loanService from '../../services/loanService';

const Payment = () => {
    const { user, setUserRole } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const loan = location.state?.loan;

    const [step, setStep] = useState(1);
    const [method, setMethod] = useState('');
    const [credentials, setCredentials] = useState({ mobile: '', password: '' });
    const [otp, setOtp] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);

    useEffect(() => {
        if (!loan) {
            navigate('/marketplace');
        }
    }, [loan, navigate]);

    if (!loan) return null;

    const handleNext = () => {
        if (step === 2 && (!credentials.mobile || !credentials.password)) {
            alert("Please enter your credentials.");
            return;
        }
        if (step === 3 && otp.length < 6) {
            alert("Please enter a valid 6-digit OTP.");
            return;
        }

        if (step < 4) {
            setIsProcessing(true);
            setTimeout(() => {
                setIsProcessing(false);
                setStep(step + 1);
            }, 1000);
        } else {
            // Final Confirm
            handleSubmit();
        }
    };



    const handleSubmit = async () => {
        setIsProcessing(true);
        try {
            // Call the backend API to fund the loan
            // Note: Current backend Mock Transaction Ref is handled in service or backend?
            // Service sends mock ref. Backend accepts it.
            await loanService.fundLoan(loan.id, loan.amount);

            setUserRole('lender'); // Lock role to lender per business rule
            setStep(5); // Success Step
        } catch (error) {
            console.error("Funding failed", error);
            alert("Transaction failed: " + (error.response?.data?.detail || error.message));
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <div className="container mt-8 mb-12">
            <div className="payment-gateway-wrapper">
                <div className="payment-sidebar card glass animate-fade">
                    <div className="order-summary">
                        <h3>Investment Summary</h3>
                        <div className="loan-brief mt-4">
                            <p className="text-muted text-sm">Borrower</p>
                            <p className="font-bold">{loan.borrower}</p>

                            <p className="text-muted text-sm mt-3">Purpose</p>
                            <p className="font-medium text-sm">{loan.purpose}</p>

                            <hr className="my-4" style={{ borderColor: 'var(--color-bg-subtle)' }} />

                            <div className="flex justify-between items-center mb-2">
                                <span className="text-muted">Investment Amount</span>
                                <span className="font-bold">NPR {loan.amount.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-muted">Processing Fee</span>
                                <span className="text-success">FREE</span>
                            </div>

                            <div className="total-row flex justify-between items-center mt-6">
                                <span>Total Payable</span>
                                <span className="total-amount">NPR {loan.amount.toLocaleString()}</span>
                            </div>
                        </div>
                    </div>

                    <div className="security-note mt-12 p-4 rounded-xl mt-auto">
                        <div className="flex gap-3 text-sm text-muted">
                            <ShieldCheck className="text-primary flex-shrink-0" size={18} />
                            <p>Artha uses 256-bit encryption to ensure your transaction is safe and secure.</p>
                        </div>
                    </div>
                </div>

                <div className="payment-main card animate-slide-up">
                    <div className="gateway-header mb-8">
                        <div className="flex items-center gap-4">
                            {step > 1 && step < 5 && (
                                <button onClick={() => setStep(step - 1)} className="back-btn">
                                    <ArrowLeft size={20} />
                                </button>
                            )}
                            <div>
                                <h2>Payment Gateway</h2>
                                <div className="step-indicator">
                                    <span className={step >= 1 ? 'active' : ''}>Method</span>
                                    <div className="line"></div>
                                    <span className={step >= 2 ? 'active' : ''}>Login</span>
                                    <div className="line"></div>
                                    <span className={step >= 3 ? 'active' : ''}>OTP</span>
                                    <div className="line"></div>
                                    <span className={step >= 4 ? 'active' : ''}>Confirm</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="gateway-content">
                        {step === 1 && (
                            <div className="step-1 animate-fade">
                                <h3 className="mb-6">Select Payment Method</h3>
                                <div className="method-grid">
                                    <div
                                        className={`method-card ${method === 'khalti' ? 'active' : ''}`}
                                        onClick={() => { setMethod('khalti'); setStep(2); }}
                                    >
                                        <div className="method-logo khalti">K</div>
                                        <span>Khalti Wallet</span>
                                    </div>
                                    <div
                                        className={`method-card ${method === 'esewa' ? 'active' : ''}`}
                                        onClick={() => { setMethod('esewa'); setStep(2); }}
                                    >
                                        <div className="method-logo esewa">e</div>
                                        <span>eSewa Wallet</span>
                                    </div>
                                    <div
                                        className={`method-card ${method === 'bank' ? 'active' : ''}`}
                                        onClick={() => { setMethod('bank'); setStep(2); }}
                                    >
                                        <div className="method-logo bank">B</div>
                                        <span>Mobile Banking</span>
                                    </div>
                                    <div className="method-card disabled">
                                        <div className="method-logo">C</div>
                                        <span>Debit/Credit Card</span>
                                    </div>
                                </div>
                            </div>
                        )}

                        {step === 2 && (
                            <div className="step-2 animate-fade">
                                <h3 className="mb-2">Login to {method.charAt(0).toUpperCase() + method.slice(1)}</h3>
                                <p className="text-muted mb-6">Enter your registered mobile number and password.</p>

                                <div className="form-group mb-4">
                                    <label>Registered Mobile Number</label>
                                    <div className="input-with-icon">
                                        <Smartphone className="icon" size={18} />
                                        <input
                                            type="text"
                                            placeholder="98XXXXXXXX"
                                            value={credentials.mobile}
                                            onChange={(e) => setCredentials({ ...credentials, mobile: e.target.value })}
                                        />
                                    </div>
                                </div>
                                <div className="form-group mb-8">
                                    <label>Wallet Password / PIN</label>
                                    <div className="input-with-icon">
                                        <Lock className="icon" size={18} />
                                        <input
                                            type="password"
                                            placeholder="Enter Password"
                                            value={credentials.password}
                                            onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <button onClick={handleNext} className="btn btn-primary w-100 py-4" disabled={isProcessing}>
                                    {isProcessing ? 'Verifying...' : 'Continue to OTP'} <ChevronRight size={18} />
                                </button>
                            </div>
                        )}

                        {step === 3 && (
                            <div className="step-3 animate-fade text-center">
                                <div className="otp-icon-wrapper mb-6">
                                    <Smartphone size={32} className="text-primary" />
                                </div>
                                <h3 className="mb-2">Enter OTP Code</h3>
                                <p className="text-muted mb-8">A 6-digit confirmation code has been sent to <br /> <strong>+977 {credentials.mobile}</strong></p>

                                <div className="otp-input-container mb-8">
                                    <input
                                        type="text"
                                        maxLength="6"
                                        className="otp-input"
                                        placeholder="0 0 0 0 0 0"
                                        value={otp}
                                        onChange={(e) => setOtp(e.target.value)}
                                        style={{ textAlign: 'center', letterSpacing: '12px', fontSize: '1.5rem', fontWeight: 'bold' }}
                                    />
                                </div>

                                <button onClick={handleNext} className="btn btn-primary w-100 py-4" disabled={isProcessing}>
                                    {isProcessing ? 'Confirming...' : 'Verify & Continue'}
                                </button>
                                <p className="mt-6 text-sm">Didn't receive code? <button className="btn-link">Resend OTP</button></p>
                            </div>
                        )}

                        {step === 4 && (
                            <div className="step-4 animate-fade">
                                <h3 className="mb-6">Final Confirmation</h3>
                                <div className="confirm-box p-6 rounded-xl border-dashed mb-8" style={{ border: '2px dashed var(--color-border)' }}>
                                    <div className="flex justify-between items-center mb-4">
                                        <span className="text-muted">Total Payment</span>
                                        <span className="font-bold text-xl">NPR {loan.amount.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between items-center mb-4">
                                        <span className="text-muted">Authorized By</span>
                                        <span className="font-medium">{credentials.mobile}</span>
                                    </div>
                                    <div className="flex justify-between items-center">
                                        <span className="text-muted">Reference ID</span>
                                        <span className="text-muted text-sm">#ART-{Math.floor(Math.random() * 900000 + 100000)}</span>
                                    </div>
                                </div>

                                <div className="warning-note flex gap-3 p-4 bg-orange-50 rounded-lg text-sm text-orange-800 mb-8" style={{ background: '#FFF7ED', color: '#9A3412', borderRadius: '12px' }}>
                                    <AlertCircle size={20} className="flex-shrink-0" />
                                    <p>By clicking "Pay Now", you authorize the transfer of the full amount to the borrower's escrow account.</p>
                                </div>

                                <button onClick={handleNext} className="btn btn-primary w-100 py-4" disabled={isProcessing}>
                                    {isProcessing ? 'Processing Transaction...' : `Confirm & Pay NPR ${loan.amount.toLocaleString()}`}
                                </button>
                            </div>
                        )}

                        {step === 5 && (
                            <div className="step-5 animate-fade text-center py-8">
                                <div className="success-icon-wrapper mb-6 animate-scale-up">
                                    <CheckCircle size={80} className="text-success mx-auto" strokeWidth={1.5} />
                                </div>
                                <h2 className="mb-4">Investment Successful!</h2>
                                <p className="text-muted mb-8 text-lg">
                                    Your investment of <strong>NPR {loan.amount.toLocaleString()}</strong> <br />
                                    in <strong>{loan.borrower}'s</strong> loan has been processed.
                                </p>

                                <div className="success-actions flex gap-4 justify-center">
                                    <button onClick={() => navigate('/portfolio')} className="btn btn-primary px-8">View Portfolio</button>
                                    <button onClick={() => navigate('/marketplace')} className="btn btn-outline px-8">Back to Marketplace</button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Payment;
