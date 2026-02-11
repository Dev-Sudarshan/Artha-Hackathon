import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Hero from '../../components/Hero/Hero';
import Stats from '../../components/Stats/Stats';
import HowItWorks from '../../components/HowItWorks/HowItWorks';
import WhyArtha from '../../components/WhyArtha/WhyArtha';
import TrustSecurity from '../../components/TrustSecurity/TrustSecurity';
import Footer from '../../components/Footer/Footer';
import { CheckCircle, X } from 'lucide-react';
import '../../styles/global.css';

const Home = () => {
    const location = useLocation();
    const [showPopup, setShowPopup] = useState(false);

    useEffect(() => {
        if (location.state?.loanSubmitted) {
            setShowPopup(true);
            // Clear state so it doesn't show again on refresh
            window.history.replaceState({}, document.title);
        }
    }, [location]);

    return (
        <>
            {showPopup && (
                <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-900/60 backdrop-blur-sm animate-fade">
                    <div className="bg-white rounded-[2rem] p-10 max-w-md w-full shadow-2xl relative animate-slide-up mx-4" style={{ zIndex: 10000 }}>
                        <button
                            onClick={() => setShowPopup(false)}
                            className="absolute top-6 right-6 p-2 rounded-full hover:bg-slate-100 transition-colors"
                        >
                            <X size={20} className="text-slate-400" />
                        </button>
                        <div className="text-center">
                            <div className="w-20 h-20 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6">
                                <CheckCircle size={40} className="text-emerald-500" />
                            </div>
                            <h2 className="text-2xl font-black text-slate-900 mb-4">Request Submitted!</h2>
                            <p className="text-slate-600 leading-relaxed mb-8">
                                Your loan request is currently being processed by our AI verification system.
                                Once verified, it will be automatically published to the marketplace.
                            </p>
                            <button
                                onClick={() => setShowPopup(false)}
                                className="w-full py-4 bg-slate-900 text-white rounded-2xl font-bold hover:bg-slate-800 transition-all shadow-lg"
                            >
                                Got it, thanks!
                            </button>
                        </div>
                    </div>
                </div>
            )}
            <main>
                <Hero />
                <Stats />
                <HowItWorks />
                <WhyArtha />
                <TrustSecurity />
            </main>
            <Footer />
        </>
    );
};

export default Home;
