import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Phone, Lock, User, Calendar, ArrowRight, Key } from 'lucide-react';
import logo from '../../assets/artha-logo.jpg';
import '../../styles/Auth.css';

const Signup = () => {
    const [formData, setFormData] = useState({
        firstName: '',
        middleName: '',
        lastName: '',
        dob: '',
        phone: '',
        password: '',
        confirmPassword: ''
    });

    const [otp, setOtp] = useState('');
    const [otpSent, setOtpSent] = useState(false);

    const [agree, setAgree] = useState(false);
    const [loading, setLoading] = useState(false);
    const { register, verifyOtp } = useAuth();
    const navigate = useNavigate();

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // OTP Verification Step
        if (otpSent) {
            setLoading(true);
            try {
                await verifyOtp(formData.phone, otp);
                alert("Account verified successfully! Please login.");
                navigate('/login');
            } catch (error) {
                console.error(error);
                alert(error.response?.data?.detail || "Invalid OTP");
            } finally {
                setLoading(false);
            }
            return;
        }

        // Registration Step
        if (formData.password !== formData.confirmPassword) {
            alert("Passwords do not match");
            return;
        }
        if (!agree) {
            alert("Please agree to the terms");
            return;
        }

        setLoading(true);
        try {
            await register(formData);
            setOtpSent(true);
            alert(`OTP sent to ${formData.phone}`);
        } catch (error) {
            console.error(error);
            alert(error.response?.data?.detail || "Registration failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card card" style={{ maxWidth: '550px' }}>
                <div className="auth-header text-center">
                    <img src={logo} alt="Artha" className="auth-logo mb-4" />
                    <h2>{otpSent ? 'Verify Phone' : 'Create Account'}</h2>
                    <p>{otpSent ? `Enter the code sent to ${formData.phone}` : 'Join the Artha community today'}</p>
                </div>

                <form onSubmit={handleSubmit}>
                    {!otpSent ? (
                        <>
                            <div className="grid grid-2" style={{ gap: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
                                <div className="form-group">
                                    <label>First Name</label>
                                    <div className="input-wrapper no-icon">
                                        <input type="text" name="firstName" value={formData.firstName} onChange={handleChange} required />
                                    </div>
                                </div>
                                <div className="form-group">
                                    <label>Last Name</label>
                                    <div className="input-wrapper no-icon">
                                        <input type="text" name="lastName" value={formData.lastName} onChange={handleChange} required />
                                    </div>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Middle Name (Optional)</label>
                                <div className="input-wrapper no-icon">
                                    <input type="text" name="middleName" value={formData.middleName} onChange={handleChange} />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Date of Birth</label>
                                <div className="input-wrapper">
                                    <Calendar size={18} className="input-icon" />
                                    <input type="date" name="dob" value={formData.dob} onChange={handleChange} required />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Phone Number</label>
                                <div className="input-wrapper">
                                    <Phone size={18} className="input-icon" />
                                    <input type="tel" name="phone" placeholder="98XXXXXXXX" value={formData.phone} onChange={handleChange} required />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Password</label>
                                <div className="input-wrapper">
                                    <Lock size={18} className="input-icon" />
                                    <input type="password" name="password" value={formData.password} onChange={handleChange} required />
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Confirm Password</label>
                                <div className="input-wrapper">
                                    <Lock size={18} className="input-icon" />
                                    <input type="password" name="confirmPassword" value={formData.confirmPassword} onChange={handleChange} required />
                                </div>
                            </div>

                            <div className="checkbox-group">
                                <input type="checkbox" id="terms" checked={agree} onChange={(e) => setAgree(e.target.checked)} required />
                                <label htmlFor="terms">
                                    I agree to the <Link to="/terms" className="text-primary">Terms of Service</Link> and <Link to="/privacy" className="text-primary">Privacy Policy</Link>
                                </label>
                            </div>
                        </>
                    ) : (
                        <div className="form-group">
                            <label>One-Time Password (OTP)</label>
                            <div className="input-wrapper">
                                <Key size={18} className="input-icon" />
                                <input
                                    type="text"
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value)}
                                    placeholder="Enter 6-digit code"
                                    required
                                    maxLength="6"
                                    className="text-center text-lg tracking-widest font-bold"
                                />
                            </div>
                            <p className="text-xs text-muted text-center mt-3 cursor-pointer hover:text-primary" onClick={() => setOtpSent(false)}>
                                Incorrect number? Go back
                            </p>
                        </div>
                    )}

                    <button type="submit" className="btn btn-primary w-100 mt-4" disabled={loading}>
                        {loading ? 'Processing...' : (otpSent ? 'Verify & Finish' : 'Sign Up')} <ArrowRight size={18} className="ml-2" />
                    </button>
                </form>

                <div className="auth-footer text-center mt-4">
                    <p>Already have an account? <Link to="/login" className="text-primary font-bold">Login</Link></p>
                </div>
            </div>
        </div>
    );
};

export default Signup;
