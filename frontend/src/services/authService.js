import api from './api';

const authService = {
    // 1. Register (Step 1: Send OTP)
    register: async (userData) => {
        const response = await api.post('/auth/register', userData);
        return response.data;
    },

    // 2. Verify Registration OTP (Step 2: Get Token)
    verifyOtp: async (phone, otp) => {
        const response = await api.post('/auth/verify-otp', { phone, otp });
        return response.data; // { token }
    },

    // 3. Login (Step 1 or Direct)
    login: async (phone, password) => {
        const response = await api.post('/auth/login', { phone, password });
        return response.data; // { token, user } or error
    },

    // 3b. Me (Live profile)
    me: async (tokenOverride = null) => {
        const headers = tokenOverride
            ? { Authorization: `Bearer ${tokenOverride}` }
            : undefined;
        const response = await api.get('/auth/me', { headers });
        return response.data;
    },

    // 4. Send Login OTP (if needed, e.g., 2FA)
    sendLoginOtp: async (phone) => {
        const response = await api.post('/auth/send-login-otp', { phone });
        return response.data;
    },

    // 5. Logout
    logout: async (token) => {
        try {
            await api.post('/auth/logout', { token });
        } catch (error) {
            console.error("Logout failed", error);
        }
    }
};

export default authService;
