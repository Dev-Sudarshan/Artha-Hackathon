import { useMemo, useState, useRef } from 'react';
import Webcam from 'react-webcam';
import './DevKycCheck.css';

const DevKycCheck = () => {
    const apiBase = useMemo(() => {
        const params = new URLSearchParams(window.location.search);
        return params.get('api') || import.meta.env.VITE_API_URL || 'http://localhost:8000';
    }, []);

    const [ocrForm, setOcrForm] = useState({
        fullName: '',
        dob: '',
        citizenshipNo: ''
    });
    const [ocrFile, setOcrFile] = useState(null);
    const [ocrResult, setOcrResult] = useState(null);
    const [ocrError, setOcrError] = useState(null);
    const [ocrLoading, setOcrLoading] = useState(false);

    const [faceMode, setFaceMode] = useState('capture');
    const [idImage, setIdImage] = useState(null);
    const [selfieImage, setSelfieImage] = useState(null);
    const [selfieVideo, setSelfieVideo] = useState(null);
    const [capturedImage, setCapturedImage] = useState(null);
    const [faceResult, setFaceResult] = useState(null);
    const [faceError, setFaceError] = useState(null);
    const [faceLoading, setFaceLoading] = useState(false);
    const webcamRef = useRef(null);

    const handleOcrSubmit = async (event) => {
        event.preventDefault();
        setOcrError(null);
        setOcrResult(null);

        if (!ocrFile) {
            setOcrError('Please upload a citizenship front image.');
            return;
        }

        setOcrLoading(true);
        try {
            const formData = new FormData();
            formData.append('front_image', ocrFile);
            formData.append('full_name', ocrForm.fullName);
            formData.append('date_of_birth', ocrForm.dob);
            formData.append('citizenship_no', ocrForm.citizenshipNo);

            const response = await fetch(`${apiBase}/dev/ocr`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'OCR request failed');
            }

            setOcrResult(data);
        } catch (error) {
            setOcrError(error.message);
        } finally {
            setOcrLoading(false);
        }
    };

    const capturePhoto = () => {
        if (!webcamRef.current) {
            setFaceError('Camera not ready');
            return;
        }

        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) {
            setFaceError('Failed to capture image');
            return;
        }

        fetch(imageSrc)
            .then(res => res.blob())
            .then(blob => {
                const file = new File([blob], "selfie-capture.jpg", { type: "image/jpeg" });
                setCapturedImage(imageSrc);
                setSelfieImage(file);
            })
            .catch(err => {
                console.error('Error converting image:', err);
                setFaceError('Failed to process captured image');
            });
    };

    const retakePhoto = () => {
        setCapturedImage(null);
        setSelfieImage(null);
    };

    const handleFaceSubmit = async (event) => {
        event.preventDefault();
        setFaceError(null);
        setFaceResult(null);

        if (!idImage) {
            setFaceError('Please upload the ID image.');
            return;
        }

        if (faceMode === 'capture' && !selfieImage) {
            setFaceError('Please capture a selfie image.');
            return;
        }

        if (faceMode === 'image' && !selfieImage) {
            setFaceError('Please upload a selfie image.');
            return;
        }

        if (faceMode === 'video' && !selfieVideo) {
            setFaceError('Please upload a selfie video.');
            return;
        }

        setFaceLoading(true);
        try {
            const formData = new FormData();
            formData.append('id_image', idImage);
            if (faceMode === 'video') {
                formData.append('selfie_video', selfieVideo);
            } else {
                formData.append('selfie_image', selfieImage);
            }

            const response = await fetch(`${apiBase}/dev/face-match`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'Face match request failed');
            }

            setFaceResult(data);
        } catch (error) {
            setFaceError(error.message);
        } finally {
            setFaceLoading(false);
        }
    };

    return (
        <div className="dev-kyc-page">
            <section className="dev-kyc-hero">
                <div>
                    <p className="dev-kyc-eyebrow">Dev Tools</p>
                    <h1>OCR + Face Verification Lab</h1>
                    <p className="dev-kyc-subtitle">
                        Test OCR, face match, and liveness without signing up.
                    </p>
                    <p className="dev-kyc-subtitle">API: {apiBase}</p>
                </div>
            </section>

            <section className="dev-kyc-grid">
                <div className="dev-kyc-card">
                    <h2>Citizenship OCR</h2>
                    <p className="dev-kyc-muted">Upload a front image and validate the extracted fields.</p>

                    <form onSubmit={handleOcrSubmit} className="dev-kyc-form">
                        <label className="dev-kyc-label">Back Image (English side)</label>
                        <input type="file" accept="image/*" onChange={(e) => setOcrFile(e.target.files[0])} />

                        <label className="dev-kyc-label">Full Name</label>
                        <input
                            type="text"
                            value={ocrForm.fullName}
                            onChange={(e) => setOcrForm({ ...ocrForm, fullName: e.target.value })}
                            placeholder="Ram Bahadur Thapa"
                            required
                        />

                        <label className="dev-kyc-label">Date of Birth</label>
                        <input
                            type="text"
                            value={ocrForm.dob}
                            onChange={(e) => setOcrForm({ ...ocrForm, dob: e.target.value })}
                            placeholder="1990-05-12"
                            required
                        />

                        <label className="dev-kyc-label">Citizenship No</label>
                        <input
                            type="text"
                            value={ocrForm.citizenshipNo}
                            onChange={(e) => setOcrForm({ ...ocrForm, citizenshipNo: e.target.value })}
                            placeholder="12345678"
                            required
                        />

                        <button type="submit" className="dev-kyc-btn" disabled={ocrLoading}>
                            {ocrLoading ? 'Running OCR...' : 'Run OCR'}
                        </button>
                    </form>

                    {ocrError && <p className="dev-kyc-error">{ocrError}</p>}
                    {ocrResult && (
                        <pre className="dev-kyc-output">{JSON.stringify(ocrResult, null, 2)}</pre>
                    )}
                </div>

                <div className="dev-kyc-card">
                    <h2>Face Match + Liveness</h2>
                    <p className="dev-kyc-muted">Compare selfie with ID and run liveness checks.</p>

                    <form onSubmit={handleFaceSubmit} className="dev-kyc-form">
                        <label className="dev-kyc-label">ID Image</label>
                        <input type="file" accept="image/*" onChange={(e) => setIdImage(e.target.files[0])} />

                        <div className="dev-kyc-toggle">
                            <button
                                type="button"
                                className={faceMode === 'capture' ? 'active' : ''}
                                onClick={() => {
                                    setFaceMode('capture');
                                    setSelfieImage(null);
                                    setSelfieVideo(null);
                                    setCapturedImage(null);
                                }}
                            >
                                Capture Photo
                            </button>
                            <button
                                type="button"
                                className={faceMode === 'image' ? 'active' : ''}
                                onClick={() => {
                                    setFaceMode('image');
                                    setCapturedImage(null);
                                    setSelfieImage(null);
                                }}
                            >
                                Upload Image
                            </button>
                            <button
                                type="button"
                                className={faceMode === 'video' ? 'active' : ''}
                                onClick={() => {
                                    setFaceMode('video');
                                    setCapturedImage(null);
                                    setSelfieVideo(null);
                                }}
                            >
                                Upload Video
                            </button>
                        </div>

                        {faceMode === 'capture' ? (
                            <div style={{ marginTop: '1rem' }}>
                                {capturedImage ? (
                                    <div>
                                        <img src={capturedImage} alt="Captured selfie" style={{ width: '100%', maxWidth: '400px', borderRadius: '8px' }} />
                                        <button type="button" onClick={retakePhoto} className="dev-kyc-btn" style={{ marginTop: '0.5rem' }}>
                                            Retake Photo
                                        </button>
                                    </div>
                                ) : (
                                    <div>
                                        <Webcam
                                            audio={false}
                                            ref={webcamRef}
                                            screenshotFormat="image/jpeg"
                                            style={{ width: '100%', maxWidth: '400px', borderRadius: '8px' }}
                                        />
                                        <button type="button" onClick={capturePhoto} className="dev-kyc-btn" style={{ marginTop: '0.5rem' }}>
                                            Capture Photo
                                        </button>
                                    </div>
                                )}
                            </div>
                        ) : faceMode === 'image' ? (
                            <input type="file" accept="image/*" onChange={(e) => setSelfieImage(e.target.files[0])} />
                        ) : (
                            <input type="file" accept="video/*" onChange={(e) => setSelfieVideo(e.target.files[0])} />
                        )}

                        <button type="submit" className="dev-kyc-btn" disabled={faceLoading}>
                            {faceLoading ? 'Checking...' : 'Run Face Match'}
                        </button>
                    </form>

                    {faceError && <p className="dev-kyc-error">{faceError}</p>}
                    {faceResult && (
                        <pre className="dev-kyc-output">{JSON.stringify(faceResult, null, 2)}</pre>
                    )}
                </div>
            </section>
        </div>
    );
};

export default DevKycCheck;
