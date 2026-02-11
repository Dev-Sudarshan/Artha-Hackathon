from blockchain.utils import sha256_hash
from multichain_rpc import publish_to_stream

LOAN_STATUS_STREAM = "loan_status"

def record_loan_status(status_payload: dict, loan_id: str) -> str:
    """
    Hash loan status change and store on blockchain
    status: active | repaid | defaulted
    """
    status_hash = sha256_hash(status_payload)

    publish_to_stream(
        stream=LOAN_STATUS_STREAM,
        key=loan_id,
        value=status_hash
    )

    return status_hash
