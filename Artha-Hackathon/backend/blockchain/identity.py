from blockchain.utils import sha256_hash
from multichain_rpc import publish_to_stream

IDENTITY_STREAM = "identity_proofs"

def record_identity_proof(identity_payload: dict, user_id: str) -> str:
    """
    Hash government ID / live photo / location verification result
    and store proof on blockchain
    """
    identity_hash = sha256_hash(identity_payload)

    publish_to_stream(
        stream=IDENTITY_STREAM,
        key=user_id,
        value=identity_hash
    )

    return identity_hash
