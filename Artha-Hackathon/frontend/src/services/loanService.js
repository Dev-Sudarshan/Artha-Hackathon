import api from './api';

const loanService = {
    // Helper to upload file
    upload: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        const response = await api.post('/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data.url;
    },

    // 1. Get Marketplace Listings
    getMarketplaceListings: async () => {
        const response = await api.get('/loans/marketplace');
        return response.data;
    },

    // 2. Create Borrow Request
    createBorrowRequest: async (loanId = null, loanData, guarantorData, guarantorFiles, legalFiles) => {
        // Upload images first
        let frontUrl = null;
        let backUrl = null;
        if (guarantorFiles.front) frontUrl = await loanService.upload(guarantorFiles.front);
        if (guarantorFiles.back) backUrl = await loanService.upload(guarantorFiles.back);

        let signedUrl = null;
        let videoUrl = null;
        if (legalFiles.signedDoc) signedUrl = await loanService.upload(legalFiles.signedDoc);
        if (legalFiles.videoStatement) videoUrl = await loanService.upload(legalFiles.videoStatement);

        const payload = {
            user_id: "", // filled by backend from token
            loan_id: loanId,
            amount: parseInt(loanData.amount),
            interest_rate: 13.0,
            tenure_months: parseInt(loanData.tenure),
            purpose: loanData.purpose,
            emi_amount: 0,
            guarantor: {
                full_name: guarantorData.name,
                relation: guarantorData.relation,
                card_images: {
                    front_image_ref: frontUrl || "",
                    back_image_ref: backUrl || ""
                },
                citizenship_no: guarantorData.citizenshipNo
            },
            agreement_pdf_signed: signedUrl,
            video_verification_ref: videoUrl,
            agreed_to_rules: true,
            platform_fee_percent: 3.0,
            net_amount_received: loanData.amount * 0.97,
            submitted_at: Math.floor(Date.now() / 1000)
        };

        const response = await api.post('/loans/borrow', payload);
        return response.data;
    },

    // 3. Fund a Loan (Lender)
    fundLoan: async (loanId, amount) => {
        const payload = {
            loan_id: loanId,
            amount: parseFloat(amount),
            transaction_id: `TXN-${Math.floor(Date.now())}`,
            sender_account: "WALLET-MOCK",
            receiver_account: "ESCROW-POOL",
            timestamp: Math.floor(Date.now() / 1000),
            success: true
        };
        const response = await api.post('/transactions/fund-transfer', payload);
        return response.data;
    },

    // 4. Repay Loan
    repayLoan: async (loanId, amount) => {
        const payload = {
            loan_id: loanId,
            amount: parseFloat(amount),
            paid_by: "OVERRIDE_BY_BACKEND",
            repayment_type: "PARTIAL",
            repayment_id: "GENERATE_ME",
            timestamp: Math.floor(Date.now() / 1000)
        };
        const response = await api.post('/repayments/', payload);
        return response.data;
    },

    // 5. Get User Portfolio
    getUserPortfolio: async () => {
        const response = await api.get('/loans/my-portfolio');
        return response.data;
    }
};

export default loanService;
