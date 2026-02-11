import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Phone, Lock, ArrowRight } from 'lucide-react';
import logo from '../../assets/artha-logo.jpg';
import '../../styles/Auth.css'; // Shared Auth styles

const Login = () => {
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await login(phone, password);
            navigate('/'); // Redirect to home or dashboard
        } catch (err) {
            setError('Invalid phone number or password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-card card">
                <div className="auth-header text-center">
                    <img src={logo} alt="Artha" className="auth-logo mb-4" />
                    <h2>Welcome Back</h2>
                    <p>Login to access your Artha account</p>
                </div>

                {error && <div className="alert-error">{error}</div>}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label>Phone Number</label>
                        <div className="input-wrapper">
                            <Phone size={18} className="input-icon" />
                            <input
                                type="tel"
                                placeholder="98XXXXXXXX"
                                value={phone}
                                onChange={(e) => setPhone(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <div className="input-wrapper">
                            <Lock size={18} className="input-icon" />
                            <input
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-actions display-flex justify-between items-center mb-4">
                        <Link to="/forgot-password" style={{ fontSize: '0.9rem', color: 'var(--color-primary)' }}>Forgot Password?</Link>
                    </div>

                    <button type="submit" className="btn btn-primary w-100" disabled={loading}>
                        {loading ? 'Logging in...' : 'Login'} <ArrowRight size={18} className="ml-2" />
                    </button>
                </form>

                <div className="auth-footer text-center mt-4">
                    <p>Don't have an account? <Link to="/signup" className="text-primary font-bold">Sign Up</Link></p>
                </div>
            </div>
        </div>
    );
};

export default Login;
