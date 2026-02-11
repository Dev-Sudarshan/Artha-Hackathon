import { Percent, TrendingUp, Shield, MapPin } from 'lucide-react';
import './WhyArtha.css';

const WhyArtha = () => {
    const features = [
        {
            icon: <Percent size={28} />,
            title: 'Lower Interest Rates',
            desc: 'Borrow at fixed 13% p.a., significantly lower than traditional informal lenders.'
        },
        {
            icon: <TrendingUp size={28} />,
            title: 'Better Returns',
            desc: 'Lenders earn more than savings accounts with monthly EMI payouts.'
        },
        {
            icon: <Shield size={28} />,
            title: 'Full Transparency',
            desc: 'No hidden fees. 2% platform fee and 1% insurance fee, clearly stated.'
        },
        {
            icon: <MapPin size={28} />,
            title: 'Built for Nepal',
            desc: 'Tailored to local needs, supporting community growth and financial inclusion.'
        }
    ];

    return (
        <section className="why-artha section-padding bg-subtle">
            <div className="container">
                <div className="section-header text-center">
                    <h2>Why Choose Artha?</h2>
                    <p>We bridge the gap between aspirations and capital.</p>
                </div>

                <div className="grid grid-4 gap-8 mt-12">
                    {features.map((feature, index) => (
                        <div key={index} className={`feature-card animate-slide-up delay-${(index + 1) * 100}`}>
                            <div className="feature-icon">
                                {feature.icon}
                            </div>
                            <h3>{feature.title}</h3>
                            <p>{feature.desc}</p>
                        </div>
                    ))}
                </div>
            </div>
        </section>
    );
};

export default WhyArtha;
