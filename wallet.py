"""
SimpleBlockchain Wallet & Cryptography Module (Lecture 04)
Module: BLCH9X2 - Master of Financial Engineering (University of Johannesburg)
Author: Olonda Thoba Holizwi Masuku
"""

import hashlib
import json
from typing import Tuple, Dict, Any, Union
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError


class Wallet:
    """
    Encapsulates an ECDSA key pair (SECP256k1 curve) and provides helper methods
    for key derivation, payload signing, and address management.
    """

    def __init__(self, signing_key: SigningKey = None):
        """
        Initialize a Wallet instance. If no signing key is provided, generates a fresh throwaway key.
        """
        self._sk = signing_key if signing_key else SigningKey.generate(curve=SECP256k1)
        self._vk = self._sk.get_verifying_key()

    @classmethod
    def create(cls) -> 'Wallet':
        """Factory method to instantiate a new Wallet with fresh throwaway keys."""
        return cls()

    @property
    def private_key_hex(self) -> str:
        """Returns the private key as a 64-character hex string (FOR DEMO/TESTING ONLY)."""
        return self._sk.to_string().hex()

    @property
    def public_key_hex(self) -> str:
        """Returns the uncompressed verifying (public) key as a hex string."""
        return self._vk.to_string().hex()

    @property
    def address(self) -> str:
        """
        Derives a simplified pedagogical address from the public key bytes.
        Recipe: SHA-256(pubkey_bytes) truncated to the first 40 hex characters.
        """
        pubkey_bytes = self._vk.to_string()
        return hashlib.sha256(pubkey_bytes).hexdigest()[:40]

    def sign(self, message_bytes: bytes) -> str:
        """
        Signs a raw byte payload using ECDSA with SECP256k1.
        Returns the resulting signature as a hex-encoded string.
        """
        signature_bytes = self._sk.sign(message_bytes)
        return signature_bytes.hex()

    @staticmethod
    def verify(message_bytes: bytes, signature_hex: str, public_key_hex: str) -> bool:
        """
        Static verification method checking whether a signature matches a message digest
        under a given public key hex string.
        """
        try:
            signature_bytes = bytes.fromhex(signature_hex)
            pubkey_bytes = bytes.fromhex(public_key_hex)
            vk = VerifyingKey.from_string(pubkey_bytes, curve=SECP256k1)
            return vk.verify(signature_bytes, message_bytes)
        except (BadSignatureError, ValueError):
            return False


def canonical_tx_payload(sender: str, recipient: str, amount: Union[int, float], timestamp: Union[int, float]) -> bytes:
    """
    Constructs a deterministic canonical byte payload for signing/verifying.
    Excludes the signature field to prevent circular signing references.
    
    Rules:
    - Dict key sorting (sort_keys=True)
    - Tight separators (no whitespace: separators=(',', ':'))
    - UTF-8 byte encoding
    """
    body = {
        "amount": amount,
        "recipient": recipient,
        "sender": sender,
        "timestamp": timestamp,
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def pubkey_to_address(public_key_hex: str) -> str:
    """Helper function to derive address directly from a public key hex string."""
    pubkey_bytes = bytes.fromhex(public_key_hex)
    return hashlib.sha256(pubkey_bytes).hexdigest()[:40]