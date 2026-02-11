from blockchain.utils import sha256_hash
from multichain_rpc import publish_to_stream

KYC_STREAM = "kyc_results"

def record_kyc_result(kyc_payload: dict, user_id: str) -> str:
    """
    Hash KYC result and store hash on blockchain
    """
    kyc_hash = sha256_hash(kyc_payload)

    publish_to_stream(
        stream=KYC_STREAM,
        key=user_id,
        value=kyc_hash
    )

    return kyc_hash
