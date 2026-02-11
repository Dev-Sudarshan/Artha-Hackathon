import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import kycService from '../../services/kycService';
import Step1PersonalInfo from './Step1PersonalInfo';
import Step2Documents from './Step2Documents';
import Step3Verification from './Step3Verification';
import { CheckCircle } from 'lucide-react';
import './KYC.css';

const KYC = () => {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);

    const [formData, setFormData] = useState({
        gender: '',
        fatherName: '',
        profession: '',
        permAddress: { province: '', district: '', municipality: '', ward: '' },
        tempAddress: { province: '', district: '', municipality: '', ward: '' },
        sameAddress: false,
        docType: 'citizenship',
        docNumber: '',
        issueDate: '',
        docFront: null,
        docBack: null,
        livePhoto: null,
        livePhotoUrl: null
    });

    const { user, loading: authLoading, refreshUser } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (!authLoading && !user) {
            navigate('/login');
        }
    }, [authLoading, user, navigate]);

    useEffect(() => {
        if (step < 1) setStep(1);
        if (step > 3) setStep(3);
    }, [step]);

    if (authLoading) {
        return <div className="container mt-8 mb-12 text-center">Loading...</div>;
    }

    if (!user) {
        return <div className="container mt-8 mb-12 text-center">Please log in to continue.</div>;
    }

    const updateData = (key, value) => {
        setFormData(prev => ({ ...prev, [key]: value }));
    };

    const nextStep = () => {
        window.scrollTo(0, 0);
        setStep(prev => Math.min(prev + 1, 3));
    };
    const prevStep = () => {
        window.scrollTo(0, 0);
        setStep(prev => Math.max(prev - 1, 1));
    };

    // --- API Handlers ---

    const handleStep1Submit = async () => {
        setLoading(true);
        try {
            // Mapping frontend Address to backend Schema is needed if structure differs.
            // Backend Schema 'KYCPageOneSchema' expects:
            /*
            first_name, middle_name, last_name, date_of_birth, gender, profession, father_name,
            permanent_address: Address, temporary_address: Address
            */
            // We need to fetch Basic Info from User Object + FormData
            // user object has: firstName, lastName, phone, dob (from login/register)
            // formData has: gender, fatherName, profession, permAddress...

            const payload = {
                basic_info: {
                    first_name: user.firstName,
                    middle_name: user.middleName || "",
                    last_name: user.lastName,
                    date_of_birth: user.dob,
                    phone: user.phone,
                    gender: formData.gender,
                    profession: formData.profession,
                    father_name: formData.fatherName,
                },
                permanent_address: {
                    ...formData.permAddress,
                    ward: parseInt(formData.permAddress.ward)
                },
                temporary_address: {
                    ...formData.tempAddress,
                    ward: parseInt(formData.tempAddress.ward)
                }
            };

            await kycService.submitBasicInfo(payload, user.phone); // using Phone as ID for now as per AuthContext
            nextStep();
        } catch (error) {
            console.error("Step 1 Error", error);
            alert("Failed to submit basic info: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleStep2Submit = async () => {
        console.log("Step 2 Submit Started");
        setLoading(true);
        try {
            console.log("Uploading documents and running OCR...");
            await kycService.submitIdDocuments(
                user.phone,
                formData.docType,
                formData.docNumber,
                formData.issueDate,
                formData.docFront,
                formData.docBack
            );
            console.log("Step 2 Success, moving to Step 3");
            nextStep();
        } catch (error) {
            console.error("Step 2 Error", error);
            alert("Failed to upload/verify documents: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const text = "I declare that the information provided is true.";
            if (!formData.livePhoto) {
                alert('Please capture your photo first.');
                return;
            }

            await kycService.submitSelfie(user.phone, formData.livePhoto, text);

            const refreshed = await refreshUser();
            if (refreshed?.kycStatus === 'verified') {
                alert('KYC Verified Successfully!');
                navigate('/profile');
            } else if (String(refreshed?.kycStatus || '').toLowerCase() === 'rejected') {
                alert('KYC was rejected. Please try again.');
            } else {
                alert('KYC submitted. Status: ' + (refreshed?.kycStatus || 'pending'));
                navigate('/profile');
            }
        } catch (error) {
            console.error("Step 3 Error", error);
            alert("Verification failed: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container mt-8 mb-12 animate-fade">
            <div className="kyc-container card">
                <div className="kyc-header text-center mb-4">
                    <h2>KYC Verification</h2>
                    <p>Step {Math.min(step, 3)} of 3</p>
                </div>

                <div className="kyc-progress mb-4">
                    <div className={`progress-step ${step >= 1 ? 'active' : ''}`}>1</div>
                    <div className={`progress-line ${step >= 2 ? 'active' : ''}`}></div>
                    <div className={`progress-step ${step >= 2 ? 'active' : ''}`}>2</div>
                    <div className={`progress-line ${step >= 3 ? 'active' : ''}`}></div>
                    <div className={`progress-step ${step >= 3 ? 'active' : ''}`}>3</div>
                </div>

                {loading && <div className="text-center p-4">Processing...</div>}

                <div className={`kyc-content animate-slide-up ${loading ? 'opacity-50 pointer-events-none' : ''}`}>
                    {step === 1 && (
                        <Step1PersonalInfo
                            data={formData}
                            updateData={updateData}
                            nextStep={handleStep1Submit}
                            user={user}
                        />
                    )}
                    {step === 2 && (
                        <Step2Documents
                            data={formData}
                            updateData={updateData}
                            nextStep={handleStep2Submit}
                            prevStep={prevStep}
                        />
                    )}
                    {step === 3 && (
                        <Step3Verification
                            data={formData}
                            updateData={updateData}
                            submit={handleSubmit}
                            prevStep={prevStep}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default KYC;
