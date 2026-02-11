import { Link } from 'react-router-dom';
import logo from '../../assets/artha-logo.jpg';
import './Footer.css';

const Footer = () => {
    return (
        <footer className="footer">
            <div className="container">
                <div className="footer-top grid grid-4">
                    <div className="footer-brand">
                        <img src={logo} alt="Artha" className="footer-logo mb-4" />
                        <p>Empowering Nepal through community-driven finance. Transparent, secure, and accessible to all.</p>
                    </div>

                    <div className="footer-links">
                        <h4>Platform</h4>
                        <ul>
                            <li><Link to="/">Home</Link></li>
                            <li><Link to="/marketplace">Marketplace</Link></li>
                            <li><Link to="/portfolio">Portfolio</Link></li>
                        </ul>
                    </div>

                    <div className="footer-links">
                        <h4>Legal</h4>
                        <ul>
                            <li><Link to="/privacy">Privacy Policy</Link></li>
                            <li><Link to="/terms">Terms of Service</Link></li>
                            <li><Link to="/compliance">Compliance</Link></li>
                        </ul>
                    </div>

                    <div className="footer-links">
                        <h4>Contact</h4>
                        <ul>
                            <li>support@artha.com.np</li>
                            <li>+977-9800000000</li>
                            <li>Kathmandu, Nepal</li>
                        </ul>
                    </div>
                </div>

                <div className="footer-bottom">
                    <p>&copy; {new Date().getFullYear()} Artha Financial Services. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
