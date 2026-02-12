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

    try:
        response = requests.post(
            URL,
            data=json.dumps(payload),
            auth=(RPC_USER, RPC_PASSWORD),
            headers=HEADERS,
            timeout=5 # Prevent hanging
        )
    except requests.exceptions.ConnectionError:
        print(f"[MultiChain] WARNING: Cannot connect to MultiChain at {URL}. Is it running?")
        return None
    except requests.exceptions.Timeout:
        print(f"[MultiChain] WARNING: Connection to MultiChain timed out.")
        return None
    except Exception as e:
        print(f"[MultiChain] WARNING: RPC call failed: {e}")
        return None

    result = response.json()
    if "error" in result and result["error"]:
        raise Exception(result["error"])

    return result["result"]


# -------- STREAM HELPERS --------

def create_stream(stream_name: str, open_stream: bool = True):
    result = call_rpc("create", ["stream", stream_name, open_stream])
    if result is None:
        print(f"[MultiChain] WARNING: Could not create stream '{stream_name}' - MultiChain not available")
    return result


def publish_to_stream(stream: str, key: str, value: str):
    """
    Publish hash to stream
    """
    result = call_rpc("publish", [stream, key, value])
    if result is None:
        raise Exception(f"MultiChain is not available. Cannot publish to stream '{stream}'.")
    return result


def get_stream_items(stream: str):
    result = call_rpc("liststreamitems", [stream])
    return result if result is not None else []


def get_stream_key_items(stream: str, key: str):
    """
    Used for audit verification
    """
    result = call_rpc("liststreamkeyitems", [stream, key])
    return result if result is not None else []
