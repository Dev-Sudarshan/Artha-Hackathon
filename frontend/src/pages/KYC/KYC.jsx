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
        dob: '',
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
        // Redirect if KYC already submitted (pending/processing/verified)
        if (!authLoading && user) {
            const status = user.kycStatus;
            if (status === 'verified' || status === 'pending_admin_review' || status === 'processing') {
                navigate('/profile');
            }
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

            // Use DOB from form (user may have entered it) or fall back to user profile
            const dob = formData.dob || user.dob || '';
            if (!dob) {
                alert('Date of Birth is required. Please fill it in.');
                setLoading(false);
                return;
            }

            // When "Same as Permanent" is checked, always use current permAddress
            const tempAddr = formData.sameAddress ? formData.permAddress : formData.tempAddress;

            const payload = {
                basic_info: {
                    first_name: user.firstName || '',
                    middle_name: user.middleName || '',
                    last_name: user.lastName || '',
                    date_of_birth: dob,
                    phone: user.phone || '',
                    gender: formData.gender,
                    profession: formData.profession,
                    father_name: formData.fatherName,
                },
                permanent_address: {
                    province: formData.permAddress.province || '',
                    district: formData.permAddress.district || '',
                    municipality: formData.permAddress.municipality || '',
                    ward: parseInt(formData.permAddress.ward) || 0
                },
                temporary_address: {
                    province: tempAddr.province || '',
                    district: tempAddr.district || '',
                    municipality: tempAddr.municipality || '',
                    ward: parseInt(tempAddr.ward) || 0
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
                setLoading(false);
                return;
            }

            await kycService.submitSelfie(user.phone, formData.livePhoto, text);

            // Verification now runs in background - don't wait for it
            await refreshUser();
            alert('KYC submitted successfully! Verification is being processed. You will be notified once reviewed.');
            navigate('/profile');
        } catch (error) {
            console.error("Step 3 Error", error);
            alert("Submission failed: " + (error.response?.data?.detail || error.message));
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
                            loading={loading}
                        />
                    )}
                    {step === 2 && (
                        <Step2Documents
                            data={formData}
                            updateData={updateData}
                            nextStep={handleStep2Submit}
                            prevStep={prevStep}
                            loading={loading}
                        />
                    )}
                    {step === 3 && (
                        <Step3Verification
                            data={formData}
                            updateData={updateData}
                            submit={handleSubmit}
                            prevStep={prevStep}
                            loading={loading}
                        />
                    )}
                </div>
            </div>
        </div>
    );
};

export default KYC;
