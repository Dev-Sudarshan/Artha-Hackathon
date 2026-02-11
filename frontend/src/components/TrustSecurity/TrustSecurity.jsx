import { Lock, BadgeCheck, FileText } from 'lucide-react';
import './TrustSecurity.css';

const TrustSecurity = () => {
    return (
        <section className="trust-security section-padding">
            <div className="container">
                <div className="trust-wrapper animate-fade">
                    <div className="text-center mb-16">
                        <span className="badge badge-success mb-4">SECURITY FIRST</span>
                        <h2>Bank-Level Infrastructure</h2>
                        <p>Your financial security and privacy are our highest priorities.</p>
                    </div>

                    <div className="grid grid-3 gap-8">
                        <div className="trust-item">
                            <div className="flex justify-center mb-6">
                                <div className="p-5 rounded-3xl bg-blue-50 text-primary">
                                    <Lock size={40} />
                                </div>
                            </div>
                            <h4>End-to-End Encryption</h4>
                            <p>We use military-grade AES-256 encryption to protect your data and transactions.</p>
                        </div>
                        <div className="trust-item">
                            <div className="flex justify-center mb-6">
                                <div className="p-5 rounded-3xl bg-blue-50 text-primary">
                                    <BadgeCheck size={40} />
                                </div>
                            </div>
                            <h4>Verified Community</h4>
                            <p>Every Artha member undergoes rigorous identity verification via digital KYC.</p>
                        </div>
                        <div className="trust-item">
                            <div className="flex justify-center mb-6">
                                <div className="p-5 rounded-3xl bg-blue-50 text-primary">
                                    <FileText size={40} />
                                </div>
                            </div>
                            <h4>Legal Framework</h4>
                            <p>Our platform operates within the legal guidelines for P2P finance in Nepal.</p>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default TrustSecurity;
