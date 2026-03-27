"""
On-Chain Analytics Tool
========================
Chain Clarity Lab — @chainclar
Author: Elias Kfoury

Blockchain data analysis utilities:
- Transaction volume analysis
- Gas price tracking
- DeFi yield comparison
- USDT flow tracking
"""

import json
import time
import hashlib
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Transaction:
    tx_hash:   str
    from_addr: str
    to_addr:   str
    value_eth: float
    gas_used:  int
    gas_price:  int   # in gwei
    timestamp:  int
    block:      int


@dataclass
class DeFiProtocol:
    name:         str
    tvl_usd:      float
    apy_percent:  float
    chain:        str
    risk_level:   str   # Low / Medium / High


class BlockchainAnalytics:
    """
    On-chain analytics with simulated data
    Connect to real nodes for production use:
      - Ethereum: web3.py
      - BSC: web3.py with BSC RPC
      - Tron: tronpy
    """

    def __init__(self):
        self.networks = {
            "ethereum": {"rpc": "https://mainnet.infura.io/v3/YOUR_KEY", "chain_id": 1},
            "bsc":      {"rpc": "https://bsc-dataseed.binance.org/",      "chain_id": 56},
            "polygon":  {"rpc": "https://polygon-rpc.com/",               "chain_id": 137},
            "tron":     {"rpc": "https://api.trongrid.io",                "chain_id": 0},
        }

    # ── Transaction Analysis ──────────────────────────────────────────
    def simulate_transactions(self, n: int = 50) -> List[Transaction]:
        """Generate simulated transaction data for analysis"""
        addresses = ["0x" + hashlib.sha256(str(i).encode()).hexdigest()[:40] for i in range(10)]
        txs = []
        base_time = int(time.time()) - 86400  # 24 hours ago

        for i in range(n):
            txs.append(Transaction(
                tx_hash=   "0x" + hashlib.sha256(str(i*7).encode()).hexdigest(),
                from_addr= random.choice(addresses),
                to_addr=   random.choice(addresses),
                value_eth= round(random.uniform(0.01, 5.0), 4),
                gas_used=  random.randint(21000, 200000),
                gas_price= random.randint(10, 80),  # gwei
                timestamp= base_time + i * (86400 // n),
                block=     18500000 + i
            ))
        return txs

    def analyse_transactions(self, txs: List[Transaction]) -> Dict:
        """Analyse a list of transactions"""
        total_value = sum(t.value_eth for t in txs)
        total_fees  = sum(t.gas_used * t.gas_price * 1e-9 for t in txs)  # ETH
        avg_gas     = sum(t.gas_price for t in txs) / len(txs)

        # Volume by hour
        hourly = {}
        for tx in txs:
            hour = datetime.fromtimestamp(tx.timestamp).strftime("%H:00")
            hourly[hour] = hourly.get(hour, 0) + tx.value_eth

        return {
            "total_transactions": len(txs),
            "total_volume_eth":   round(total_value, 4),
            "total_fees_eth":     round(total_fees, 6),
            "avg_gas_price_gwei": round(avg_gas, 1),
            "peak_hour":          max(hourly, key=hourly.get) if hourly else "N/A",
            "hourly_volume":      hourly,
        }

    # ── Gas Analysis ──────────────────────────────────────────────────
    def gas_cost_calculator(self, action: str, gas_price_gwei: float, eth_price_usd: float) -> Dict:
        """Calculate gas costs for common blockchain actions"""
        gas_limits = {
            "ETH Transfer":          21_000,
            "ERC-20 Transfer":       65_000,
            "ERC-20 Approve":        46_000,
            "Uniswap Swap":         150_000,
            "Escrow Deploy":        300_000,
            "Smart Contract Call":  100_000,
            "NFT Mint":             150_000,
            "DAO Vote":              80_000,
            "PQC Signature (est)": 500_000,   # Post-quantum larger signature
        }

        gas_limit = gas_limits.get(action, 100_000)
        eth_cost  = (gas_limit * gas_price_gwei) / 1e9
        usd_cost  = eth_cost * eth_price_usd

        return {
            "action":           action,
            "gas_limit":        gas_limit,
            "gas_price_gwei":   gas_price_gwei,
            "eth_cost":         round(eth_cost, 6),
            "usd_cost":         round(usd_cost, 4),
        }

    # ── DeFi Analytics ────────────────────────────────────────────────
    def get_defi_protocols(self) -> List[DeFiProtocol]:
        """Simulated DeFi protocol data — connect to DeFiLlama API for real data"""
        return [
            DeFiProtocol("Aave V3",      50_000_000_000, 4.2,  "Ethereum", "Low"),
            DeFiProtocol("Compound",     10_000_000_000, 3.8,  "Ethereum", "Low"),
            DeFiProtocol("Uniswap V3",   8_000_000_000,  12.5, "Ethereum", "Medium"),
            DeFiProtocol("PancakeSwap",  3_000_000_000,  18.3, "BSC",      "Medium"),
            DeFiProtocol("Curve Finance",20_000_000_000, 5.1,  "Ethereum", "Low"),
            DeFiProtocol("Yearn Finance", 500_000_000,  9.7,  "Ethereum", "Medium"),
            DeFiProtocol("GMX",           600_000_000,  22.0, "Arbitrum", "High"),
        ]

    def compare_yields(self, investment_usd: float) -> None:
        """Compare DeFi yields for a given investment"""
        protocols = self.get_defi_protocols()

        print(f"\n💰 Yield Comparison for ${investment_usd:,.0f} Investment")
        print("="*65)
        print(f"{'Protocol':<18} {'Chain':<12} {'APY%':<8} {'Annual ($)':<14} {'Risk'}")
        print("-"*65)

        protocols.sort(key=lambda x: x.apy_percent, reverse=True)
        for p in protocols:
            annual = investment_usd * p.apy_percent / 100
            risk_emoji = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}.get(p.risk_level, "⚪")
            print(f"{p.name:<18} {p.chain:<12} {p.apy_percent:<8.1f} "
                  f"${annual:<13,.0f} {risk_emoji} {p.risk_level}")

    # ── USDT Flow Analysis ────────────────────────────────────────────
    def analyse_usdt_flows(self, address: str) -> Dict:
        """
        Simulate USDT flow analysis for an address
        In production: use Etherscan/BSCScan API with your key
        """
        # Simulate 30 days of USDT transactions
        inflows  = [random.uniform(10, 200) for _ in range(random.randint(5, 20))]
        outflows = [random.uniform(10, 200) for _ in range(random.randint(3, 15))]

        return {
            "address":          address,
            "period":           "Last 30 days",
            "total_inflow":     round(sum(inflows), 2),
            "total_outflow":    round(sum(outflows), 2),
            "net_flow":         round(sum(inflows) - sum(outflows), 2),
            "tx_count":         len(inflows) + len(outflows),
            "avg_tx_size":      round((sum(inflows) + sum(outflows)) / (len(inflows) + len(outflows)), 2),
            "note":             "Connect to Etherscan API for real data",
            "api_endpoint":     f"https://api.etherscan.io/api?module=account&action=tokentx&address={address}",
        }


# ── Gas Price Tracker ─────────────────────────────────────────────────
class GasTracker:
    """Real-time gas price analysis (simulated)"""

    def get_recommendations(self) -> Dict:
        """Get gas price recommendations"""
        base = random.randint(15, 40)  # gwei
        return {
            "slow":     {"gwei": base - 5,    "wait": "~5 min",  "usd_transfer": round((base-5)*21000/1e9*3000, 4)},
            "standard": {"gwei": base,         "wait": "~1 min",  "usd_transfer": round(base*21000/1e9*3000, 4)},
            "fast":     {"gwei": base + 10,    "wait": "~15 sec", "usd_transfer": round((base+10)*21000/1e9*3000, 4)},
            "urgent":   {"gwei": base + 25,    "wait": "~10 sec", "usd_transfer": round((base+25)*21000/1e9*3000, 4)},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source":    "Simulated — connect to https://api.etherscan.io/api?module=gastracker for real data",
        }


# ── Demo ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("⛓  Chain Clarity Lab — On-Chain Analytics")
    print("="*55)

    analytics = BlockchainAnalytics()

    # Transaction analysis
    print("\n📊 Transaction Analysis (simulated 50 txs)")
    txs    = analytics.simulate_transactions(50)
    report = analytics.analyse_transactions(txs)
    for k, v in report.items():
        if k != "hourly_volume":
            print(f"   {k}: {v}")

    # Gas costs
    print("\n⛽ Gas Cost Calculator (30 gwei, ETH=$3,000)")
    for action in ["ETH Transfer", "ERC-20 Transfer", "Escrow Deploy", "PQC Signature (est)"]:
        r = analytics.gas_cost_calculator(action, 30, 3000)
        print(f"   {r['action']:<28} ${r['usd_cost']:.4f}")

    # DeFi yields
    analytics.compare_yields(10000)

    # Gas recommendations
    gas = GasTracker()
    recs = gas.get_recommendations()
    print(f"\n⛽ Gas Recommendations (ETH Mainnet)")
    for speed, data in recs.items():
        if isinstance(data, dict):
            print(f"   {speed.upper():<10}: {data['gwei']} gwei | {data['wait']}")

    print("\n⛓ Chain Clarity Lab | @chainclar")
