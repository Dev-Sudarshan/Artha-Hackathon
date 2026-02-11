import { UserPlus, FileCheck, Coins, TrendingUp } from 'lucide-react';
import './HowItWorks.css';

const HowItWorks = () => {
    const steps = [
        {
            icon: <UserPlus size={32} />,
            title: 'Sign Up & KYC',
            desc: 'Create an account and verify your identity securely with digital KYC.'
        },
        {
            icon: <FileCheck size={32} />,
            title: 'List or Invest',
            desc: 'Borrowers list loan requests. Lenders browse and fund opportunities.'
        },
        {
            icon: <Coins size={32} />,
            title: 'Instant Transfer',
            desc: 'Funds are transferred directly once the loan is fully funded.'
        },
        {
            icon: <TrendingUp size={32} />,
            title: 'Grow Wealth',
            desc: 'Lenders earn monthly interest. Borrowers repay easily via the app.'
        }
    ];

    return (
        <section className="how-it-works section-padding">
            <div className="container">
                <div className="section-header text-center animate-fade">
                    <span className="badge badge-primary mb-4">EASY PROCESS</span>
                    <h2>Secure Community Lending</h2>
                    <p>Designed specifically for Nepal, Artha makes P2P lending simple and transparent.</p>
                </div>

                <div className="steps-container mt-12">
                    {steps.map((step, index) => (
                        <div key={index} className={`step-card animate-slide-up delay-${(index + 1) * 100}`}>
                            <div className="step-icon">
                                {step.icon}
                            </div>
                            <h3>{step.title}</h3>
                            <p>{step.desc}</p>
                            {index < steps.length - 1 && <div className="step-connector mobile-hide"></div>}
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default HowItWorks;
