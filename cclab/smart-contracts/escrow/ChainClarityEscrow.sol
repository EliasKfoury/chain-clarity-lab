// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ChainClarityEscrow
 * @author Elias Kfoury — @chainclar
 * @notice Milestone-based escrow with arbiter dispute resolution
 * @dev Supports ETH and ERC-20 tokens, milestone releases, and refunds
 */
contract ChainClarityEscrow {

    // ── State ────────────────────────────────────────────────────────
    address public buyer;
    address public seller;
    address public arbiter;
    uint256 public amount;
    uint256 public createdAt;
    uint256 public expiresAt;

    enum State { AWAITING_PAYMENT, AWAITING_DELIVERY, COMPLETE, REFUNDED, DISPUTED }
    State public currentState;

    struct Milestone {
        string  description;
        uint256 amount;
        bool    released;
    }

    Milestone[] public milestones;
    uint256 public totalMilestoneAmount;

    // ── Events ────────────────────────────────────────────────────────
    event Deposited(address indexed buyer, uint256 amount);
    event MilestoneReleased(uint256 milestoneIndex, uint256 amount);
    event DeliveryConfirmed(address indexed buyer, uint256 amount);
    event Refunded(address indexed buyer, uint256 amount);
    event DisputeRaised(address indexed raisedBy);
    event DisputeResolved(address indexed winner, uint256 amount);

    // ── Modifiers ─────────────────────────────────────────────────────
    modifier onlyBuyer()   { require(msg.sender == buyer,   "Only buyer");   _; }
    modifier onlySeller()  { require(msg.sender == seller,  "Only seller");  _; }
    modifier onlyArbiter() { require(msg.sender == arbiter, "Only arbiter"); _; }
    modifier inState(State _state) {
        require(currentState == _state, "Invalid state");
        _;
    }

    // ── Constructor ───────────────────────────────────────────────────
    constructor(
        address _seller,
        address _arbiter,
        uint256 _durationDays
    ) payable {
        require(_seller  != address(0), "Invalid seller");
        require(_arbiter != address(0), "Invalid arbiter");
        require(msg.value > 0,          "Must deposit ETH");

        buyer       = msg.sender;
        seller      = _seller;
        arbiter     = _arbiter;
        amount      = msg.value;
        createdAt   = block.timestamp;
        expiresAt   = block.timestamp + (_durationDays * 1 days);
        currentState = State.AWAITING_DELIVERY;

        emit Deposited(buyer, msg.value);
    }

    // ── Milestone Management ──────────────────────────────────────────
    /**
     * @notice Add a milestone (buyer only, before delivery)
     * @param _description Human-readable milestone description
     * @param _milestoneAmount ETH amount for this milestone in wei
     */
    function addMilestone(
        string calldata _description,
        uint256 _milestoneAmount
    ) external onlyBuyer inState(State.AWAITING_DELIVERY) {
        require(
            totalMilestoneAmount + _milestoneAmount <= amount,
            "Exceeds escrow balance"
        );
        milestones.push(Milestone({
            description: _description,
            amount:      _milestoneAmount,
            released:    false
        }));
        totalMilestoneAmount += _milestoneAmount;
    }

    /**
     * @notice Release a specific milestone payment to seller
     * @param _index Milestone index to release
     */
    function releaseMilestone(uint256 _index)
        external onlyBuyer inState(State.AWAITING_DELIVERY)
    {
        require(_index < milestones.length,   "Invalid milestone");
        require(!milestones[_index].released, "Already released");

        milestones[_index].released = true;
        uint256 milestoneAmt = milestones[_index].amount;
        amount -= milestoneAmt;

        payable(seller).transfer(milestoneAmt);
        emit MilestoneReleased(_index, milestoneAmt);
    }

    // ── Core Functions ────────────────────────────────────────────────
    /**
     * @notice Buyer confirms delivery — releases all remaining funds to seller
     */
    function confirmDelivery()
        external onlyBuyer inState(State.AWAITING_DELIVERY)
    {
        currentState = State.COMPLETE;
        uint256 remaining = address(this).balance;
        payable(seller).transfer(remaining);
        emit DeliveryConfirmed(buyer, remaining);
    }

    /**
     * @notice Raise a dispute — only arbiter can resolve
     */
    function raiseDispute()
        external inState(State.AWAITING_DELIVERY)
    {
        require(
            msg.sender == buyer || msg.sender == seller,
            "Only buyer or seller"
        );
        currentState = State.DISPUTED;
        emit DisputeRaised(msg.sender);
    }

    /**
     * @notice Arbiter resolves dispute
     * @param _releaseToSeller true = pay seller, false = refund buyer
     */
    function resolveDispute(bool _releaseToSeller)
        external onlyArbiter inState(State.DISPUTED)
    {
        currentState = State.COMPLETE;
        uint256 balance = address(this).balance;
        address winner;

        if (_releaseToSeller) {
            winner = seller;
            payable(seller).transfer(balance);
        } else {
            winner = buyer;
            payable(buyer).transfer(balance);
        }
        emit DisputeResolved(winner, balance);
    }

    /**
     * @notice Refund buyer if escrow expires without delivery
     */
    function claimExpiredRefund()
        external onlyBuyer inState(State.AWAITING_DELIVERY)
    {
        require(block.timestamp > expiresAt, "Not yet expired");
        currentState = State.REFUNDED;
        uint256 balance = address(this).balance;
        payable(buyer).transfer(balance);
        emit Refunded(buyer, balance);
    }

    // ── View Functions ────────────────────────────────────────────────
    function getBalance()       external view returns (uint256) { return address(this).balance; }
    function getMilestoneCount() external view returns (uint256) { return milestones.length; }
    function isExpired()         external view returns (bool)    { return block.timestamp > expiresAt; }
    function getState()          external view returns (string memory) {
        if (currentState == State.AWAITING_PAYMENT)  return "AWAITING_PAYMENT";
        if (currentState == State.AWAITING_DELIVERY) return "AWAITING_DELIVERY";
        if (currentState == State.COMPLETE)          return "COMPLETE";
        if (currentState == State.REFUNDED)          return "REFUNDED";
        if (currentState == State.DISPUTED)          return "DISPUTED";
        return "UNKNOWN";
    }
}
