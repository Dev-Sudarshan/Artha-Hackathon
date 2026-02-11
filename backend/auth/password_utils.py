import hashlib
import os


def hash_password(password: str) -> str:
    """
    Hash password with salt using SHA-256
    """
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )
    return salt.hex() + ":" + pwd_hash.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """
    Verify password against stored hash
    """
    salt_hex, hash_hex = stored_hash.split(":")
    salt = bytes.fromhex(salt_hex)

    pwd_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100_000
    )

    return pwd_hash.hex() == hash_hex