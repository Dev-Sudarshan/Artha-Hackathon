import { NavLink, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Menu, X, User, LogOut } from 'lucide-react';
import { useState } from 'react';
import logo from '../../assets/artha-logo.jpg';
import './Navbar.css';

const Navbar = () => {
    const { user, logout } = useAuth();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

    return (
        <nav className="navbar">
            <div className="navbar-container container">
                <div className="navbar-logo">
                    <Link to="/">
                        <img src={logo} alt="Artha Logo" className="logo-img" />
                    </Link>
                </div>

                {/* Desktop Menu */}
                <div className={`navbar-menu ${isMenuOpen ? 'active' : ''}`}>
                    <div className="navbar-links">
                        <NavLink to="/" className={({ isActive }) => (isActive ? 'active' : '')} onClick={() => setIsMenuOpen(false)}>
                            Home
                        </NavLink>
                        <NavLink to="/marketplace" className={({ isActive }) => (isActive ? 'active' : '')} onClick={() => setIsMenuOpen(false)}>
                            Marketplace
                        </NavLink>
                        <NavLink to="/portfolio" className={({ isActive }) => (isActive ? 'active' : '')} onClick={() => setIsMenuOpen(false)}>
                            Portfolio
                        </NavLink>
                        {/* <NavLink to="/about" className={({ isActive }) => (isActive ? 'active' : '')}>About Us</NavLink> */}
                    </div>

                    <div className="navbar-auth">
                        {user ? (
                            <div className="user-menu">
                                <Link to="/profile" className="user-profile" onClick={() => setIsMenuOpen(false)}>
                                    <img src={user.avatar} alt={user.name} className="user-avatar" />
                                    <span>{user.name.split(' ')[0]}</span>
                                </Link>
                                <button onClick={handleLogout} className="btn-logout" title="Logout">
                                    <LogOut size={18} />
                                </button>
                            </div>
                        ) : (
                            <div className="auth-buttons">
                                <Link to="/login" className="btn btn-outline" onClick={() => setIsMenuOpen(false)}>Login</Link>
                                <Link to="/signup" className="btn btn-primary" onClick={() => setIsMenuOpen(false)}>Sign Up</Link>
                            </div>
                        )}
                    </div>
                </div>

                <button className="navbar-toggle" onClick={toggleMenu}>
                    {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>
        </nav>
    );
};

export default Navbar;
