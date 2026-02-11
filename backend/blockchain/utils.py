import hashlib
import json

def sha256_hash(payload: dict) -> str:
    """
    Convert dict → canonical JSON → SHA256 hash
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
