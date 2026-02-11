from blockchain.utils import sha256_hash
from multichain_rpc import get_stream_key_items

from db.database import get_item, get_repayments

# ---- STORES REPLACED BY DB ----


def _get_blockchain_hash(stream: str, key: str):
    """
    Fetch latest hash value for a key from a stream
    """
    items = get_stream_key_items(stream, key)
    if not items:
        return None
    return items[-1]["data"]


# -------- KYC AUDIT --------

def verify_kyc(user_id: str):
    # Fetch relevant part of KYC data for hashing
    full_kyc = get_item("kyc", user_id)
    if not full_kyc or "final_result" not in full_kyc:
        raise Exception("KYC data not found")
        
    db_data = full_kyc["final_result"]

    db_hash = sha256_hash(db_data)
    chain_hash = _get_blockchain_hash("kyc_results", user_id)

    return {
        "db_hash": db_hash,
        "blockchain_hash": chain_hash,
        "match": db_hash == chain_hash,
    }


def verify_identity(user_id: str):
    # Identity proof is mostly on chain, but if we stored it in DB it would be here
    # For now, assuming it's part of KYC or separate. 
    # Current implementation implies IDENTITY_STORE distinct from KYC. 
    # Let's assume it should be in `kyc` table or skip if not implemented in kyc_service.
    # Actually kyc_service.py writes to blockchain but doesn't explicitly store "identity proof" separate from "final_kyc_result" except in local var.
    # For compatibility, we'll try to reconstruct or use kyc data.
    # Or raises not found.
    raise Exception("Identity data store not implemented in DB")

    db_hash = sha256_hash(db_data)
    chain_hash = _get_blockchain_hash("identity_proofs", user_id)

    return {
        "db_hash": db_hash,
        "blockchain_hash": chain_hash,
        "match": db_hash == chain_hash,
    }


# -------- LOAN AUDIT --------

def verify_loan_request(loan_id: str):
    db_data = get_item("loans", loan_id)
    if not db_data:
        raise Exception("Loan request not found")

    db_hash = sha256_hash(db_data)
    chain_hash = _get_blockchain_hash("loan_requests", loan_id)

    return {
        "db_hash": db_hash,
        "blockchain_hash": chain_hash,
        "match": db_hash == chain_hash,
    }


def verify_loan_acceptance(loan_id: str):
    db_data = get_item("loan_acceptances", loan_id)
    if not db_data:
        raise Exception("Loan acceptance not found")

    db_hash = sha256_hash(db_data)
    chain_hash = _get_blockchain_hash("loan_acceptance", loan_id)

    return {
        "db_hash": db_hash,
        "blockchain_hash": chain_hash,
        "match": db_hash == chain_hash,
    }


# -------- TRANSACTION & REPAYMENT AUDIT --------

def verify_transaction(loan_id: str):
    # Note: caller seems to pass tx_id in original code, but we stored by loan_id in transaction_service.
    # We should align. transaction_service uses loan_id as key.
    db_data = get_item("transactions", loan_id)
    if not db_data:
        raise Exception("Transaction not found")

    db_hash = sha256_hash(db_data)
    chain_hash = _get_blockchain_hash("transactions", tx_id)

    return {
        "db_hash": db_hash,
        "blockchain_hash": chain_hash,
        "match": db_hash == chain_hash,
    }


def verify_repayments(loan_id: str):
    repayments = get_repayments(loan_id)
    if not repayments:
        raise Exception("No repayments found")

    results = []
    for r in repayments:
        db_hash = sha256_hash(r)
        chain_hash = _get_blockchain_hash("repayments", loan_id)

        results.append(
            {
                "repayment_id": r.get("repayment_id"),
                "db_hash": db_hash,
                "blockchain_hash": chain_hash,
                "match": db_hash == chain_hash,
            }
        )

    return results


# -------- AGREEMENT EXECUTION (VIDEO + THUMB + SIGNATURE) AUDIT --------

def verify_agreement_execution(loan_id: str):
    """
    Verify signed agreement execution:
    - signed PDF
    - video verification
    - thumb verification
    """

    db_data = get_item("agreement_executions", loan_id)
    if not db_data:
        raise Exception("Agreement execution data not found")

    db_hash = sha256_hash(db_data)
    chain_hash = _get_blockchain_hash("loan_agreements", loan_id)

    return {
        "loan_id": loan_id,
        "db_hash": db_hash,
        "blockchain_hash": chain_hash,
        "match": db_hash == chain_hash,
    }
