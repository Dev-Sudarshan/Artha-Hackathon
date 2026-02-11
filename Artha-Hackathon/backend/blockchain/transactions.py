# backend/blockchain/transactions.py

from blockchain.utils import sha256_hash
from multichain_rpc import publish_to_stream

TXN_STREAM = "transactions"
REPAYMENT_STREAM = "repayments"
FEE_STREAM = "fee_allocation"


def record_transaction_receipt(txn_payload: dict, tx_id: str) -> str:
    """
    Hash bank transfer receipt and store on blockchain
    """
    txn_hash = sha256_hash(txn_payload)

    publish_to_stream(
        stream=TXN_STREAM,
        key=tx_id,
        value=txn_hash
    )

    return txn_hash


def record_repayment(repayment_payload: dict, loan_id: str) -> str:
    """
    Hash repayment event (partial/full) and store on blockchain
    """
    repayment_hash = sha256_hash(repayment_payload)

    publish_to_stream(
        stream=REPAYMENT_STREAM,
        key=loan_id,
        value=repayment_hash
    )

    return repayment_hash


def record_fee_allocation(fee_payload: dict, loan_id: str) -> str:
    """
    Hash platform fee & insurance allocation and store on blockchain
    """
    fee_hash = sha256_hash(fee_payload)

    publish_to_stream(
        stream=FEE_STREAM,
        key=loan_id,
        value=fee_hash
    )

    return fee_hash
