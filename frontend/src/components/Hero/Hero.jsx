import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { ArrowRight, ShieldCheck } from 'lucide-react';
import './Hero.css';

const Hero = () => {
    const { user } = useAuth();

    return (
        <section className="hero">
            <div className="hero-container container">
                <div className="hero-content">
                    <div className="hero-badge">
                        <ShieldCheck size={16} />
                        <span>Nepal's Trusted P2P Network</span>
                    </div>
                    <h1>Financial Freedom for Every Nepali</h1>
                    <p className="hero-subtitle">
                        Artha bridges the gap between those with capital and those with dreams.
                        Direct, transparent, and community-driven lending.
                    </p>

                    <div className="hero-actions">
                        {!user ? (
                            <>
                                <Link to="/signup" className="btn btn-primary">
                                    Start Journey <ArrowRight size={20} />
                                </Link>
                                <Link to="/login" className="btn btn-outline">Member Login</Link>
                            </>
                        ) : (
                            <>
                                {user.kycStatus !== 'verified' ? (
                                    <Link to="/kyc" className="btn btn-primary">
                                        Verify to Invest <ArrowRight size={20} />
                                    </Link>
                                ) : (
                                    <Link to="/marketplace" className="btn btn-primary">
                                        Explore Loans <ArrowRight size={20} />
                                    </Link>
                                )}
                                <Link to="/portfolio" className="btn btn-outline">My Dashboard</Link>
                            </>
                        )}
                    </div>
                </div>

                <div className="hero-image mobile-hide">
                    <div className="hero-visual">
                        <div className="visual-card card-1 shadow-premium">
                            <span>13% p.a.</span>
                            <small>Guaranteed Community Rate</small>
                        </div>
                        <div className="visual-card card-2 shadow-premium">
                            <span>NPR 100k</span>
                            <small>Max Micro-Loan Limit</small>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default Hero;
