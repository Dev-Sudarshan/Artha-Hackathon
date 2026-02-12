// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title LoanRegistry
 * @dev Smart contract for storing P2P loan records on blockchain
 * 
 * This contract stores loan hashes for audit and verification purposes.
 * The actual loan data is stored off-chain (in database), only hashes
 * are stored on-chain for proof of existence and integrity verification.
 */
contract LoanRegistry {
    
    // Loan structure
    struct Loan {
        string loanId;           // Unique loan identifier
        string loanHash;         // SHA256 hash of loan data
        address borrower;        // Borrower's blockchain address
        address lender;          // Lender's blockchain address
        bool isRepaid;          // Repayment status
        uint256 timestamp;      // Storage timestamp
    }
    
    // Mapping from loan ID to Loan struct
    mapping(string => Loan) public loans;
    
    // Array of all loan IDs for enumeration
    string[] public loanIds;
    
    // Events
    event LoanStored(
        string indexed loanId,
        string loanHash,
        address borrower,
        address lender,
        uint256 timestamp
    );
    
    event LoanRepaid(
        string indexed loanId,
        uint256 timestamp
    );
    
    // Owner address (can be used for access control)
    address public owner;
    
    // Authorized admin addresses
    mapping(address => bool) public admins;
    
    constructor() {
        owner = msg.sender;
        admins[msg.sender] = true;
    }
    
    // Modifiers
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this");
        _;
    }
    
    modifier onlyAdmin() {
        require(admins[msg.sender], "Only admin can call this");
        _;
    }
    
    /**
     * @dev Add or remove admin
     */
    function setAdmin(address admin, bool isAdmin) external onlyOwner {
        admins[admin] = isAdmin;
    }
    
    /**
     * @dev Store loan record on blockchain
     * @param loanId Unique loan identifier
     * @param loanHash SHA256 hash of loan data
     * @param borrower Borrower's blockchain address
     * @param lender Lender's blockchain address (can be zero address if not assigned yet)
     */
    function storeLoan(
        string memory loanId,
        string memory loanHash,
        address borrower,
        address lender
    ) external onlyAdmin {
        require(bytes(loanId).length > 0, "Loan ID cannot be empty");
        require(bytes(loanHash).length > 0, "Loan hash cannot be empty");
        require(bytes(loans[loanId].loanId).length == 0, "Loan already exists");
        
        loans[loanId] = Loan({
            loanId: loanId,
            loanHash: loanHash,
            borrower: borrower,
            lender: lender,
            isRepaid: false,
            timestamp: block.timestamp
        });
        
        loanIds.push(loanId);
        
        emit LoanStored(loanId, loanHash, borrower, lender, block.timestamp);
    }
    
    /**
     * @dev Mark loan as repaid
     * @param loanId Unique loan identifier
     */
    function markRepaid(string memory loanId) external onlyAdmin {
        require(bytes(loans[loanId].loanId).length > 0, "Loan does not exist");
        require(!loans[loanId].isRepaid, "Loan already marked as repaid");
        
        loans[loanId].isRepaid = true;
        
        emit LoanRepaid(loanId, block.timestamp);
    }
    
    /**
     * @dev Get loan record
     * @param loanId Unique loan identifier
     * @return Loan struct
     */
    function getLoan(string memory loanId) external view returns (Loan memory) {
        require(bytes(loans[loanId].loanId).length > 0, "Loan does not exist");
        return loans[loanId];
    }
    
    /**
     * @dev Check if loan exists
     * @param loanId Unique loan identifier
     * @return bool
     */
    function loanExists(string memory loanId) external view returns (bool) {
        return bytes(loans[loanId].loanId).length > 0;
    }
    
    /**
     * @dev Get total number of loans
     * @return uint256
     */
    function getLoanCount() external view returns (uint256) {
        return loanIds.length;
    }
    
    /**
     * @dev Get loan ID by index
     * @param index Array index
     * @return string Loan ID
     */
    function getLoanIdByIndex(uint256 index) external view returns (string memory) {
        require(index < loanIds.length, "Index out of bounds");
        return loanIds[index];
    }
    
    /**
     * @dev Transfer ownership
     * @param newOwner New owner address
     */
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid address");
        owner = newOwner;
        admins[newOwner] = true;
    }
}
