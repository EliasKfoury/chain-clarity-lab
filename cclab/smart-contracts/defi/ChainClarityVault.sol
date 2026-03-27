// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ChainClarityVault
 * @author Elias Kfoury — @chainclar
 * @notice Simple DeFi yield vault — deposit ETH, earn yield, withdraw anytime
 * @dev Educational implementation — NOT for production use without audit
 */
contract ChainClarityVault {

    address public owner;
    uint256 public totalDeposits;
    uint256 public yieldRateBPS;   // basis points per year (100 = 1%)
    uint256 public constant BPS_DENOMINATOR = 10000;
    uint256 public constant SECONDS_PER_YEAR = 365 days;

    struct Position {
        uint256 amount;
        uint256 depositTime;
        uint256 lastClaimTime;
    }

    mapping(address => Position) public positions;
    address[] public depositors;

    // ── Events ────────────────────────────────────────────────────────
    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount, uint256 yield);
    event YieldClaimed(address indexed user, uint256 yield);
    event YieldRateUpdated(uint256 oldRate, uint256 newRate);

    modifier onlyOwner() { require(msg.sender == owner, "Not owner"); _; }

    constructor(uint256 _yieldRateBPS) {
        owner        = msg.sender;
        yieldRateBPS = _yieldRateBPS; // e.g. 500 = 5% APY
    }

    // ── Core Functions ────────────────────────────────────────────────
    /**
     * @notice Deposit ETH into the vault
     */
    function deposit() external payable {
        require(msg.value > 0, "Must deposit ETH");

        Position storage pos = positions[msg.sender];
        if (pos.amount > 0) {
            // Claim pending yield before adding to position
            _claimYield(msg.sender);
        } else {
            depositors.push(msg.sender);
            pos.depositTime  = block.timestamp;
            pos.lastClaimTime = block.timestamp;
        }

        pos.amount    += msg.value;
        totalDeposits += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    /**
     * @notice Withdraw full position including yield
     */
    function withdraw() external {
        Position storage pos = positions[msg.sender];
        require(pos.amount > 0, "No position");

        uint256 pendingYield = _calculateYield(msg.sender);
        uint256 totalReturn  = pos.amount + pendingYield;

        totalDeposits -= pos.amount;
        delete positions[msg.sender];

        require(address(this).balance >= totalReturn, "Insufficient vault balance");
        payable(msg.sender).transfer(totalReturn);
        emit Withdrawn(msg.sender, pos.amount, pendingYield);
    }

    /**
     * @notice Claim yield without withdrawing principal
     */
    function claimYield() external {
        require(positions[msg.sender].amount > 0, "No position");
        _claimYield(msg.sender);
    }

    // ── View Functions ────────────────────────────────────────────────
    function getPendingYield(address _user) external view returns (uint256) {
        return _calculateYield(_user);
    }

    function getPosition(address _user) external view returns (
        uint256 amount, uint256 depositTime, uint256 pendingYield
    ) {
        Position storage pos = positions[_user];
        return (pos.amount, pos.depositTime, _calculateYield(_user));
    }

    function getTotalValueLocked() external view returns (uint256) {
        return address(this).balance;
    }

    // ── Owner Functions ───────────────────────────────────────────────
    function updateYieldRate(uint256 _newRateBPS) external onlyOwner {
        emit YieldRateUpdated(yieldRateBPS, _newRateBPS);
        yieldRateBPS = _newRateBPS;
    }

    function fundVault() external payable onlyOwner {}

    // ── Internal ──────────────────────────────────────────────────────
    function _calculateYield(address _user) internal view returns (uint256) {
        Position storage pos = positions[_user];
        if (pos.amount == 0) return 0;
        uint256 elapsed = block.timestamp - pos.lastClaimTime;
        return (pos.amount * yieldRateBPS * elapsed) / (BPS_DENOMINATOR * SECONDS_PER_YEAR);
    }

    function _claimYield(address _user) internal {
        uint256 yield = _calculateYield(_user);
        if (yield > 0 && address(this).balance >= yield) {
            positions[_user].lastClaimTime = block.timestamp;
            payable(_user).transfer(yield);
            emit YieldClaimed(_user, yield);
        }
    }

    receive() external payable {}
}
