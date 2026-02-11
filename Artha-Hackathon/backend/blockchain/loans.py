# backend/blockchain/loans.py

from blockchain.utils import sha256_hash
from multichain_rpc import publish_to_stream

LOAN_REQUEST_STREAM = "loan_requests"
LOAN_ACCEPT_STREAM = "loan_acceptance"


def record_loan_request(loan_payload: dict, loan_id: str) -> str:
    """
    Hash loan request / obligation and store on blockchain
    """
    loan_hash = sha256_hash(loan_payload)

    publish_to_stream(
        stream=LOAN_REQUEST_STREAM,
        key=loan_id,
        value=loan_hash
    )

    return loan_hash


def record_loan_acceptance(acceptance_payload: dict, loan_id: str) -> str:
    """
    Hash loan acceptance and store on blockchain
    """
    acceptance_hash = sha256_hash(acceptance_payload)

    publish_to_stream(
        stream=LOAN_ACCEPT_STREAM,
        key=loan_id,
        value=acceptance_hash
    )

    return acceptance_hash
