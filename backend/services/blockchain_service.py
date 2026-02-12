"""
Blockchain Service Module for Aartha P2P Lending Platform
Integrates with your EXISTING MultiChain infrastructure for loan proof layer

This service handles:
- Storing loan data hashes on MultiChain streams
- Marking loans as repaid on-chain
- Retrieving loan records from MultiChain
- Verifying data integrity between DB and blockchain
"""

import os
import json
import hashlib
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import logging

# Import your existing MultiChain code
from multichain_rpc import publish_to_stream, get_stream_key_items, create_stream
from blockchain.utils import sha256_hash

logger = logging.getLogger("artha.blockchain")

# MultiChain stream names for loan records
LOAN_STORAGE_STREAM = "loan_storage"
LOAN_REPAYMENT_STREAM = "loan_repayments"


class BlockchainService:
    """
    Service for interacting with MultiChain blockchain using your existing infrastructure
    Uses MultiChain streams instead of smart contracts
    """
    
    def __init__(self):
        # Ensure streams exist
        try:
            create_stream(LOAN_STORAGE_STREAM, open_stream=True)
            logger.info(f"Stream '{LOAN_STORAGE_STREAM}' ready")
        except Exception as e:
            logger.info(f"Stream '{LOAN_STORAGE_STREAM}' already exists or created")
        
        try:
            create_stream(LOAN_REPAYMENT_STREAM, open_stream=True)
            logger.info(f"Stream '{LOAN_REPAYMENT_STREAM}' ready")
        except Exception as e:
            logger.info(f"Stream '{LOAN_REPAYMENT_STREAM}' already exists or created")
    
    def _generate_loan_hash(self, loan_data: Dict) -> str:
        """
        Generate SHA256 hash of loan data for blockchain storage
        Uses your existing hash utility
        
        Args:
            loan_data: Dictionary containing loan details
            
        Returns:
            Hexadecimal hash string
        """
        return sha256_hash(loan_data)
    
    def _publish_to_multichain(self, stream: str, key: str, data: Dict) -> str:
        """
        Publish data to MultiChain stream using your existing RPC
        
        Args:
            stream: Stream name
            key: Key for the item
            data: Data dictionary to publish
            
        Returns:
            Transaction ID (txid) from MultiChain
        """
        try:
            # Convert data to JSON, then hex-encode for MultiChain
            json_data = json.dumps(data, sort_keys=True)
            hex_data = json_data.encode("utf-8").hex()
            
            # Publish using your existing multichain_rpc
            txid = publish_to_stream(stream, key, hex_data)
            
            logger.info(f"Published to MultiChain stream '{stream}' with key '{key}': {txid}")
            return txid
            
        except Exception as e:
            logger.error(f"Failed to publish to MultiChain: {e}")
            raise
    
    def store_loan_on_chain(
        self,
        loan_id: str,
        loan_data: Dict,
        borrower_address: str = None,
        lender_address: str = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Store loan record on MultiChain using your existing streams
        
        Args:
            loan_id: Unique loan identifier
            loan_data: Complete loan data to hash
            borrower_address: Borrower identifier (optional)
            lender_address: Lender identifier (optional)
            
        Returns:
            Tuple of (success, transaction_id, error_message)
        """
        logger.info(f"Storing loan {loan_id} on MultiChain")
        
        try:
            # Generate hash of loan data using your existing utility
            loan_hash = self._generate_loan_hash(loan_data)
            logger.info(f"Generated loan hash: {loan_hash}")
            
            # Prepare data to store on MultiChain
            blockchain_data = {
                "loan_id": loan_id,
                "loan_hash": loan_hash,
                "borrower": borrower_address or loan_data.get("borrower_phone", ""),
                "lender": lender_address or loan_data.get("lender_phone", ""),
                "timestamp": datetime.utcnow().isoformat(),
                "is_repaid": False
            }
            
            # Publish to loan_storage stream using loan_id as key
            tx_hash = self._publish_to_multichain(
                LOAN_STORAGE_STREAM,
                f"loan_{loan_id}",
                blockchain_data
            )
            
            logger.info(f"Loan {loan_id} stored on MultiChain. TX: {tx_hash}")
            return True, tx_hash, None
            
        except Exception as e:
            error_msg = f"Failed to store loan on MultiChain: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def mark_loan_repaid_on_chain(
        self,
        loan_id: str,
        repayment_amount: float,
        borrower_address: str = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Mark loan as fully repaid on MultiChain
        
        Args:
            loan_id: Unique loan identifier
            repayment_amount: Total amount repaid
            borrower_address: Borrower identifier (optional)
            
        Returns:
            Tuple of (success, transaction_id, error_message)
        """
        logger.info(f"Marking loan {loan_id} as repaid on MultiChain")
        
        try:
            repayment_data = {
                "loan_id": loan_id,
                "repayment_amount": repayment_amount,
                "borrower": borrower_address or "",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "FULLY_REPAID"
            }
            
            # Publish to loan_repayments stream
            tx_hash = self._publish_to_multichain(
                LOAN_REPAYMENT_STREAM,
                f"repayment_{loan_id}",
                repayment_data
            )
            
            logger.info(f"Loan {loan_id} marked as repaid on MultiChain. TX: {tx_hash}")
            return True, tx_hash, None
            
        except Exception as e:
            error_msg = f"Failed to mark loan as repaid: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def get_loan_from_chain(self, loan_id: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Retrieve loan record from MultiChain
        
        Args:
            loan_id: Unique loan identifier
            
        Returns:
            Tuple of (success, loan_data, error_message)
        """
        logger.info(f"Retrieving loan {loan_id} from MultiChain")
        
        try:
            # Get items from loan_storage stream with this key
            items = get_stream_key_items(LOAN_STORAGE_STREAM, f"loan_{loan_id}")
            
            if not items:
                return False, None, "Loan not found on blockchain"
            
            # Get the latest item (should be only one)
            latest_item = items[-1] if isinstance(items, list) else items
            
            # Parse the data
            if isinstance(latest_item, dict):
                loan_data = latest_item.get("data", {})
                if isinstance(loan_data, str):
                    # Try hex-decode first, then JSON parse
                    try:
                        loan_data = json.loads(bytes.fromhex(loan_data).decode("utf-8"))
                    except (ValueError, UnicodeDecodeError):
                        loan_data = json.loads(loan_data)
                return True, loan_data, None
            
            return False, None, "Invalid data format"
            
        except Exception as e:
            error_msg = f"Failed to retrieve loan from MultiChain: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def verify_loan_integrity(
        self,
        loan_id: str,
        current_loan_data: Dict
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify that current loan data matches blockchain record
        
        Args:
            loan_id: Unique loan identifier
            current_loan_data: Current loan data from database
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        logger.info(f"Verifying integrity of loan {loan_id}")
        
        try:
            # Get loan from blockchain
            success, chain_data, error = self.get_loan_from_chain(loan_id)
            
            if not success:
                return False, f"Cannot verify: {error}"
            
            # Generate hash of current data
            current_hash = self._generate_loan_hash(current_loan_data)
            
            # Compare with blockchain hash
            chain_hash = chain_data.get("loan_hash", "")
            
            if current_hash == chain_hash:
                logger.info(f"Loan {loan_id} integrity verified ✓")
                return True, None
            else:
                logger.warning(f"Loan {loan_id} integrity check FAILED")
                return False, "Data hash mismatch - loan data may have been tampered with"
                
        except Exception as e:
            error_msg = f"Integrity verification failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg


# Singleton instance
_blockchain_service: Optional[BlockchainService] = None


def get_blockchain_service() -> BlockchainService:
    """
    Get singleton instance of BlockchainService
    """
    global _blockchain_service
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
    return _blockchain_service
