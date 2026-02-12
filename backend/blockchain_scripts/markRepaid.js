/**
 * Mark Loan as Repaid on Blockchain using ethers.js v6
 * 
 * This script marks a loan as repaid on the blockchain smart contract
 * Usage: node markRepaid.js <loanId>
 */

const { ethers } = require('ethers');

// Smart Contract ABI - Update this with your actual contract ABI
const CONTRACT_ABI = [
  {
    "inputs": [
      { "internalType": "string", "name": "loanId", "type": "string" }
    ],
    "name": "markRepaid",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
];

async function markRepaid(loanId) {
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
    
    // Call markRepaid function
    const tx = await contract.markRepaid(loanId);
    
    // Wait for transaction confirmation
    const receipt = await tx.wait();
    
    // Return transaction details
    const result = {
      success: true,
      transactionHash: receipt.hash,
      blockNumber: receipt.blockNumber,
      gasUsed: receipt.gasUsed.toString(),
      loanId: loanId,
      status: 'REPAID'
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
if (args.length < 1) {
  console.error(JSON.stringify({
    success: false,
    error: 'Usage: node markRepaid.js <loanId>'
  }));
  process.exit(1);
}

const [loanId] = args;

// Execute
markRepaid(loanId);
