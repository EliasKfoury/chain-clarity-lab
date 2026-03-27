# Getting Started — Chain Clarity Lab

**Chain Clarity Lab** | @chainclar | [chainclarify](https://beacons.ai/chainclarity)

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| npm | 9+ | Comes with Node.js |
| Python | 3.9+ | [python.org](https://python.org) |
| Git | Any | [git-scm.com](https://git-scm.com) |

---

## Quick Setup

```bash
# 1. Clone the repository
git clone https://github.com/chainclar/chain-clarity-lab.git
cd chain-clarity-lab

# 2. Install Node.js dependencies
npm install

# 3. Install Python dependencies
pip install web3 eth-account requests python-dotenv

# 4. Copy environment template
cp .env.example .env
# Edit .env with your RPC URLs and API keys
```

---

## Smart Contracts

### Compile
```bash
npx hardhat compile
```

### Test
```bash
# Run all tests
npx hardhat test

# Run with gas report
REPORT_GAS=true npx hardhat test

# Run specific test
npx hardhat test test/ChainClarity.test.js
```

### Deploy locally
```bash
# Start local Hardhat node
npx hardhat node

# In a new terminal, deploy
npx hardhat run scripts/deploy.js --network localhost
```

### Deploy to testnet
```bash
# Deploy to Sepolia testnet
npx hardhat run scripts/deploy.js --network sepolia
```

---

## Python Tools

### Post-Quantum Cryptography Benchmark
```bash
cd post-quantum/pqc-signatures
python pqc_simulator.py
```

### QKD Protocol Simulation
```bash
cd post-quantum/qkd-simulation
python bb84_qkd.py
```

### Wallet Utilities
```bash
cd tools/wallet-utils
python wallet_utils.py
```

### On-Chain Analytics
```bash
cd tools/on-chain-analytics
python analytics.py
```

---

## Environment Variables

Create a `.env` file in the root directory:

```env
# RPC URLs (get free keys from Infura or Alchemy)
MAINNET_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_INFURA_KEY
BSC_RPC_URL=https://bsc-dataseed.binance.org/

# Deployer private key (NEVER commit this!)
PRIVATE_KEY=your_private_key_here

# Block explorer API keys (for contract verification)
ETHERSCAN_API_KEY=your_etherscan_key
POLYGONSCAN_API_KEY=your_polygonscan_key
BSCSCAN_API_KEY=your_bscscan_key

# Optional
CMC_API_KEY=your_coinmarketcap_key
```

> ⚠️ **NEVER commit your `.env` file or private keys to Git!**

---

## Project Structure

```
chain-clarity-lab/
├── smart-contracts/
│   ├── escrow/          ChainClarityEscrow.sol
│   ├── tokens/          ChainClarityToken.sol (ERC-20)
│   ├── defi/            ChainClarityVault.sol
│   └── healthcare/      HealthcareConsent.sol
├── blockchain-demos/
│   ├── supply-chain/    SupplyChainTracker.sol
│   ├── identity/        (coming soon)
│   └── voting/          ChainClarityDAO.sol
├── post-quantum/
│   ├── pqc-signatures/  pqc_simulator.py
│   └── qkd-simulation/  bb84_qkd.py
├── tools/
│   ├── wallet-utils/    wallet_utils.py
│   └── on-chain-analytics/ analytics.py
├── test/                ChainClarity.test.js
├── scripts/             deploy.js
├── hardhat.config.js
└── package.json
```

---

## Learn More

📚 **Chain Clarity Ebook Series**
- [Decoding The Digital Currency Revolution](https://beacons.ai/chainclarity)
- [Blockchain & Supply Chain](https://beacons.ai/chainclarity)
- [Blockchain Finance & AI Finance](https://beacons.ai/chainclarity)
- [Healthcare & Blockchain](https://beacons.ai/chainclarity)
- [Blockchain & Quantum](https://beacons.ai/chainclarity)

📷 **Instagram:** [@chainclar](https://instagram.com/chainclar)  
🌐 **Website:** [chainclarify](https://beacons.ai/chainclarity)  
📧 **Email:** n.satoshi@gmx.com

---

*Chain Clarity Lab — Blockchain Research & Development · 2026*
