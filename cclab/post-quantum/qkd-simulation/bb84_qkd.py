"""
Quantum Key Distribution (QKD) — BB84 Protocol Simulation
============================================================
Chain Clarity Lab — @chainclar
Author: Elias Kfoury

Simulates the BB84 QKD protocol:
- Alice generates random bits and sends quantum states
- Bob measures with random bases
- Basis reconciliation over classical channel
- Eavesdrop detection via error rate analysis
- Privacy amplification to produce final secret key
"""

import random
import hashlib
import math
from typing import List, Tuple, Optional


# ── Quantum Basis Definitions ────────────────────────────────────────
# Rectilinear basis (+): 0=horizontal(→), 1=vertical(↑)
# Diagonal basis (×):    0=diagonal(↗),  1=anti-diagonal(↘)

BASES    = ['+', '×']
SYMBOLS  = {
    ('+', 0): '→', ('+', 1): '↑',
    ('×', 0): '↗', ('×', 1): '↘',
}


class QuantumChannel:
    """Simulates a quantum channel that may be eavesdropped"""

    def __init__(self, eavesdrop: bool = False, error_rate: float = 0.02):
        self.eavesdrop  = eavesdrop
        self.error_rate = error_rate   # Channel noise (independent of eavesdropping)
        self.intercepted_count = 0

    def transmit(self, bit: int, alice_basis: str) -> Tuple[int, str]:
        """
        Transmit a qubit from Alice to Bob (with possible eavesdropping)
        Returns: (received_bit, alice_basis_preserved)
        """
        received_bit   = bit
        current_basis  = alice_basis

        # Eve intercepts and re-sends
        if self.eavesdrop:
            eve_basis = random.choice(BASES)
            if eve_basis != alice_basis:
                # Wrong basis measurement — collapses qubit, introduces error
                received_bit = random.randint(0, 1)
                self.intercepted_count += 1

        # Channel noise
        if random.random() < self.error_rate:
            received_bit = 1 - received_bit

        return received_bit, current_basis


class Alice:
    """Alice — the sender of quantum key bits"""

    def __init__(self, n_bits: int):
        self.n_bits    = n_bits
        self.bits      = [random.randint(0, 1) for _ in range(n_bits)]
        self.bases     = [random.choice(BASES) for _ in range(n_bits)]
        self.sifted_key: List[int] = []

    def prepare_qubits(self) -> List[Tuple[int, str]]:
        """Prepare qubits for transmission"""
        return list(zip(self.bits, self.bases))

    def sift_key(self, matching_indices: List[int]):
        """Keep only bits where bases matched"""
        self.sifted_key = [self.bits[i] for i in matching_indices]

    def privacy_amplify(self, error_indices: List[int]) -> bytes:
        """Apply hash to remove any partial Eve knowledge"""
        secure_indices = [i for i in range(len(self.sifted_key))
                         if i not in error_indices]
        secure_bits = [self.sifted_key[i] for i in secure_indices]
        bit_string  = ''.join(map(str, secure_bits))
        return hashlib.sha3_256(bit_string.encode()).digest()


class Bob:
    """Bob — the receiver of quantum key bits"""

    def __init__(self, n_bits: int):
        self.n_bits       = n_bits
        self.bases        = [random.choice(BASES) for _ in range(n_bits)]
        self.measurements: List[int] = []
        self.sifted_key:   List[int] = []

    def measure(self, received_bit: int, alice_basis: str) -> int:
        """Measure incoming qubit in Bob's chosen basis"""
        idx = self.measurements.__len__()
        bob_basis = self.bases[idx] if idx < len(self.bases) else random.choice(BASES)

        if bob_basis == alice_basis:
            # Same basis — correct measurement
            result = received_bit
        else:
            # Different basis — random result (quantum superposition collapse)
            result = random.randint(0, 1)

        self.measurements.append(result)
        return result

    def sift_key(self, matching_indices: List[int]):
        """Keep only bits where bases matched"""
        self.sifted_key = [self.measurements[i] for i in matching_indices]

    def privacy_amplify(self, error_indices: List[int]) -> bytes:
        """Apply same hash as Alice to derive identical key"""
        secure_indices = [i for i in range(len(self.sifted_key))
                         if i not in error_indices]
        secure_bits = [self.sifted_key[i] for i in secure_indices]
        bit_string  = ''.join(map(str, secure_bits))
        return hashlib.sha3_256(bit_string.encode()).digest()


def run_bb84_protocol(
    n_bits: int = 1000,
    eavesdrop: bool = False,
    channel_noise: float = 0.02,
    verbose: bool = True
) -> dict:
    """
    Run the complete BB84 QKD protocol

    Args:
        n_bits:        Number of qubits to transmit
        eavesdrop:     Whether Eve intercepts the channel
        channel_noise: Background error rate (0.0 to 0.1)
        verbose:       Print detailed output

    Returns:
        dict with protocol results
    """
    if verbose:
        print("\n" + "="*60)
        print("  CHAIN CLARITY LAB — BB84 QKD PROTOCOL SIMULATION")
        print("  @chainclar | chainclarify.netlify.app")
        print("="*60)
        print(f"\n  Qubits to transmit:  {n_bits}")
        print(f"  Eavesdropping:       {'⚠️  YES — EVE IS ACTIVE' if eavesdrop else '✅ No'}")
        print(f"  Channel noise:       {channel_noise*100:.1f}%")

    # ── Step 1: Alice prepares qubits ────────────────────────────────
    alice   = Alice(n_bits)
    bob     = Bob(n_bits)
    channel = QuantumChannel(eavesdrop=eavesdrop, error_rate=channel_noise)

    if verbose: print(f"\n📡 Step 1: Alice prepares {n_bits} qubits")

    # ── Step 2: Quantum transmission ─────────────────────────────────
    qubits    = alice.prepare_qubits()
    bob.bases = [random.choice(BASES) for _ in range(n_bits)]

    for i, (bit, alice_basis) in enumerate(qubits):
        received_bit, _ = channel.transmit(bit, alice_basis)
        bob_basis = bob.bases[i]
        if bob_basis == alice_basis:
            bob.measurements.append(received_bit)
        else:
            bob.measurements.append(random.randint(0, 1))

    if verbose:
        print(f"📡 Step 2: {n_bits} qubits transmitted")
        if eavesdrop:
            print(f"   ⚠️  Eve intercepted ~{channel.intercepted_count} qubits")

    # ── Step 3: Basis reconciliation (public) ────────────────────────
    matching_indices = [i for i in range(n_bits)
                       if alice.bases[i] == bob.bases[i]]

    alice.sift_key(matching_indices)
    bob.sift_key(matching_indices)
    sifted_length = len(matching_indices)

    if verbose:
        print(f"\n🔑 Step 3: Basis reconciliation")
        print(f"   Matching bases: {sifted_length} / {n_bits} "
              f"({sifted_length/n_bits*100:.1f}%)")

    # ── Step 4: Error estimation ──────────────────────────────────────
    sample_size   = min(100, sifted_length // 4)
    sample_indices = random.sample(range(sifted_length), sample_size)

    errors = sum(1 for i in sample_indices
                if alice.sifted_key[i] != bob.sifted_key[i])
    error_rate = errors / sample_size if sample_size > 0 else 0

    # Threshold: >11% error rate indicates eavesdropping
    eve_detected = error_rate > 0.11

    if verbose:
        print(f"\n🔍 Step 4: Error rate estimation")
        print(f"   Sample size:  {sample_size} bits")
        print(f"   Errors found: {errors}")
        print(f"   Error rate:   {error_rate*100:.2f}%")
        print(f"   Threshold:    11%")
        if eve_detected:
            print(f"   🚨 EVE DETECTED! Error rate exceeds threshold. ABORT.")
        else:
            print(f"   ✅ Channel secure — error rate within normal bounds")

    # ── Step 5: Privacy amplification ────────────────────────────────
    final_key = None
    key_length = 0

    if not eve_detected:
        final_key  = alice.privacy_amplify(sample_indices)
        bob_key    = bob.privacy_amplify(sample_indices)
        key_length = len(final_key) * 8  # bits
        keys_match = final_key == bob_key

        if verbose:
            print(f"\n🔐 Step 5: Privacy amplification")
            print(f"   Final key length: {key_length} bits ({len(final_key)} bytes)")
            print(f"   Keys match: {'✅ YES' if keys_match else '❌ NO'}")
            print(f"\n   Alice's key: {final_key.hex()[:32]}...")
            print(f"   Bob's key:   {bob_key.hex()[:32]}...")

    if verbose:
        print(f"\n📊 PROTOCOL SUMMARY")
        print(f"   Qubits sent:        {n_bits}")
        print(f"   Sifted key bits:    {sifted_length}")
        print(f"   Final key bits:     {key_length}")
        print(f"   Efficiency:         {key_length/n_bits*100:.1f}%")
        print(f"   Eve detected:       {'YES ⚠️' if eve_detected else 'NO ✅'}")
        print(f"   Key established:    {'NO — aborted' if eve_detected else 'YES ✅'}")

    return {
        "n_bits":          n_bits,
        "sifted_length":   sifted_length,
        "error_rate":      error_rate,
        "eve_detected":    eve_detected,
        "key_length_bits": key_length,
        "key":             final_key.hex() if final_key else None,
        "eavesdropped":    eavesdrop,
    }


if __name__ == "__main__":
    print("\n🔬 TEST 1: Normal channel (no eavesdropping)")
    result1 = run_bb84_protocol(n_bits=1000, eavesdrop=False, verbose=True)

    print("\n\n🔬 TEST 2: Channel with active eavesdropper (Eve)")
    result2 = run_bb84_protocol(n_bits=1000, eavesdrop=True, verbose=True)

    print("\n\n⛓ Chain Clarity Lab | @chainclar | chainclarify.netlify.app\n")
