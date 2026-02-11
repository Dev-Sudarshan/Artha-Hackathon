import requests
import json

# Multichain RPC Configuration
RPC_HOST = "172.31.25.55"
RPC_PORT = 6820
RPC_USER = "multichainrpc"
RPC_PASSWORD = "HimPrFVxvxT5zhdoUuCXXZ5y62MpaZsFEemgbHBgKngQ"

URL = f"http://{RPC_HOST}:{RPC_PORT}"
HEADERS = {"content-type": "application/json"}
CHAIN_NAME = "artha-chain"


def call_rpc(method, params=None, rpc_id=1):
    if params is None:
        params = []

    payload = {
        "method": method,
        "params": params,
        "id": rpc_id,
        "chain_name": CHAIN_NAME,
    }

    response = requests.post(
        URL,
        data=json.dumps(payload),
        auth=(RPC_USER, RPC_PASSWORD),
        headers=HEADERS,
        timeout=5 # Prevent hanging
    )

    result = response.json()
    if "error" in result and result["error"]:
        raise Exception(result["error"])

    return result["result"]


# -------- STREAM HELPERS --------

def create_stream(stream_name: str, open_stream: bool = True):
    return call_rpc("create", ["stream", stream_name, open_stream])


def publish_to_stream(stream: str, key: str, value: str):
    """
    Publish hash to stream
    """
    return call_rpc("publish", [stream, key, value])


def get_stream_items(stream: str):
    return call_rpc("liststreamitems", [stream])


def get_stream_key_items(stream: str, key: str):
    """
    Used for audit verification
    """
    return call_rpc("liststreamkeyitems", [stream, key])
