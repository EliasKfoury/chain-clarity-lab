"""
Post-Quantum Cryptography Simulation
=====================================
Chain Clarity Lab — @chainclar
Author: Elias Kfoury

Simulates CRYSTALS-Dilithium (ML-DSA) signature scheme concepts
and compares classical ECDSA vs post-quantum signature sizes.

NOTE: This is an educational simulation only.
For production use, install the official liboqs library:
    pip install liboqs-python
"""

import hashlib
import os
import time
import json
from dataclasses import dataclass, asdict
from typing import Tuple

# ── Simulated Key Sizes (bytes) — NIST FIPS 204 ──────────────────────
PQC_PARAMS = {
    "ML-DSA-44": {  # CRYSTALS-Dilithium Level 2
        "public_key_size": 1312,
        "private_key_size": 2528,
        "signature_size": 2420,
        "security_level": 2,
        "quantum_security_bits": 128,
    },
    "ML-DSA-65": {  # CRYSTALS-Dilithium Level 3
        "public_key_size": 1952,
        "private_key_size": 4000,
        "signature_size": 3293,
        "security_level": 3,
        "quantum_security_bits": 192,
    },
    "ML-DSA-87": {  # CRYSTALS-Dilithium Level 5
        "public_key_size": 2592,
        "private_key_size": 4864,
        "signature_size": 4595,
        "security_level": 5,
        "quantum_security_bits": 256,
    },
    "FN-DSA-512": {  # FALCON-512
        "public_key_size": 897,
        "private_key_size": 1281,
        "signature_size": 690,
        "security_level": 1,
        "quantum_security_bits": 108,
    },
    "FN-DSA-1024": {  # FALCON-1024
        "public_key_size": 1793,
        "private_key_size": 2305,
        "signature_size": 1330,
        "security_level": 5,
        "quantum_security_bits": 256,
    },
    "SLH-DSA-SHA2-128s": {  # SPHINCS+
        "public_key_size": 32,
        "private_key_size": 64,
        "signature_size": 7856,
        "security_level": 1,
        "quantum_security_bits": 128,
    },
}

CLASSICAL_PARAMS = {
    "ECDSA-secp256k1": {  # Bitcoin
        "public_key_size": 33,
        "private_key_size": 32,
        "signature_size": 71,
        "classical_security_bits": 128,
        "quantum_security_bits": 0,  # BROKEN by Shor's
    },
    "Ed25519": {  # Solana, many others
        "public_key_size": 32,
        "private_key_size": 64,
        "signature_size": 64,
        "classical_security_bits": 128,
        "quantum_security_bits": 0,  # BROKEN by Shor's
    },
    "RSA-2048": {
        "public_key_size": 256,
        "private_key_size": 1192,
        "signature_size": 256,
        "classical_security_bits": 112,
        "quantum_security_bits": 0,  # BROKEN by Shor's
    },
}


@dataclass
class KeyPair:
    algorithm:       str
    public_key:      bytes
    private_key:     bytes
    created_at:      float
    is_quantum_safe: bool


@dataclass
class Signature:
    algorithm:  str
    message:    bytes
    sig_bytes:  bytes
    signed_at:  float
    valid:      bool


class PQCSimulator:
    """
    Simulates post-quantum cryptographic operations.
    Uses real hash functions but simulated key/signature sizes.
    """

    def __init__(self, algorithm: str = "ML-DSA-65"):
        if algorithm not in PQC_PARAMS and algorithm not in CLASSICAL_PARAMS:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        self.algorithm  = algorithm
        self.is_pqc     = algorithm in PQC_PARAMS
        self.params     = PQC_PARAMS.get(algorithm) or CLASSICAL_PARAMS.get(algorithm)

    def generate_keypair(self) -> KeyPair:
        """Generate a simulated key pair"""
        start = time.perf_counter()
        pub_key  = os.urandom(self.params["public_key_size"])
        priv_key = os.urandom(self.params["private_key_size"])
        elapsed  = time.perf_counter() - start

        print(f"  [{self.algorithm}] Key generation: {elapsed*1000:.3f}ms")
        print(f"  Public key size:  {len(pub_key)} bytes")
        print(f"  Private key size: {len(priv_key)} bytes")

        return KeyPair(
            algorithm=self.algorithm,
            public_key=pub_key,
            private_key=priv_key,
            created_at=time.time(),
            is_quantum_safe=self.is_pqc,
        )

    def sign(self, keypair: KeyPair, message: bytes) -> Signature:
        """Sign a message (simulated)"""
        start = time.perf_counter()
        # Real hash of message
        msg_hash = hashlib.sha3_256(message + keypair.private_key).digest()
        # Simulated signature of correct size
        sig_bytes = os.urandom(self.params["signature_size"] - 32) + msg_hash[:32]
        elapsed  = time.perf_counter() - start

        print(f"  [{self.algorithm}] Sign: {elapsed*1000:.3f}ms | Sig size: {len(sig_bytes)} bytes")

        return Signature(
            algorithm=self.algorithm,
            message=message,
            sig_bytes=sig_bytes,
            signed_at=time.time(),
            valid=True,
        )

    def verify(self, keypair: KeyPair, signature: Signature) -> bool:
        """Verify a signature (simulated)"""
        start = time.perf_counter()
        expected_hash = hashlib.sha3_256(signature.message + keypair.private_key).digest()
        is_valid = signature.sig_bytes[-32:] == expected_hash[:32]
        elapsed  = time.perf_counter() - start

        print(f"  [{self.algorithm}] Verify: {elapsed*1000:.3f}ms | Valid: {is_valid}")
        return is_valid


def benchmark_all():
    """Benchmark and compare all algorithms"""
    print("\n" + "="*70)
    print("  CHAIN CLARITY LAB — POST-QUANTUM CRYPTOGRAPHY BENCHMARK")
    print("  @chainclar | chainclarify.netlify.app")
    print("="*70)

    message = b"Chain Clarity blockchain transaction: Send 100 USDT to 0xABC..."
    results = []

    # ── Classical algorithms ──────────────────────────────────────────
    print("\n🔴 CLASSICAL ALGORITHMS (QUANTUM VULNERABLE)")
    print("-"*50)
    for algo in CLASSICAL_PARAMS:
        sim     = PQCSimulator(algo)
        kp      = sim.generate_keypair()
        sig     = sim.sign(kp, message)
        valid   = sim.verify(kp, sig)
        results.append({
            "algorithm":    algo,
            "type":         "Classical",
            "quantum_safe": False,
            "pub_key_bytes": len(kp.public_key),
            "sig_bytes":     len(sig.sig_bytes),
            "valid":         valid,
        })
        print()

    # ── Post-quantum algorithms ───────────────────────────────────────
    print("\n🟢 POST-QUANTUM ALGORITHMS (NIST 2024 STANDARDS)")
    print("-"*50)
    for algo in ["ML-DSA-65", "FN-DSA-512", "SLH-DSA-SHA2-128s"]:
        sim   = PQCSimulator(algo)
        kp    = sim.generate_keypair()
        sig   = sim.sign(kp, message)
        valid = sim.verify(kp, sig)
        results.append({
            "algorithm":    algo,
            "type":         "Post-Quantum",
            "quantum_safe": True,
            "pub_key_bytes": len(kp.public_key),
            "sig_bytes":     len(sig.sig_bytes),
            "valid":         valid,
        })
        print()

    # ── Comparison table ──────────────────────────────────────────────
    print("\n📊 COMPARISON TABLE")
    print("-"*70)
    print(f"{'Algorithm':<25} {'Type':<15} {'Quantum':<10} {'PubKey':<10} {'Sig':<8}")
    print("-"*70)
    for r in results:
        qs = "✅ SAFE" if r["quantum_safe"] else "❌ BROKEN"
        print(f"{r['algorithm']:<25} {r['type']:<15} {qs:<10} "
              f"{r['pub_key_bytes']:<10} {r['sig_bytes']:<8}")

    print("\n📋 BLOCKCHAIN MIGRATION OVERHEAD")
    print("-"*70)
    ecdsa_sig = 71
    for r in results:
        if r["quantum_safe"]:
            overhead = r["sig_bytes"] / ecdsa_sig
            print(f"  {r['algorithm']}: {r['sig_bytes']} bytes "
                  f"({overhead:.1f}x larger than ECDSA)")

    # Save results
    with open("pqc_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n✅ Results saved to pqc_benchmark_results.json")


def simulate_blockchain_migration():
    """Simulate migrating a blockchain wallet to post-quantum"""
    print("\n" + "="*70)
    print("  BLOCKCHAIN WALLET PQC MIGRATION SIMULATION")
    print("="*70)

    # Step 1: Current classical wallet
    print("\n📍 Step 1: Current Wallet (ECDSA — QUANTUM VULNERABLE)")
    classical  = PQCSimulator("ECDSA-secp256k1")
    old_wallet = classical.generate_keypair()
    print(f"  ⚠️  This wallet is vulnerable to Shor's algorithm")
    print(f"  ⚠️  25% of all Bitcoin is in wallets like this")

    # Step 2: Generate PQC wallet
    print("\n📍 Step 2: New Post-Quantum Wallet (FALCON-512)")
    pqc       = PQCSimulator("FN-DSA-512")
    new_wallet = pqc.generate_keypair()
    print(f"  ✅ This wallet is quantum-safe (NIST FIPS 206)")

    # Step 3: Sign migration transaction
    print("\n📍 Step 3: Sign Migration Transaction")
    migration_tx = json.dumps({
        "from":    "0x" + old_wallet.public_key.hex()[:40],
        "to":      "0x" + new_wallet.public_key.hex()[:40],
        "action":  "MIGRATE_TO_PQC",
        "network": "Chain Clarity Lab",
    }).encode()

    # Both old and new sign (hybrid approach)
    old_sig = classical.sign(old_wallet, migration_tx)
    new_sig = pqc.sign(new_wallet, migration_tx)

    print(f"\n  Combined hybrid signature size: "
          f"{len(old_sig.sig_bytes) + len(new_sig.sig_bytes)} bytes")
    print(f"  ✅ Migration secured by BOTH classical AND post-quantum signatures")
    print(f"  ✅ Secure against both classical AND quantum attacks during transition")


if __name__ == "__main__":
    benchmark_all()
    simulate_blockchain_migration()
    print("\n\n⛓ Chain Clarity Lab | @chainclar | chainclarify.netlify.app\n")
