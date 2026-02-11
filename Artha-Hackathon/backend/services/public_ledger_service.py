"""
PUBLIC LEDGER SERVICE
---------------------
Read-only access layer for blockchain audit data.

Rules:
- NO writes
- NO authentication
- NO private data
- Hash + metadata ONLY
"""

from multichain_rpc import call_rpc


# =========================
# INTERNAL HELPERS
# =========================

def _list_stream_items(stream_name: str):
    """
    Fetch all items from a MultiChain stream
    """
    response = call_rpc(
        method="liststreamitems",
        params=[stream_name]
    )

    if "error" in response and response["error"]:
        raise Exception(response["error"])

    return response.get("result", [])


def _normalize_item(item: dict) -> dict:
    """
    Normalize raw MultiChain stream item into public-safe format
    """
    return {
        "stream": item.get("stream"),
        "txid": item.get("txid"),
        "blocktime": item.get("blocktime"),
        "confirmations": item.get("confirmations"),
        "data": item.get("data"),   # hash only (already safe)
    }


# =========================
# PUBLIC READ FUNCTIONS
# =========================

def get_public_transactions():
    """
    Public view of transaction receipts
    """
    items = _list_stream_items("transactions")
    return [_normalize_item(i) for i in items]


def get_public_loans():
    """
    Public view of loan requests & agreements
    """
    items = _list_stream_items("loan_requests")
    return [_normalize_item(i) for i in items]


def get_public_repayments():
    """
    Public view of repayment events
    """
    items = _list_stream_items("repayments")
    return [_normalize_item(i) for i in items]


def get_public_kyc():
    """
    Public view of KYC verification hashes
    """
    items = _list_stream_items("kyc_results")
    return [_normalize_item(i) for i in items]


def get_public_identity_proofs():
    """
    Public view of identity proof hashes
    """
    items = _list_stream_items("identity_proofs")
    return [_normalize_item(i) for i in items]
