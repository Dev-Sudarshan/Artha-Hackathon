/**
 * Store Loan on Blockchain using ethers.js v6
 * 
 * This script stores a loan record on the blockchain smart contract
 * Usage: node storeLoan.js <loanId> <loanHash> <borrowerAddress> <lenderAddress>
 */

const { ethers } = require('ethers');

// Smart Contract ABI - Update this with your actual contract ABI
const CONTRACT_ABI = [
  {
    "inputs": [
      { "internalType": "string", "name": "loanId", "type": "string" },
      { "internalType": "string", "name": "loanHash", "type": "string" },
      { "internalType": "address", "name": "borrower", "type": "address" },
      { "internalType": "address", "name": "lender", "type": "address" }
    ],
    "name": "storeLoan",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
];

async function storeLoan(loanId, loanHash, borrowerAddress, lenderAddress) {
  try {
    // Read configuration from environment
    const privateKey = process.env.BLOCKCHAIN_PRIVATE_KEY;
    const rpcUrl = process.env.BLOCKCHAIN_RPC_URL;
    const contractAddress = process.env.BLOCKCHAIN_CONTRACT_ADDRESS;

    // Validate configuration
    if (!privateKey || !rpcUrl || !contractAddress) {
      throw new Error('Missing blockchain configuration');
    }

    // Connect to blockchain provider
    const provider = new ethers.JsonRpcProvider(rpcUrl);
    
    // Create wallet from private key
    const wallet = new ethers.Wallet(privateKey, provider);
    
    // Connect to contract
    const contract = new ethers.Contract(contractAddress, CONTRACT_ABI, wallet);
    
    // Call storeLoan function
    const tx = await contract.storeLoan(
      loanId,
      loanHash,
      borrowerAddress,
      lenderAddress
    );
    
    // Wait for transaction confirmation
    const receipt = await tx.wait();
    
    // Return transaction details
    const result = {
      success: true,
      transactionHash: receipt.hash,
      blockNumber: receipt.blockNumber,
      gasUsed: receipt.gasUsed.toString(),
      loanId: loanId,
      loanHash: loanHash
    };
    
    console.log(JSON.stringify(result));
    process.exit(0);
    
  } catch (error) {
    console.error(JSON.stringify({
      success: false,
      error: error.message
    }));
    process.exit(1);
  }
}

// Parse command line arguments
const args = process.argv.slice(2);
if (args.length < 4) {
  console.error(JSON.stringify({
    success: false,
    error: 'Usage: node storeLoan.js <loanId> <loanHash> <borrowerAddress> <lenderAddress>'
  }));
  process.exit(1);
}

const [loanId, loanHash, borrowerAddress, lenderAddress] = args;

// Execute
storeLoan(loanId, loanHash, borrowerAddress, lenderAddress);
