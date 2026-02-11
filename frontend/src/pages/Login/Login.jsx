import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Phone, Lock, ArrowRight, LogOut } from 'lucide-react';
import logo from '../../assets/artha-logo.jpg';
import '../../styles/Auth.css'; // Shared Auth styles

const Login = () => {
    const [phone, setPhone] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { user, login, logout } = useAuth();
    const navigate = useNavigate();

    console.log('[Login] User state:', user ? `${user.firstName} ${user.lastName}` : 'null');

    const handleLogout = () => {
        logout();
        setError('');
        setPhone('');
        setPassword('');
    };

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

    // If user is already logged in, show a message
    if (user) {
        return (
            <div className="auth-page">
                <div className="auth-card card">
                    <div className="auth-header text-center">
                        <img src={logo} alt="Artha" className="auth-logo mb-4" />
                        <h2>Already Logged In</h2>
                        <p>You are currently logged in as <strong>{user.name}</strong></p>
                    </div>

                    <div className="alert-info mb-4" style={{ textAlign: 'center' }}>
                        <p>Want to log in as a different user?</p>
                        <button onClick={handleLogout} className="btn btn-outline mt-3">
                            <LogOut size={18} className="mr-2" />
                            Logout and Login as Different User
                        </button>
                    </div>

                    <div className="auth-footer text-center mt-4">
                        <Link to="/" className="btn btn-primary">
                            Go to Home
                        </Link>
                    </div>
                </div>
            </div>
        );
    }

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
