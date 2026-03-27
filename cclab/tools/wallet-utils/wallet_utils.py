"""
Blockchain Wallet Utilities
=============================
Chain Clarity Lab — @chainclar
Author: Elias Kfoury

Tools for:
- Generating Ethereum wallets
- Checking wallet balance (via RPC)
- Encoding/decoding transactions
- Address validation
- USDT balance checker
"""

import hashlib
import hmac
import struct
import os
import json
from typing import Optional, Dict


# ── Address Utilities ─────────────────────────────────────────────────
def keccak256(data: bytes) -> bytes:
    """Simplified keccak256 using sha3_256 (educational only)"""
    return hashlib.sha3_256(data).digest()


def is_valid_eth_address(address: str) -> bool:
    """Validate Ethereum address format"""
    if not address.startswith('0x'):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False


def checksum_address(address: str) -> str:
    """Convert Ethereum address to EIP-55 checksum format"""
    address = address.lower().replace('0x', '')
    addr_hash = keccak256(address.encode()).hex()
    result = '0x'
    for i, char in enumerate(address):
        if char.isdigit():
            result += char
        elif int(addr_hash[i], 16) >= 8:
            result += char.upper()
        else:
            result += char
    return result


def address_from_private_key(private_key_hex: str) -> str:
    """Derive Ethereum address from private key (simplified simulation)"""
    priv_bytes = bytes.fromhex(private_key_hex.replace('0x', ''))
    # Simplified: in production use secp256k1 library
    pub_key_hash = keccak256(priv_bytes)
    address = '0x' + pub_key_hash[-20:].hex()
    return checksum_address(address)


# ── Key Generation ────────────────────────────────────────────────────
def generate_wallet() -> Dict[str, str]:
    """Generate a new Ethereum wallet"""
    private_key = os.urandom(32)
    private_key_hex = private_key.hex()
    address = address_from_private_key(private_key_hex)

    return {
        "address":     address,
        "private_key": "0x" + private_key_hex,
        "warning":     "NEVER share your private key! Store securely offline.",
    }


# ── Transaction Utilities ─────────────────────────────────────────────
def encode_erc20_transfer(to: str, amount_wei: int) -> str:
    """
    Encode ERC-20 transfer(address,uint256) call data
    Function selector: 0xa9059cbb
    """
    if not is_valid_eth_address(to):
        raise ValueError(f"Invalid address: {to}")

    selector  = "a9059cbb"
    to_padded = to.replace('0x', '').zfill(64).lower()
    amount_hex = hex(amount_wei)[2:].zfill(64)
    return "0x" + selector + to_padded + amount_hex


def decode_erc20_transfer(calldata: str) -> Dict:
    """Decode an ERC-20 transfer call"""
    data = calldata.replace('0x', '')
    if data[:8] != 'a9059cbb':
        raise ValueError("Not an ERC-20 transfer")
    to_address = '0x' + data[8:72].lstrip('0')
    amount_wei = int(data[72:136], 16)
    return {
        "function":   "transfer(address,uint256)",
        "to":         to_address,
        "amount_wei": amount_wei,
        "amount_usdt": amount_wei / 10**6,  # USDT has 6 decimals
    }


def wei_to_eth(wei: int) -> float:
    """Convert wei to ETH"""
    return wei / 10**18


def eth_to_wei(eth: float) -> int:
    """Convert ETH to wei"""
    return int(eth * 10**18)


def usdt_to_units(usdt: float) -> int:
    """Convert USDT to base units (6 decimals)"""
    return int(usdt * 10**6)


def units_to_usdt(units: int) -> float:
    """Convert USDT base units to USDT"""
    return units / 10**6


# ── Mnemonic Utilities ────────────────────────────────────────────────
def generate_entropy(strength: int = 128) -> bytes:
    """Generate entropy for mnemonic (128 or 256 bits)"""
    if strength not in [128, 256]:
        raise ValueError("Strength must be 128 or 256 bits")
    return os.urandom(strength // 8)


def entropy_to_checksum(entropy: bytes) -> str:
    """Add BIP39 checksum to entropy"""
    h = hashlib.sha256(entropy).digest()
    checksum_bits = len(entropy) * 8 // 32
    entropy_bits = bin(int.from_bytes(entropy, 'big'))[2:].zfill(len(entropy)*8)
    checksum = bin(h[0])[2:].zfill(8)[:checksum_bits]
    return entropy_bits + checksum


# ── Chain Clarity USDT Payment Verifier ──────────────────────────────
class USDTPaymentVerifier:
    """
    Verify USDT payments for Chain Clarity ebook store
    Educational simulation — connect to real node for production
    """

    USDT_CONTRACTS = {
        "TRC20": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        "ERC20": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "BEP20": "0x55d398326f99059fF775485246999027B3197955",
    }

    EBOOK_PRICES = {
        "ebook_1": 19.00,   # Digital Currency Revolution
        "ebook_2": 19.00,   # Charity & Blockchain
        "ebook_3": 24.00,   # Blockchain & Supply Chain
        "ebook_4": 27.00,   # Blockchain Finance & AI Finance
        "bundle":  59.00,   # Complete Bundle
    }

    def verify_payment(
        self,
        network:   str,
        tx_hash:   str,
        product:   str,
        tolerance: float = 0.01
    ) -> Dict:
        """
        Simulate payment verification
        In production: connect to blockchain node and check actual transaction
        """
        expected_usdt = self.EBOOK_PRICES.get(product)
        if not expected_usdt:
            return {"valid": False, "error": "Unknown product"}

        # Simulate: in production use web3.py or tronpy to check tx
        print(f"\n  🔍 Verifying payment:")
        print(f"     Network:  {network}")
        print(f"     TX Hash:  {tx_hash[:20]}...")
        print(f"     Product:  {product}")
        print(f"     Expected: {expected_usdt} USDT")
        print(f"     Contract: {self.USDT_CONTRACTS.get(network, 'Unknown')}")
        print(f"\n  ⚠️  Connect to {network} node for real verification")
        print(f"     Use web3.py (ERC20/BEP20) or tronpy (TRC20)")

        return {
            "valid":          None,  # None = simulation mode
            "network":        network,
            "product":        product,
            "expected_usdt":  expected_usdt,
            "contract":       self.USDT_CONTRACTS.get(network),
            "verification_url": f"https://{'tronscan.org' if network=='TRC20' else 'etherscan.io'}/tx/{tx_hash}",
            "note": "Connect to blockchain node for real verification"
        }


# ── Demo ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("⛓  Chain Clarity Lab — Wallet Utilities")
    print("="*50)

    # Generate wallet
    print("\n1️⃣  Generating new wallet...")
    wallet = generate_wallet()
    print(f"   Address:     {wallet['address']}")
    print(f"   Private key: {wallet['private_key'][:10]}...HIDDEN")
    print(f"   ⚠️  {wallet['warning']}")

    # Encode USDT transfer
    print("\n2️⃣  Encoding USDT transfer (19 USDT for Ebook 1)...")
    calldata = encode_erc20_transfer(
        to="0x591379ce0EE304aD9eD1eAbd666508C9511C206D",
        amount_wei=usdt_to_units(19.00)
    )
    print(f"   Calldata: {calldata[:30]}...")

    # Decode it back
    print("\n3️⃣  Decoding USDT transfer calldata...")
    decoded = decode_erc20_transfer(calldata)
    print(f"   To:     {decoded['to']}")
    print(f"   Amount: {decoded['amount_usdt']} USDT")

    # Verify address
    print("\n4️⃣  Address validation...")
    test_addresses = [
        "0x591379ce0EE304aD9eD1eAbd666508C9511C206D",
        "invalid_address",
        "0xShortAddress",
    ]
    for addr in test_addresses:
        valid = is_valid_eth_address(addr)
        print(f"   {addr[:20]}... → {'✅ Valid' if valid else '❌ Invalid'}")

    # Payment verifier
    print("\n5️⃣  Chain Clarity Payment Verifier...")
    verifier = USDTPaymentVerifier()
    result = verifier.verify_payment(
        network="TRC20",
        tx_hash="0xABC123" + "0"*58,
        product="ebook_1"
    )

    print("\n⛓ Chain Clarity Lab | @chainclar")
