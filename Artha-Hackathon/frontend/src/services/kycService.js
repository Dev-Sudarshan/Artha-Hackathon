import api from './api';

const kycService = {
    // Helper to upload file
    upload: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data.url; // Returns path string
    },

    // Page 1: Basic Info
    submitBasicInfo: async (data, userId) => {
        const payload = { ...data, user_id: userId, submitted_at: Math.floor(Date.now() / 1000) };
        const response = await api.post('/kyc/basic-info', payload);
        return response.data;
    },

    // Page 2: Documents
    submitIdDocuments: async (userId, idType, idNumber, issueDate, frontFile, backFile) => {
        // 1. Upload images first
        const frontUrl = await kycService.upload(frontFile);
        const backUrl = await kycService.upload(backFile);

        // 2. Submit JSON payload
        const payload = {
            user_id: userId,
            id_details: {
                id_type: idType,
                id_number: idNumber,
                issue_date: issueDate
            },
            id_images: {
                front_image_ref: frontUrl,
                back_image_ref: backUrl
            },
            submitted_at: Math.floor(Date.now() / 1000)
        };

        const response = await api.post('/kyc/id-documents', payload);
        return response.data;
    },

    // Page 3: Selfie (image)
    submitSelfie: async (userId, imageFile, text, language = 'ne') => {
        const imageUrl = await kycService.upload(imageFile);

        const payload = {
            user_id: userId,
            declaration_video: {
                selfie_image_ref: imageUrl,
                language: language,
                declared_text: text
            },
            submitted_at: Math.floor(Date.now() / 1000)
        };

        const response = await api.post('/kyc/declaration-video', payload);
        return response.data;
    },

    // Page 3: Video
    submitVideo: async (userId, videoFile, text, language = 'ne') => {
        const videoUrl = await kycService.upload(videoFile);

        const payload = {
            user_id: userId,
            declaration_video: {
                video_ref: videoUrl,
                language: language,
                declared_text: text
            },
            submitted_at: Math.floor(Date.now() / 1000)
        };

        const response = await api.post('/kyc/declaration-video', payload);
        return response.data;
    }
};

export default kycService;
