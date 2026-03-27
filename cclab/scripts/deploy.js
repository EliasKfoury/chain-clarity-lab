/**
 * Chain Clarity Lab — Deploy Script
 * @author Elias Kfoury — @chainclar
 *
 * Deploys all Chain Clarity smart contracts
 * Usage:
 *   npx hardhat run scripts/deploy.js --network localhost
 *   npx hardhat run scripts/deploy.js --network sepolia
 */

const { ethers } = require("hardhat");

async function main() {
  const [deployer] = await ethers.getSigners();
  const network    = await ethers.provider.getNetwork();

  console.log("\n⛓  Chain Clarity Lab — Contract Deployment");
  console.log("=".repeat(50));
  console.log(`Network:   ${network.name} (chainId: ${network.chainId})`);
  console.log(`Deployer:  ${deployer.address}`);
  console.log(`Balance:   ${ethers.formatEther(await ethers.provider.getBalance(deployer.address))} ETH`);

  const deployed = {};

  // ── 1. Deploy ChainClarityToken ─────────────────────────────────
  console.log("\n📦 Deploying ChainClarityToken (CCT)...");
  const Token = await ethers.getContractFactory("ChainClarityToken");
  const token = await Token.deploy(1_000_000); // 1 million tokens
  await token.waitForDeployment();
  deployed.token = await token.getAddress();
  console.log(`   ✅ CCT Token deployed: ${deployed.token}`);

  // ── 2. Deploy ChainClarityEscrow ────────────────────────────────
  console.log("\n📦 Deploying ChainClarityEscrow...");
  const sellerAddr  = deployer.address;  // Replace with actual seller
  const arbiterAddr = deployer.address;  // Replace with actual arbiter
  const Escrow = await ethers.getContractFactory("ChainClarityEscrow");
  const escrow = await Escrow.deploy(
    sellerAddr,
    arbiterAddr,
    30, // 30 day duration
    { value: ethers.parseEther("0.01") } // 0.01 ETH deposit
  );
  await escrow.waitForDeployment();
  deployed.escrow = await escrow.getAddress();
  console.log(`   ✅ Escrow deployed: ${deployed.escrow}`);

  // ── 3. Deploy ChainClarityVault ─────────────────────────────────
  console.log("\n📦 Deploying ChainClarityVault (DeFi)...");
  const Vault = await ethers.getContractFactory("ChainClarityVault");
  const vault = await Vault.deploy(500); // 5% APY
  await vault.waitForDeployment();
  deployed.vault = await vault.getAddress();
  console.log(`   ✅ Vault deployed: ${deployed.vault}`);

  // ── 4. Deploy HealthcareConsent ─────────────────────────────────
  console.log("\n📦 Deploying HealthcareConsent...");
  const Health = await ethers.getContractFactory("HealthcareConsent");
  const health = await Health.deploy();
  await health.waitForDeployment();
  deployed.healthcare = await health.getAddress();
  console.log(`   ✅ HealthcareConsent deployed: ${deployed.healthcare}`);

  // ── 5. Deploy SupplyChainTracker ────────────────────────────────
  console.log("\n📦 Deploying SupplyChainTracker...");
  const Supply = await ethers.getContractFactory("SupplyChainTracker");
  const supply = await Supply.deploy();
  await supply.waitForDeployment();
  deployed.supplyChain = await supply.getAddress();
  console.log(`   ✅ SupplyChainTracker deployed: ${deployed.supplyChain}`);

  // ── 6. Deploy ChainClarityDAO ───────────────────────────────────
  console.log("\n📦 Deploying ChainClarityDAO...");
  const DAO = await ethers.getContractFactory("ChainClarityDAO");
  const dao = await DAO.deploy(deployed.token);
  await dao.waitForDeployment();
  deployed.dao = await dao.getAddress();
  console.log(`   ✅ DAO deployed: ${deployed.dao}`);

  // ── Summary ──────────────────────────────────────────────────────
  console.log("\n" + "=".repeat(50));
  console.log("✅ ALL CONTRACTS DEPLOYED SUCCESSFULLY");
  console.log("=".repeat(50));
  for (const [name, address] of Object.entries(deployed)) {
    console.log(`  ${name.padEnd(15)}: ${address}`);
  }

  // Save deployment addresses
  const fs = require("fs");
  const deploymentData = {
    network:   network.name,
    chainId:   network.chainId.toString(),
    deployer:  deployer.address,
    timestamp: new Date().toISOString(),
    contracts: deployed,
  };
  fs.writeFileSync(
    `deployments-${network.chainId}.json`,
    JSON.stringify(deploymentData, null, 2)
  );
  console.log(`\n📄 Deployment saved to deployments-${network.chainId}.json`);
  console.log("\n⛓  Chain Clarity Lab | @chainclar | chainclarify.netlify.app\n");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
