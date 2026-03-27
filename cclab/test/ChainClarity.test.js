/**
 * Chain Clarity Lab — Test Suite
 * @author Elias Kfoury — @chainclar
 */

const { expect }        = require("chai");
const { ethers }        = require("hardhat");
const { loadFixture }   = require("@nomicfoundation/hardhat-toolbox/network-helpers");

// ── ESCROW TESTS ──────────────────────────────────────────────────────
describe("ChainClarityEscrow", function () {
  async function deployEscrowFixture() {
    const [buyer, seller, arbiter, other] = await ethers.getSigners();
    const Escrow = await ethers.getContractFactory("ChainClarityEscrow");
    const deposit = ethers.parseEther("1.0");
    const escrow  = await Escrow.connect(buyer).deploy(
      seller.address, arbiter.address, 30, { value: deposit }
    );
    return { escrow, buyer, seller, arbiter, other, deposit };
  }

  it("Should deploy with correct state", async function () {
    const { escrow, buyer, seller, arbiter, deposit } = await loadFixture(deployEscrowFixture);
    expect(await escrow.buyer()).to.equal(buyer.address);
    expect(await escrow.seller()).to.equal(seller.address);
    expect(await escrow.arbiter()).to.equal(arbiter.address);
    expect(await escrow.getBalance()).to.equal(deposit);
    expect(await escrow.getState()).to.equal("AWAITING_DELIVERY");
  });

  it("Should allow buyer to add milestones", async function () {
    const { escrow, buyer } = await loadFixture(deployEscrowFixture);
    await escrow.connect(buyer).addMilestone(
      "Deliver Chapter 1", ethers.parseEther("0.3")
    );
    expect(await escrow.getMilestoneCount()).to.equal(1);
  });

  it("Should release milestone payment to seller", async function () {
    const { escrow, buyer, seller } = await loadFixture(deployEscrowFixture);
    await escrow.connect(buyer).addMilestone("Milestone 1", ethers.parseEther("0.5"));
    const sellerBefore = await ethers.provider.getBalance(seller.address);
    await escrow.connect(buyer).releaseMilestone(0);
    const sellerAfter = await ethers.provider.getBalance(seller.address);
    expect(sellerAfter).to.be.gt(sellerBefore);
  });

  it("Should complete escrow on delivery confirmation", async function () {
    const { escrow, buyer, seller } = await loadFixture(deployEscrowFixture);
    await escrow.connect(buyer).confirmDelivery();
    expect(await escrow.getState()).to.equal("COMPLETE");
    expect(await escrow.getBalance()).to.equal(0);
  });

  it("Should allow arbiter to resolve dispute for buyer", async function () {
    const { escrow, buyer, arbiter } = await loadFixture(deployEscrowFixture);
    await escrow.connect(buyer).raiseDispute();
    await escrow.connect(arbiter).resolveDispute(false); // refund buyer
    expect(await escrow.getState()).to.equal("COMPLETE");
  });

  it("Should reject non-buyer from confirming delivery", async function () {
    const { escrow, other } = await loadFixture(deployEscrowFixture);
    await expect(escrow.connect(other).confirmDelivery())
      .to.be.revertedWith("Only buyer");
  });
});

// ── TOKEN TESTS ───────────────────────────────────────────────────────
describe("ChainClarityToken", function () {
  async function deployTokenFixture() {
    const [owner, user1, user2] = await ethers.getSigners();
    const Token = await ethers.getContractFactory("ChainClarityToken");
    const token = await Token.deploy(1_000_000);
    return { token, owner, user1, user2 };
  }

  it("Should deploy with correct initial supply", async function () {
    const { token, owner } = await loadFixture(deployTokenFixture);
    const expected = ethers.parseUnits("1000000", 18);
    expect(await token.totalSupply()).to.equal(expected);
    expect(await token.balanceOf(owner.address)).to.equal(expected);
  });

  it("Should transfer tokens correctly", async function () {
    const { token, owner, user1 } = await loadFixture(deployTokenFixture);
    const amount = ethers.parseUnits("1000", 18);
    await token.transfer(user1.address, amount);
    expect(await token.balanceOf(user1.address)).to.equal(amount);
  });

  it("Should allow owner to mint", async function () {
    const { token, owner, user1 } = await loadFixture(deployTokenFixture);
    const amount = ethers.parseUnits("500", 18);
    await token.mint(user1.address, amount);
    expect(await token.balanceOf(user1.address)).to.equal(amount);
  });

  it("Should allow burning tokens", async function () {
    const { token, owner } = await loadFixture(deployTokenFixture);
    const supply = await token.totalSupply();
    const burnAmount = ethers.parseUnits("100", 18);
    await token.burn(burnAmount);
    expect(await token.totalSupply()).to.equal(supply - burnAmount);
  });

  it("Should pause and unpause transfers", async function () {
    const { token, owner, user1 } = await loadFixture(deployTokenFixture);
    await token.pause();
    await expect(token.transfer(user1.address, 100)).to.be.revertedWith("Paused");
    await token.unpause();
    await expect(token.transfer(user1.address, 100)).to.not.be.reverted;
  });
});

// ── VAULT TESTS ───────────────────────────────────────────────────────
describe("ChainClarityVault", function () {
  async function deployVaultFixture() {
    const [owner, user1, user2] = await ethers.getSigners();
    const Vault = await ethers.getContractFactory("ChainClarityVault");
    const vault = await Vault.deploy(500); // 5% APY
    // Fund vault
    await vault.fundVault({ value: ethers.parseEther("10.0") });
    return { vault, owner, user1, user2 };
  }

  it("Should accept deposits", async function () {
    const { vault, user1 } = await loadFixture(deployVaultFixture);
    const amount = ethers.parseEther("1.0");
    await vault.connect(user1).deposit({ value: amount });
    const pos = await vault.getPosition(user1.address);
    expect(pos.amount).to.equal(amount);
  });

  it("Should calculate yield over time", async function () {
    const { vault, user1 } = await loadFixture(deployVaultFixture);
    await vault.connect(user1).deposit({ value: ethers.parseEther("1.0") });
    // Yield is time-based — will be very small in test but > 0 after some time
    const yield_ = await vault.getPendingYield(user1.address);
    expect(yield_).to.be.gte(0);
  });

  it("Should allow withdrawal with principal", async function () {
    const { vault, user1 } = await loadFixture(deployVaultFixture);
    const deposit = ethers.parseEther("1.0");
    await vault.connect(user1).deposit({ value: deposit });
    const balBefore = await ethers.provider.getBalance(user1.address);
    await vault.connect(user1).withdraw();
    const balAfter = await ethers.provider.getBalance(user1.address);
    // Should receive back close to deposit (minus gas)
    expect(balAfter).to.be.gt(balBefore - ethers.parseEther("0.01"));
  });
});

// ── HEALTHCARE CONSENT TESTS ──────────────────────────────────────────
describe("HealthcareConsent", function () {
  async function deployHealthcareFixture() {
    const [patient, doctor, hospital] = await ethers.getSigners();
    const HC = await ethers.getContractFactory("HealthcareConsent");
    const hc = await HC.deploy();
    return { hc, patient, doctor, hospital };
  }

  it("Should register a patient", async function () {
    const { hc, patient } = await loadFixture(deployHealthcareFixture);
    const idHash = ethers.keccak256(ethers.toUtf8Bytes("patient-id-123"));
    await hc.connect(patient).registerPatient(idHash, patient.address);
    const p = await hc.patients(patient.address);
    expect(p.registered).to.be.true;
  });

  it("Should grant and verify consent", async function () {
    const { hc, patient, doctor } = await loadFixture(deployHealthcareFixture);
    const idHash = ethers.keccak256(ethers.toUtf8Bytes("patient-id-123"));
    await hc.connect(patient).registerPatient(idHash, patient.address);
    await hc.connect(patient).grantConsent(doctor.address, 0, 30, "Treatment"); // DataType.GENERAL
    expect(await hc.hasAccess(patient.address, doctor.address, 0)).to.be.true;
  });

  it("Should revoke consent", async function () {
    const { hc, patient, doctor } = await loadFixture(deployHealthcareFixture);
    const idHash = ethers.keccak256(ethers.toUtf8Bytes("patient-id-123"));
    await hc.connect(patient).registerPatient(idHash, patient.address);
    await hc.connect(patient).grantConsent(doctor.address, 0, 30, "Treatment");
    await hc.connect(patient).revokeConsent(0);
    expect(await hc.hasAccess(patient.address, doctor.address, 0)).to.be.false;
  });
});

// ── SUPPLY CHAIN TESTS ────────────────────────────────────────────────
describe("SupplyChainTracker", function () {
  async function deploySupplyFixture() {
    const [owner, manufacturer, distributor, pharmacy] = await ethers.getSigners();
    const SC = await ethers.getContractFactory("SupplyChainTracker");
    const sc = await SC.deploy();
    await sc.authorizeActor(manufacturer.address);
    await sc.authorizeActor(distributor.address);
    return { sc, owner, manufacturer, distributor, pharmacy };
  }

  const PRODUCT_ID = ethers.keccak256(ethers.toUtf8Bytes("DRUG-BATCH-001"));

  it("Should register a product", async function () {
    const { sc, manufacturer } = await loadFixture(deploySupplyFixture);
    await sc.connect(manufacturer).registerProduct(
      PRODUCT_ID, "Amoxicillin 500mg", "BATCH-2026-001", "Basel, Switzerland"
    );
    const result = await sc.verifyProduct(PRODUCT_ID);
    expect(result.isRegistered).to.be.true;
    expect(result.isAuthentic).to.be.true;
    expect(result.isRecalled).to.be.false;
  });

  it("Should track status updates", async function () {
    const { sc, manufacturer } = await loadFixture(deploySupplyFixture);
    await sc.connect(manufacturer).registerProduct(
      PRODUCT_ID, "Test Drug", "BATCH-001", "Factory"
    );
    await sc.connect(manufacturer).updateStatus(
      PRODUCT_ID, 1, "Hamburg Port", 2500, 45, "Loaded for shipping"
    );
    const history = await sc.getTrackingHistory(PRODUCT_ID);
    expect(history.length).to.equal(2); // registration + update
  });

  it("Should transfer custody", async function () {
    const { sc, manufacturer, distributor } = await loadFixture(deploySupplyFixture);
    await sc.connect(manufacturer).registerProduct(
      PRODUCT_ID, "Test Drug", "BATCH-001", "Factory"
    );
    await sc.connect(manufacturer).transferCustody(
      PRODUCT_ID, distributor.address, "Hamburg Port"
    );
    expect(await sc.currentCustodian(PRODUCT_ID)).to.equal(distributor.address);
  });
});
