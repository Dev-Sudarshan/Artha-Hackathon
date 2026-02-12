import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Multichain RPC Configuration
RPC_HOST = os.getenv("MULTICHAIN_HOST", "127.0.0.1")
RPC_PORT = int(os.getenv("MULTICHAIN_PORT", "6836"))
RPC_USER = os.getenv("MULTICHAIN_USER", "multichainrpc")
RPC_PASSWORD = os.getenv("MULTICHAIN_PASSWORD", "Frq1yddQ5p5YTqTAJr5YPmry7PiCNCzP9YLDUarKvSJA")
CHAIN_NAME = os.getenv("MULTICHAIN_CHAIN_NAME", "artha-chain")

URL = f"http://{RPC_HOST}:{RPC_PORT}"
HEADERS = {"content-type": "application/json"}


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
