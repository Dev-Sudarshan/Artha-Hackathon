import { Upload } from 'lucide-react';
import '../../styles/Auth.css';

const Step2Documents = ({ data, updateData, nextStep, prevStep }) => {
    const handleChange = (e) => {
        updateData(e.target.name, e.target.value);
    };

    const handleFileChange = (e, side) => {
        const file = e.target.files[0];
        if (file) {
            updateData(side === 'front' ? 'docFront' : 'docBack', file);
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!data.docFront || !data.docBack) {
            alert("Please upload both front and back pages of your document");
            return;
        }
        nextStep();
    };

    const renderUploadBox = (side, label) => {
        const file = side === 'front' ? data.docFront : data.docBack;
        const id = `doc-upload-${side}`;

        return (
            <div className="form-group">
                <label>{label}</label>
                <div className="file-upload-wrapper"
                    style={{
                        border: '2px dashed var(--color-border)',
                        borderRadius: 'var(--radius-md)',
                        padding: '1.5rem',
                        textAlign: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        backgroundColor: 'white'
                    }}>
                    <input
                        type="file"
                        id={id}
                        onChange={(e) => handleFileChange(e, side)}
                        accept="image/*"
                        style={{ display: 'none' }}
                    />
                    <label htmlFor={id} style={{ cursor: 'pointer', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        {file ? (
                            <>
                                <div style={{ color: 'var(--color-success)', marginBottom: '0.5rem' }}>
                                    <strong>File Selected:</strong>
                                    <p style={{ fontSize: '0.85rem', margin: '0.25rem 0' }}>{file.name}</p>
                                </div>
                                <span className="btn btn-outline btn-sm">Change File</span>
                            </>
                        ) : (
                            <>
                                <Upload size={28} className="text-muted mb-2" />
                                <p style={{ fontSize: '0.9rem', fontWeight: '500' }}>Click to upload {label}</p>
                                <p className="text-muted" style={{ fontSize: '0.75rem' }}>JPG, PNG up to 5MB</p>
                            </>
                        )}
                    </label>
                </div>
            </div>
        );
    };

    return (
        <form onSubmit={handleSubmit}>
            <h3 className="form-section-title">Identity Verification</h3>

            <div className="form-group">
                <label>Document Type</label>
                <div className="input-wrapper no-icon">
                    <select name="docType" value={data.docType} onChange={handleChange} required>
                        <option value="citizenship">Citizenship</option>
                        <option value="nid">National ID (NID)</option>
                        <option value="passport">Passport</option>
                    </select>
                </div>
            </div>

            <div className="grid grid-2">
                <div className="form-group">
                    <label>ID Number</label>
                    <div className="input-wrapper no-icon">
                        <input type="text" name="docNumber" value={data.docNumber} onChange={handleChange} required placeholder="xx-xx-xx-xxxxx" />
                    </div>
                </div>
                <div className="form-group">
                    <label>Issue Date</label>
                    <div className="input-wrapper no-icon">
                        <input type="date" name="issueDate" value={data.issueDate} onChange={handleChange} required />
                    </div>
                </div>
            </div>

            <div className="grid grid-2">
                {renderUploadBox('front', 'Front Page')}
                {renderUploadBox('back', 'Back Page')}
            </div>

            <div className="flex justify-between mt-8">
                <button type="button" onClick={prevStep} className="btn btn-outline">Back</button>
                <button type="submit" className="btn btn-primary">Next Step</button>
            </div>
        </form>
    );
};

export default Step2Documents;
