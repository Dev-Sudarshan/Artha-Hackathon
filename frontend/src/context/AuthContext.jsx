import { createContext, useContext, useState, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext({
    user: null,
    loading: true,
    login: async () => {
        throw new Error('AuthProvider is not mounted (login)');
    },
    register: async () => {
        throw new Error('AuthProvider is not mounted (register)');
    },
    verifyOtp: async () => {
        throw new Error('AuthProvider is not mounted (verifyOtp)');
    },
    logout: () => {},
    updateKycStatus: () => {},
    setUserRole: () => {},
    refreshUser: async () => null,
});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Load user from local storage
        const bootstrap = async () => {
            try {
                const storedUser = localStorage.getItem('artha_user');
                if (storedUser) {
                    const parsed = JSON.parse(storedUser);
                    setUser(parsed);

                    // Refresh from backend for live status (KYC, role, totals)
                    if (parsed?.token) {
                        try {
                            const me = await authService.me(parsed.token);
                            const mapped = mapUser(me, parsed.token);
                            setUser(mapped);
                            localStorage.setItem('artha_user', JSON.stringify(mapped));
                        } catch (e) {
                            // If token expired, interceptor will redirect
                            console.warn('Failed to refresh /auth/me', e);
                        }
                    }
                }
            } catch (error) {
                console.error("Failed to parse user from storage", error);
                localStorage.removeItem('artha_user');
            } finally {
                setLoading(false);
            }
        };
        bootstrap();
    }, []);

    // Helper to map Backend User -> Frontend User Shape
    const mapUser = (backendUser, token) => {
        const firstName = backendUser.firstName || backendUser.first_name || '';
        const middleName = backendUser.middleName || backendUser.middle_name || '';
        const lastName = backendUser.lastName || backendUser.last_name || '';

        const kycStatus = backendUser.kycStatus
            ? String(backendUser.kycStatus).toLowerCase() === 'approved'
                ? 'verified'
                : String(backendUser.kycStatus).toLowerCase()
            : backendUser.kycVerified
                ? 'verified'
                : 'incomplete';

        return {
            ...backendUser,
            id: backendUser.phone, // Use phone as ID for now
            firstName,
            middleName,
            lastName,
            name: `${firstName} ${lastName}`.trim(),
            email: backendUser.email || '',
            avatar: `https://ui-avatars.com/api/?name=${encodeURIComponent(firstName)}+${encodeURIComponent(lastName)}&background=0A2540&color=fff`,
            kycStatus,
            activeRole: backendUser.activeRole || 'none',
            bankDetailsAdded: false, // Default
            totalLended: backendUser.totalLended || 0,
            totalBorrowed: backendUser.totalBorrowed || 0,
            token: token // Important: Store token for API interceptor
        };
    };

    const refreshUser = async () => {
        if (!user?.token) return null;
        const me = await authService.me(user.token);
        const mapped = mapUser(me, user.token);
        setUser(mapped);
        localStorage.setItem('artha_user', JSON.stringify(mapped));
        return mapped;
    };

    const login = async (phone, password) => {
        try {
            const data = await authService.login(phone, password);
            // Store token immediately, then refresh from /auth/me for live data
            const mappedUser = mapUser(data.user, data.token);
            setUser(mappedUser);
            localStorage.setItem('artha_user', JSON.stringify(mappedUser));

            try {
                const me = await authService.me(data.token);
                const mappedMe = mapUser(me, data.token);
                setUser(mappedMe);
                localStorage.setItem('artha_user', JSON.stringify(mappedMe));
                return mappedMe;
            } catch {
                return mappedUser;
            }
        } catch (error) {
            console.error("Login failed", error);
            throw error; // Propagate to UI
        }
    };

    const register = async (userData) => {
        // Step 1: Send OTP
        return await authService.register(userData);
    };

    const verifyOtp = async (phone, otp) => {
        const data = await authService.verifyOtp(phone, otp);
        // Immediately hydrate the full user from backend
        const me = await authService.me(data.token);
        const mapped = mapUser(me, data.token);
        setUser(mapped);
        localStorage.setItem('artha_user', JSON.stringify(mapped));
        return mapped;
    };

    const logout = () => {
        // specific logout logic
        try {
            if (user?.token) authService.logout(user.token);
        } catch (e) { /* ignore */ }
        setUser(null);
        localStorage.removeItem('artha_user');
    };

    // Helper to update KYC status locally
    const updateKycStatus = (status) => {
        if (user) {
            const updatedUser = { ...user, kycStatus: status };
            setUser(updatedUser);
            localStorage.setItem('artha_user', JSON.stringify(updatedUser));
        }
    }

    const setUserRole = (role) => {
        if (user) {
            const updatedUser = { ...user, activeRole: role };
            setUser(updatedUser);
            localStorage.setItem('artha_user', JSON.stringify(updatedUser));
        }
    }

    const value = {
        user,
        loading,
        login,
        register,
        verifyOtp,
        logout,
        updateKycStatus,
        setUserRole,
        refreshUser,
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children}
        </AuthContext.Provider>
    );
};
