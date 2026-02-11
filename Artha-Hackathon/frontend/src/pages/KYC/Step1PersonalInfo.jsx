import '../../styles/Auth.css'; // Reuse form styles

const Step1PersonalInfo = ({ data, updateData, nextStep, user }) => {
    const handleChange = (e) => {
        updateData(e.target.name, e.target.value);
    };

    const handleAddressChange = (type, field, value) => {
        // type: 'permAddress' or 'tempAddress'
        const updatedAddress = { ...data[type], [field]: value };
        updateData(type, updatedAddress);
    };

    const handleSameAddress = (e) => {
        const isChecked = e.target.checked;
        updateData('sameAddress', isChecked);
        if (isChecked) {
            updateData('tempAddress', data.permAddress);
        } else {
            updateData('tempAddress', { province: '', district: '', municipality: '', ward: '' });
        }
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        nextStep();
    };

    // Pre-fill name from auth user if available
    const fullName = user ? user.name : '';

    return (
        <form onSubmit={handleSubmit}>
            <h3 className="form-section-title">Personal Details</h3>

            <div className="form-group">
                <label>Full Name</label>
                <div className="input-wrapper no-icon">
                    <input type="text" value={fullName} disabled className="bg-subtle" />
                </div>
            </div>

            <div className="grid grid-2">
                <div className="form-group">
                    <label>Gender</label>
                    <div className="input-wrapper no-icon">
                        <select name="gender" value={data.gender} onChange={handleChange} required>
                            <option value="">Select Gender</option>
                            <option value="male">Male</option>
                            <option value="female">Female</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                </div>
                <div className="form-group">
                    <label>Profession</label>
                    <div className="input-wrapper no-icon">
                        <select name="profession" value={data.profession} onChange={handleChange} required>
                            <option value="">Select Profession</option>
                            <option value="student">Student</option>
                            <option value="employee">Salaried Employee</option>
                            <option value="business">Business Owner</option>
                            <option value="agriculture">Agriculture</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="form-group">
                <label>Father's Name</label>
                <div className="input-wrapper no-icon">
                    <input type="text" name="fatherName" value={data.fatherName} onChange={handleChange} required />
                </div>
            </div>

            <h3 className="form-section-title">Permanent Address</h3>
            <div className="grid grid-2">
                <div className="form-group">
                    <label>Province</label>
                    <div className="input-wrapper no-icon">
                        <select
                            value={data.permAddress.province}
                            onChange={(e) => handleAddressChange('permAddress', 'province', e.target.value)}
                            required
                        >
                            <option value="">Select Province</option>
                            <option value="koshi">Koshi</option>
                            <option value="madhesh">Madhesh</option>
                            <option value="bagmati">Bagmati</option>
                            <option value="gandaki">Gandaki</option>
                            <option value="lumbini">Lumbini</option>
                            <option value="karnali">Karnali</option>
                            <option value="sudurpashchim">Sudurpashchim</option>
                        </select>
                    </div>
                </div>
                <div className="form-group">
                    <label>District</label>
                    <div className="input-wrapper no-icon">
                        <input type="text" value={data.permAddress.district} onChange={(e) => handleAddressChange('permAddress', 'district', e.target.value)} required />
                    </div>
                </div>
                <div className="form-group">
                    <label>Municipality</label>
                    <div className="input-wrapper no-icon">
                        <input type="text" value={data.permAddress.municipality} onChange={(e) => handleAddressChange('permAddress', 'municipality', e.target.value)} required />
                    </div>
                </div>
                <div className="form-group">
                    <label>Ward No</label>
                    <div className="input-wrapper no-icon">
                        <input type="number" value={data.permAddress.ward} onChange={(e) => handleAddressChange('permAddress', 'ward', e.target.value)} required />
                    </div>
                </div>
            </div>

            <h3 className="form-section-title">Temporary Address</h3>
            <div className="checkbox-group">
                <input type="checkbox" id="sameAddress" checked={data.sameAddress} onChange={handleSameAddress} />
                <label htmlFor="sameAddress">Same as Permanent Address</label>
            </div>

            {!data.sameAddress && (
                <div className="grid grid-2">
                    <div className="form-group">
                        <label>Province</label>
                        <div className="input-wrapper no-icon">
                            <select
                                value={data.tempAddress.province}
                                onChange={(e) => handleAddressChange('tempAddress', 'province', e.target.value)}
                                required
                            >
                                <option value="">Select Province</option>
                                <option value="koshi">Koshi</option>
                                <option value="madhesh">Madhesh</option>
                                <option value="bagmati">Bagmati</option>
                                <option value="gandaki">Gandaki</option>
                                <option value="lumbini">Lumbini</option>
                                <option value="karnali">Karnali</option>
                                <option value="sudurpashchim">Sudurpashchim</option>
                            </select>
                        </div>
                    </div>
                    <div className="form-group">
                        <label>District</label>
                        <div className="input-wrapper no-icon">
                            <input type="text" value={data.tempAddress.district} onChange={(e) => handleAddressChange('tempAddress', 'district', e.target.value)} required />
                        </div>
                    </div>
                    <div className="form-group">
                        <label>Municipality</label>
                        <div className="input-wrapper no-icon">
                            <input type="text" value={data.tempAddress.municipality} onChange={(e) => handleAddressChange('tempAddress', 'municipality', e.target.value)} required />
                        </div>
                    </div>
                    <div className="form-group">
                        <label>Ward No</label>
                        <div className="input-wrapper no-icon">
                            <input type="number" value={data.tempAddress.ward} onChange={(e) => handleAddressChange('tempAddress', 'ward', e.target.value)} required />
                        </div>
                    </div>
                </div>
            )}

            <div className="flex justify-between mt-4">
                <div></div> {/* Spacer */}
                <button type="submit" className="btn btn-primary">Next Step</button>
            </div>
        </form>
    );
};

export default Step1PersonalInfo;
