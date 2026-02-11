import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowRight, ArrowLeft } from 'lucide-react';
import '../../styles/Auth.css';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = (e) => {
        e.preventDefault();
        setSubmitted(true);
        // Backend logic would go here
    };

    return (
        <div className="auth-page">
            <div className="auth-card card">
                <div className="auth-header text-center">
                    <h2>Reset Password</h2>
                    <p>Enter your email to receive recovery instructions.</p>
                </div>

                {!submitted ? (
                    <form onSubmit={handleSubmit} className="auth-form">
                        <div className="form-group">
                            <label>Email Address</label>
                            <div className="input-wrapper">
                                <Mail size={18} className="input-icon" />
                                <input
                                    type="email"
                                    placeholder="your@email.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </div>
                        </div>

                        <button type="submit" className="btn btn-primary w-100 mt-4">
                            Send Reset Link <ArrowRight size={18} className="ml-2" />
                        </button>
                    </form>
                ) : (
                    <div className="text-center py-8">
                        <div className="w-16 h-16 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
                            <Mail size={32} />
                        </div>
                        <h3 className="text-xl font-bold mb-2">Check your inbox</h3>
                        <p className="text-muted mb-6">We've sent password reset instructions to <strong>{email}</strong></p>
                    </div>
                )}

                <div className="auth-footer text-center mt-6">
                    <Link to="/login" className="flex items-center justify-center gap-2 text-slate-500 hover:text-primary transition-colors">
                        <ArrowLeft size={16} /> Back to Login
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default ForgotPassword;
