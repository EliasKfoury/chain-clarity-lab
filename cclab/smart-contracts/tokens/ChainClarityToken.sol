// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ChainClarityToken (CCT)
 * @author Elias Kfoury — @chainclar
 * @notice ERC-20 token with minting, burning, and pause functionality
 */
contract ChainClarityToken {

    // ── ERC-20 State ──────────────────────────────────────────────────
    string  public name     = "Chain Clarity Token";
    string  public symbol   = "CCT";
    uint8   public decimals = 18;
    uint256 public totalSupply;
    address public owner;
    bool    public paused;

    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;

    // ── Events ────────────────────────────────────────────────────────
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Mint(address indexed to, uint256 amount);
    event Burn(address indexed from, uint256 amount);
    event Paused(address indexed by);
    event Unpaused(address indexed by);

    // ── Modifiers ─────────────────────────────────────────────────────
    modifier onlyOwner()  { require(msg.sender == owner,  "Not owner");  _; }
    modifier whenActive() { require(!paused,               "Paused");    _; }

    // ── Constructor ───────────────────────────────────────────────────
    constructor(uint256 _initialSupply) {
        owner = msg.sender;
        _mint(msg.sender, _initialSupply * 10 ** decimals);
    }

    // ── ERC-20 Core ───────────────────────────────────────────────────
    function transfer(address _to, uint256 _value)
        external whenActive returns (bool)
    {
        require(_to != address(0),           "Zero address");
        require(balanceOf[msg.sender] >= _value, "Insufficient balance");
        balanceOf[msg.sender] -= _value;
        balanceOf[_to]        += _value;
        emit Transfer(msg.sender, _to, _value);
        return true;
    }

    function approve(address _spender, uint256 _value)
        external returns (bool)
    {
        allowance[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }

    function transferFrom(address _from, address _to, uint256 _value)
        external whenActive returns (bool)
    {
        require(balanceOf[_from] >= _value,              "Insufficient balance");
        require(allowance[_from][msg.sender] >= _value,  "Insufficient allowance");
        allowance[_from][msg.sender] -= _value;
        balanceOf[_from]             -= _value;
        balanceOf[_to]               += _value;
        emit Transfer(_from, _to, _value);
        return true;
    }

    // ── Owner Functions ───────────────────────────────────────────────
    function mint(address _to, uint256 _amount) external onlyOwner {
        _mint(_to, _amount);
    }

    function burn(uint256 _amount) external {
        require(balanceOf[msg.sender] >= _amount, "Insufficient balance");
        balanceOf[msg.sender] -= _amount;
        totalSupply           -= _amount;
        emit Burn(msg.sender, _amount);
        emit Transfer(msg.sender, address(0), _amount);
    }

    function pause()   external onlyOwner { paused = true;  emit Paused(msg.sender);   }
    function unpause() external onlyOwner { paused = false; emit Unpaused(msg.sender); }

    function transferOwnership(address _newOwner) external onlyOwner {
        require(_newOwner != address(0), "Zero address");
        owner = _newOwner;
    }

    // ── Internal ──────────────────────────────────────────────────────
    function _mint(address _to, uint256 _amount) internal {
        balanceOf[_to] += _amount;
        totalSupply    += _amount;
        emit Mint(_to, _amount);
        emit Transfer(address(0), _to, _amount);
    }
}
