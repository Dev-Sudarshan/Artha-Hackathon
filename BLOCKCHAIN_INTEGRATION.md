# Blockchain Integration for Aartha P2P Lending Platform

This document explains the blockchain proof layer integration added to the Aartha platform.

## Overview

The blockchain integration provides an immutable audit trail for loan records, ensuring data integrity and transparency. Loan data is hashed and stored on-chain, allowing verification that records haven't been tampered with.

## Architecture

### Backend Components

1. **Blockchain Service** (`backend/services/blockchain_service.py`)
   - Core service for blockchain interactions
   - Functions:
     - `store_loan_on_chain()`: Store loan hash on blockchain
     - `mark_loan_repaid_on_chain()`: Mark loan as repaid
     - `get_loan_from_chain()`: Retrieve loan from blockchain
     - `verify_loan_integrity()`: Compare DB hash with blockchain hash

2. **Node.js Scripts** (`backend/blockchain_scripts/`)
   - `storeLoan.js`: Stores loan record using ethers.js v6
   - `markRepaid.js`: Marks loan as repaid
   - `getLoan.js`: Retrieves loan from smart contract
   - Uses subprocess to execute from Python

3. **Admin API Endpoints** (`backend/admin/admin_routes.py`)
   - `POST /admin/loans/{loan_id}/blockchain/store`: Store loan on-chain
   - `POST /admin/loans/{loan_id}/blockchain/mark-repaid`: Mark repaid
   - `GET /admin/loans/{loan_id}/blockchain/verify`: Verify integrity
   - `GET /admin/loans/{loan_id}/blockchain/status`: Get status

4. **Database Models** (`backend/admin/admin_models.py`)
   - Added columns to `Loan` table:
     - `blockchain_tx_hash`: Transaction hash
     - `blockchain_status`: NOT_STORED, STORED, REPAID_ON_CHAIN
     - `blockchain_loan_hash`: SHA256 hash of loan data
     - `blockchain_stored_at`: Storage timestamp
     - `blockchain_repaid_tx_hash`: Repayment transaction hash

### Frontend Components

1. **Admin Panel Updates** (`admin-frontend/src/pages/Loans/Loans.jsx`)
   - Display blockchain status badges
   - Show transaction hashes with explorer links
   - Buttons:
     - "Store on Chain": Store after approval
     - "Verify": Check data integrity
     - "Mark Repaid": Update repayment status

2. **API Service** (`admin-frontend/src/services/adminApi.js`)
   - Added blockchain API functions
   - Handles all blockchain-related requests

3. **Styling** (`admin-frontend/src/pages/Loans/Loans.css`)
   - Blockchain status indicators
   - Verification result displays
   - Transaction hash formatting

## Setup Instructions

### 1. Install Dependencies

#### Backend (Python)
No additional Python packages needed - uses existing dependencies.

#### Blockchain Scripts (Node.js)
```bash
cd backend/blockchain_scripts
npm install
```

This installs ethers.js v6.

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and set:

```env
# Blockchain Configuration
BLOCKCHAIN_PRIVATE_KEY=0x1234567890abcdef...  # Your private key
BLOCKCHAIN_RPC_URL=http://172.31.25.55:6820   # MultiChain RPC
BLOCKCHAIN_CONTRACT_ADDRESS=0x1234...          # Contract address
```

⚠️ **SECURITY**: Never commit `.env` files or expose private keys!

### 3. Update Smart Contract ABI

Edit the `CONTRACT_ABI` constant in each blockchain script with your actual contract ABI:
- `backend/blockchain_scripts/storeLoan.js`
- `backend/blockchain_scripts/markRepaid.js`
- `backend/blockchain_scripts/getLoan.js`

### 4. Database Migration

Add new columns to the `loans` table:

```sql
ALTER TABLE loans 
ADD COLUMN blockchain_tx_hash VARCHAR(255),
ADD COLUMN blockchain_status VARCHAR(50) DEFAULT 'NOT_STORED',
ADD COLUMN blockchain_loan_hash VARCHAR(255),
ADD COLUMN blockchain_stored_at TIMESTAMP,
ADD COLUMN blockchain_repaid_tx_hash VARCHAR(255);
```

Or use the provided migration script:
```bash
cd backend
python migrate_blockchain_fields.py
```

### 5. Test the Integration

1. Start the backend:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Start the admin frontend:
   ```bash
   cd admin-frontend
   npm run dev
   ```

3. Test workflow:
   - Approve a loan
   - Click "Store on Chain"
   - Verify the transaction on blockchain explorer
   - Click "Verify" to check integrity
   - Mark as repaid when appropriate

## Usage Guide

### Admin Panel Workflow

1. **Approve Loan**
   - Admin reviews pending loan
   - Clicks "Approve" button
   - Loan status changes to "LISTED"

2. **Store on Blockchain**
   - After approval, "Store on Chain" button appears
   - Clicking generates SHA256 hash of loan data
   - Stores hash on smart contract
   - Transaction hash saved to database
   - Status badge shows "STORED"

3. **Verify Integrity**
   - Click "Verify" button anytime
   - Compares database hash with blockchain hash
   - Shows ✅ Verified or ❌ Tampered

4. **Mark Repaid**
   - When loan is repaid, click "Mark Repaid"
   - Updates smart contract
   - Status changes to "REPAID_ON_CHAIN"

### API Examples

#### Store Loan on Blockchain
```bash
curl -X POST http://localhost:8000/api/admin/loans/{loan_id}/blockchain/store \
  -H "Authorization: Bearer <admin_token>"
```

#### Verify Loan Integrity
```bash
curl -X GET http://localhost:8000/api/admin/loans/{loan_id}/blockchain/verify \
  -H "Authorization: Bearer <admin_token>"
```

#### Mark Loan as Repaid
```bash
curl -X POST http://localhost:8000/api/admin/loans/{loan_id}/blockchain/mark-repaid \
  -H "Authorization: Bearer <admin_token>"
```

## Smart Contract Requirements

Your smart contract should implement these functions:

```solidity
// Store loan record
function storeLoan(
    string memory loanId,
    string memory loanHash,
    address borrower,
    address lender
) external;

// Mark loan as repaid
function markRepaid(string memory loanId) external;

// Retrieve loan record
function getLoan(string memory loanId) external view returns (
    Loan memory
);

// Loan struct
struct Loan {
    string loanId;
    string loanHash;
    address borrower;
    address lender;
    bool isRepaid;
    uint256 timestamp;
}
```

## Data Integrity

### Hash Generation
Loans are hashed using SHA256 before storage:
```python
loan_data = {
    "loan_id": "...",
    "borrower_phone": "...",
    "lender_phone": "...",
    "amount": 100000,
    "interest_rate": 12.5,
    "status": "LISTED",
    "issued_at": "2025-01-01",
    "due_date": "2025-12-31"
}
hash = sha256(json.dumps(loan_data, sort_keys=True))
```

### Verification Process
1. Generate hash of current loan data
2. Retrieve hash from blockchain
3. Compare both hashes
4. Match = ✅ Verified
5. Mismatch = ❌ Tampered (data was modified)

## Security Considerations

1. **Private Key Protection**
   - Never expose private keys in code or logs
   - Store in environment variables only
   - Use separate keys for dev/prod
   - Consider using hardware wallets for production

2. **Access Control**
   - Only admins can store/update blockchain records
   - Role-based permissions enforced
   - All actions logged with admin identity

3. **Input Validation**
   - All inputs sanitized before blockchain calls
   - Loan IDs validated
   - Amounts and addresses checked

4. **Error Handling**
   - Blockchain failures don't crash application
   - Transactions retried on network issues
   - Clear error messages for admins

## Troubleshooting

### "Blockchain configuration missing"
- Check `.env` file has all three variables set
- Ensure no extra spaces in variable values
- Verify RPC URL is accessible

### "Failed to execute blockchain script"
- Check Node.js is installed: `node --version`
- Verify ethers.js is installed: `cd blockchain_scripts && npm list`
- Check script permissions
- Review logs for detailed errors

### "Transaction failed"
- Verify sufficient gas/balance in account
- Check RPC connection is working
- Ensure contract address is correct
- Verify ABI matches deployed contract

### Verification shows "Tampered"
- Check if loan data was modified after storage
- Ensure hash uses same fields as storage
- Review loan modification history
- May indicate security issue - investigate immediately

## Optional: Auto-Store on Approval

To automatically store loans on blockchain when approved, uncomment the code block in `admin_routes.py` in the `approve_loan()` function (around line 502).

This will:
- Store loan on blockchain immediately after approval
- Skip manual "Store on Chain" step
- Provide seamless workflow

## Monitoring & Maintenance

1. **Transaction Logs**
   - Check backend logs for blockchain operations
   - Monitor gas usage
   - Track success/failure rates

2. **Database Consistency**
   - Periodically verify all stored loans
   - Check for missing transaction hashes
   - Ensure status fields are accurate

3. **Blockchain Explorer**
   - Monitor transactions on chain
   - Verify block confirmations
   - Check contract state

## Future Enhancements

Potential improvements:
- Bulk verification of multiple loans
- Automated periodic verification
- Dashboard showing blockchain statistics
- Email notifications for blockchain events
- Support for multiple blockchain networks
- Integration with oracle for off-chain data

## Support

For issues or questions:
1. Check logs in `backend/logs/`
2. Review this documentation
3. Contact development team
4. Report bugs via issue tracker

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Maintained By**: Aartha Development Team
