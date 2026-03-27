// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ChainClarityDAO
 * @author Elias Kfoury — @chainclar
 * @notice Decentralised governance voting contract
 * @dev Token-weighted voting with time-locked execution
 */
contract ChainClarityDAO {

    enum ProposalState { PENDING, ACTIVE, PASSED, FAILED, EXECUTED, CANCELLED }

    struct Proposal {
        uint256       id;
        address       proposer;
        string        title;
        string        description;
        uint256       votesFor;
        uint256       votesAgainst;
        uint256       votesAbstain;
        uint256       startTime;
        uint256       endTime;
        ProposalState state;
        bool          executed;
        bytes         callData;      // Encoded function call for execution
        address       targetContract;
    }

    struct Vote {
        bool    hasVoted;
        uint8   support;   // 0=Against, 1=For, 2=Abstain
        uint256 weight;
    }

    // ── State ──────────────────────────────────────────────────────────
    address public owner;
    address public governanceToken;
    uint256 public proposalCount;
    uint256 public votingDuration   = 7 days;
    uint256 public quorumPercentage = 10;   // 10% of total supply must vote
    uint256 public passingThreshold = 51;   // 51% of votes must be FOR

    mapping(uint256 => Proposal)              public proposals;
    mapping(uint256 => mapping(address => Vote)) public votes;
    mapping(address => uint256)               public votingPower;  // simplified — use snapshot in production

    // ── Events ────────────────────────────────────────────────────────
    event ProposalCreated(uint256 indexed id, address proposer, string title);
    event VoteCast(uint256 indexed proposalId, address voter, uint8 support, uint256 weight);
    event ProposalExecuted(uint256 indexed id);
    event ProposalCancelled(uint256 indexed id);

    modifier onlyOwner() { require(msg.sender == owner, "Not owner"); _; }

    constructor(address _governanceToken) {
        owner           = msg.sender;
        governanceToken = _governanceToken;
    }

    // ── Governance Token Power ────────────────────────────────────────
    function setVotingPower(address _voter, uint256 _power) external onlyOwner {
        votingPower[_voter] = _power;
    }

    // ── Proposal Management ───────────────────────────────────────────
    /**
     * @notice Create a new governance proposal
     */
    function createProposal(
        string  calldata _title,
        string  calldata _description,
        address _targetContract,
        bytes   calldata _callData
    ) external returns (uint256 proposalId) {
        require(votingPower[msg.sender] > 0, "Must hold governance tokens");

        proposalId = ++proposalCount;
        proposals[proposalId] = Proposal({
            id:              proposalId,
            proposer:        msg.sender,
            title:           _title,
            description:     _description,
            votesFor:        0,
            votesAgainst:    0,
            votesAbstain:    0,
            startTime:       block.timestamp,
            endTime:         block.timestamp + votingDuration,
            state:           ProposalState.ACTIVE,
            executed:        false,
            callData:        _callData,
            targetContract:  _targetContract
        });

        emit ProposalCreated(proposalId, msg.sender, _title);
    }

    /**
     * @notice Cast a vote on an active proposal
     * @param _proposalId ID of the proposal
     * @param _support 0=Against, 1=For, 2=Abstain
     */
    function castVote(uint256 _proposalId, uint8 _support) external {
        require(_support <= 2, "Invalid vote type");
        Proposal storage p = proposals[_proposalId];
        require(p.state == ProposalState.ACTIVE,  "Not active");
        require(block.timestamp <= p.endTime,     "Voting ended");
        require(!votes[_proposalId][msg.sender].hasVoted, "Already voted");

        uint256 weight = votingPower[msg.sender];
        require(weight > 0, "No voting power");

        votes[_proposalId][msg.sender] = Vote({
            hasVoted: true,
            support:  _support,
            weight:   weight
        });

        if      (_support == 1) p.votesFor     += weight;
        else if (_support == 0) p.votesAgainst += weight;
        else                    p.votesAbstain  += weight;

        emit VoteCast(_proposalId, msg.sender, _support, weight);
    }

    /**
     * @notice Finalise proposal after voting period ends
     */
    function finaliseProposal(uint256 _proposalId) external {
        Proposal storage p = proposals[_proposalId];
        require(p.state == ProposalState.ACTIVE,  "Not active");
        require(block.timestamp > p.endTime,       "Voting ongoing");

        uint256 totalVotes = p.votesFor + p.votesAgainst + p.votesAbstain;
        bool quorumMet  = totalVotes >= _getQuorumThreshold();
        bool majorityFor = totalVotes > 0 &&
            (p.votesFor * 100 / totalVotes) >= passingThreshold;

        p.state = (quorumMet && majorityFor)
            ? ProposalState.PASSED
            : ProposalState.FAILED;
    }

    /**
     * @notice Execute a passed proposal
     */
    function executeProposal(uint256 _proposalId) external onlyOwner {
        Proposal storage p = proposals[_proposalId];
        require(p.state == ProposalState.PASSED,   "Not passed");
        require(!p.executed,                        "Already executed");
        require(p.targetContract != address(0),     "No target");

        p.executed = true;
        p.state    = ProposalState.EXECUTED;

        (bool success, ) = p.targetContract.call(p.callData);
        require(success, "Execution failed");

        emit ProposalExecuted(_proposalId);
    }

    // ── View Functions ────────────────────────────────────────────────
    function getProposalResult(uint256 _proposalId) external view returns (
        uint256 votesFor,
        uint256 votesAgainst,
        uint256 votesAbstain,
        uint256 totalVotes,
        bool    quorumMet,
        bool    passed
    ) {
        Proposal storage p = proposals[_proposalId];
        totalVotes  = p.votesFor + p.votesAgainst + p.votesAbstain;
        quorumMet   = totalVotes >= _getQuorumThreshold();
        bool majority = totalVotes > 0 &&
            (p.votesFor * 100 / totalVotes) >= passingThreshold;
        return (p.votesFor, p.votesAgainst, p.votesAbstain, totalVotes, quorumMet, quorumMet && majority);
    }

    function _getQuorumThreshold() internal view returns (uint256) {
        // Simplified — in production use ERC-20 total supply snapshot
        return 1000 * quorumPercentage / 100;
    }

    function updateVotingParams(
        uint256 _duration,
        uint256 _quorum,
        uint256 _threshold
    ) external onlyOwner {
        votingDuration   = _duration;
        quorumPercentage = _quorum;
        passingThreshold = _threshold;
    }
}
