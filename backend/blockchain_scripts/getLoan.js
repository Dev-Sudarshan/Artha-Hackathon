/**
 * Get Loan Record from Blockchain using ethers.js v6
 * 
 * This script retrieves a loan record from the blockchain smart contract
 * Usage: node getLoan.js <loanId>
 */

const { ethers } = require('ethers');

// Smart Contract ABI - Update this with your actual contract ABI
const CONTRACT_ABI = [
  {
    "inputs": [
      { "internalType": "string", "name": "loanId", "type": "string" }
    ],
    "name": "getLoan",
    "outputs": [
      {
        "components": [
          { "internalType": "string", "name": "loanId", "type": "string" },
          { "internalType": "string", "name": "loanHash", "type": "string" },
          { "internalType": "address", "name": "borrower", "type": "address" },
          { "internalType": "address", "name": "lender", "type": "address" },
          { "internalType": "bool", "name": "isRepaid", "type": "bool" },
          { "internalType": "uint256", "name": "timestamp", "type": "uint256" }
        ],
        "internalType": "struct LoanRegistry.Loan",
        "name": "",
        "type": "tuple"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
];

async function getLoan(loanId) {
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
    
    // Create wallet from private key (not needed for read-only operations, but kept for consistency)
    const wallet = new ethers.Wallet(privateKey, provider);
    
    // Connect to contract
    const contract = new ethers.Contract(contractAddress, CONTRACT_ABI, wallet);
    
    // Call getLoan function (read-only, no gas cost)
    const loan = await contract.getLoan(loanId);
    
    // Parse and return loan data
    const result = {
      success: true,
      loan: {
        loanId: loan.loanId || loan[0],
        loanHash: loan.loanHash || loan[1],
        borrower: loan.borrower || loan[2],
        lender: loan.lender || loan[3],
        isRepaid: loan.isRepaid || loan[4],
        timestamp: loan.timestamp ? loan.timestamp.toString() : (loan[5] ? loan[5].toString() : '0')
      }
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
    error: 'Usage: node getLoan.js <loanId>'
  }));
  process.exit(1);
}

const [loanId] = args;

// Execute
getLoan(loanId);
