import { useEffect, useRef, useState } from 'react';
import Webcam from 'react-webcam';
import { RefreshCw, Camera } from 'lucide-react';

const Step3Verification = ({ data, updateData, submit, prevStep }) => {
    const webcamRef = useRef(null);
    const [capturedImage, setCapturedImage] = useState(data.livePhotoUrl || null);

    useEffect(() => {
        return () => {
            if (capturedImage && capturedImage.startsWith('blob:')) {
                URL.revokeObjectURL(capturedImage);
            }
        };
    }, [capturedImage]);

    const capturePhoto = () => {
        if (!webcamRef.current) {
            alert('Camera not ready');
            return;
        }

        const imageSrc = webcamRef.current.getScreenshot();
        if (!imageSrc) {
            alert('Failed to capture image');
            return;
        }

        // Convert base64 to blob
        fetch(imageSrc)
            .then(res => res.blob())
            .then(blob => {
                const file = new File([blob], "selfie.jpg", { type: "image/jpeg" });
                setCapturedImage(imageSrc);
                updateData('livePhoto', file);
                updateData('livePhotoUrl', imageSrc);
            })
            .catch(err => {
                console.error('Error converting image:', err);
                alert('Failed to process captured image');
            });
    };

    const retake = () => {
        if (capturedImage && capturedImage.startsWith('blob:')) {
            URL.revokeObjectURL(capturedImage);
        }
        setCapturedImage(null);
        updateData('livePhoto', null);
        updateData('livePhotoUrl', null);
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!capturedImage) {
            alert("Please capture your photo first");
            return;
        }
        submit();
    };

    return (
        <div className="text-center">
            <h3 className="form-section-title">Live Verification</h3>
            <p className="mb-2 text-muted">Capture a clear photo of your face to verify your identity.</p>
            <p className="mb-4 text-muted">Tips: keep your face centered, avoid backlight, and stay within arm's length.</p>

            <div className="camera-section mb-4">
                {capturedImage ? (
                    <div>
                        <img src={capturedImage} alt="Captured selfie" className="captured-image" />
                        <div className="mt-4">
                            <button type="button" onClick={retake} className="btn btn-outline">
                                <RefreshCw size={18} className="mr-2" style={{ marginRight: '0.5rem' }} /> Retake
                            </button>
                        </div>
                    </div>
                ) : (
                    <div className="webcam-wrapper">
                        <div className="webcam-container">
                            <Webcam
                                audio={false}
                                ref={webcamRef}
                                width="100%"
                                screenshotFormat="image/jpeg"
                            />
                        </div>
                        <div className="mt-4">
                            <button type="button" onClick={capturePhoto} className="btn btn-primary">
                                <Camera size={18} className="mr-2" style={{ marginRight: '0.5rem' }} />
                                Capture Photo
                            </button>
                        </div>
                    </div>
                )}
            </div>

            <div className="flex justify-between mt-8">
                <button type="button" onClick={prevStep} className="btn btn-outline">Back</button>
                <button type="button" onClick={handleSubmit} className="btn btn-primary btn-lg" disabled={!capturedImage}>
                    Submit Verification
                </button>
            </div>
        </div>
    );
};

export default Step3Verification;
