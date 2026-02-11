import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

const adminApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
adminApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('adminToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Auth
export const adminLogin = async (email, password) => {
  const response = await adminApi.post('/admin/auth/login', { email, password });
  return response.data;
};

// Dashboard
export const getDashboard = async () => {
  const response = await adminApi.get('/admin/dashboard');
  return response.data;
};

// Borrowers
export const getBorrowers = async (params = {}) => {
  const response = await adminApi.get('/admin/borrowers', { params });
  return response.data;
};

export const updateBorrower = async (id, data) => {
  const response = await adminApi.patch(`/admin/borrowers/${id}`, data);
  return response.data;
};

// Lenders
export const getLenders = async (params = {}) => {
  const response = await adminApi.get('/admin/lenders', { params });
  return response.data;
};

export const updateLender = async (id, data) => {
  const response = await adminApi.patch(`/admin/lenders/${id}`, data);
  return response.data;
};

// Loans
export const getLoans = async (params = {}) => {
  const response = await adminApi.get('/admin/loans', { params });
  return response.data;
};

export const approveLoan = async (loanId, reason = null) => {
  const response = await adminApi.post(`/admin/loans/${encodeURIComponent(loanId)}/approve`, { reason });
  return response.data;
};

export const rejectLoan = async (loanId, reason = null) => {
  const response = await adminApi.post(`/admin/loans/${encodeURIComponent(loanId)}/reject`, { reason });
  return response.data;
};

// KYC
export const getKycRecords = async (params = {}) => {
  const response = await adminApi.get('/admin/kyc', { params });
  return response.data;
};

export const getKycRecord = async (userPhone) => {
  const response = await adminApi.get(`/admin/kyc/${encodeURIComponent(userPhone)}`);
  return response.data;
};

export const approveKyc = async (userPhone, reason = null) => {
  const response = await adminApi.post(`/admin/kyc/${encodeURIComponent(userPhone)}/approve`, { reason });
  return response.data;
};

export const rejectKyc = async (userPhone, reason = null) => {
  const response = await adminApi.post(`/admin/kyc/${encodeURIComponent(userPhone)}/reject`, { reason });
  return response.data;
};

// Transactions
export const getTransactions = async (params = {}) => {
  const response = await adminApi.get('/admin/transactions', { params });
  return response.data;
};

export default adminApi;
