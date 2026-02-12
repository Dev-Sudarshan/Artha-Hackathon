# Blockchain Scripts for Aartha Platform

This directory contains Node.js scripts that interact with the blockchain smart contract using ethers.js v6.

## Prerequisites

Install dependencies:
```bash
cd blockchain_scripts
npm install
```

## Scripts

### 1. storeLoan.js
Stores a loan record on the blockchain.

**Usage:**
```bash
node storeLoan.js <loanId> <loanHash> <borrowerAddress> <lenderAddress>
```

### 2. markRepaid.js
Marks a loan as repaid on the blockchain.

**Usage:**
```bash
node markRepaid.js <loanId>
```

### 3. getLoan.js
Retrieves a loan record from the blockchain.

**Usage:**
```bash
node getLoan.js <loanId>
```

## Configuration

These scripts read configuration from environment variables:
- `BLOCKCHAIN_PRIVATE_KEY`: Private key for signing transactions
- `BLOCKCHAIN_RPC_URL`: RPC URL for blockchain connection
- `BLOCKCHAIN_CONTRACT_ADDRESS`: Deployed smart contract address

## Smart Contract ABI

Update the `CONTRACT_ABI` constant in each script to match your deployed smart contract's ABI.

## Output Format

All scripts output JSON to stdout:

**Success:**
```json
{
  "success": true,
  "transactionHash": "0x...",
  "blockNumber": 12345,
  "gasUsed": "21000"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Error message"
}
```

## Security

⚠️ **IMPORTANT**: Never commit `.env` files or expose private keys! These scripts are called from the Python backend which securely manages credentials.
