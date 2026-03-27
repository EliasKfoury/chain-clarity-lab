// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SupplyChainTracker
 * @author Elias Kfoury — @chainclar
 * @notice End-to-end product tracking on blockchain
 * @dev Tracks products from manufacturer to end consumer with IoT data support
 */
contract SupplyChainTracker {

    enum ProductStatus {
        MANUFACTURED,   // 0
        IN_TRANSIT,     // 1
        AT_WAREHOUSE,   // 2
        AT_CUSTOMS,     // 3
        OUT_FOR_DELIVERY, // 4
        DELIVERED,      // 5
        RECALLED        // 6
    }

    struct Product {
        bytes32       productId;
        string        name;
        string        batchNumber;
        address       manufacturer;
        uint256       manufacturedAt;
        ProductStatus status;
        bool          isAuthentic;
        bool          recalled;
    }

    struct TrackingEvent {
        address       actor;
        ProductStatus status;
        string        location;
        uint256       timestamp;
        int256        temperature;   // in celsius * 100 (e.g., 2500 = 25.00°C)
        uint256       humidity;      // percentage
        string        notes;
    }

    struct CustodyTransfer {
        address from;
        address to;
        uint256 timestamp;
        string  location;
    }

    // ── State ──────────────────────────────────────────────────────────
    mapping(bytes32 => Product)          public products;
    mapping(bytes32 => TrackingEvent[])  public trackingHistory;
    mapping(bytes32 => CustodyTransfer[]) public custodyChain;
    mapping(bytes32 => address)          public currentCustodian;
    mapping(address => bool)             public authorizedActors;

    address public owner;
    uint256 public totalProducts;

    // ── Events ────────────────────────────────────────────────────────
    event ProductRegistered(bytes32 indexed productId, address manufacturer, string name);
    event StatusUpdated(bytes32 indexed productId, ProductStatus status, address actor);
    event CustodyTransferred(bytes32 indexed productId, address from, address to);
    event ProductRecalled(bytes32 indexed productId, string reason);
    event CounterfeitDetected(bytes32 indexed productId, address reportedBy);

    modifier onlyOwner()           { require(msg.sender == owner, "Not owner"); _; }
    modifier onlyAuthorized()      { require(authorizedActors[msg.sender] || msg.sender == owner, "Not authorized"); _; }
    modifier productExists(bytes32 _id) { require(products[_id].manufacturer != address(0), "Product not found"); _; }

    constructor() { owner = msg.sender; authorizedActors[msg.sender] = true; }

    // ── Actor Management ──────────────────────────────────────────────
    function authorizeActor(address _actor)   external onlyOwner { authorizedActors[_actor] = true;  }
    function deauthorizeActor(address _actor) external onlyOwner { authorizedActors[_actor] = false; }

    // ── Product Registration ──────────────────────────────────────────
    /**
     * @notice Register a new product on the blockchain
     */
    function registerProduct(
        bytes32 _productId,
        string  calldata _name,
        string  calldata _batchNumber,
        string  calldata _originLocation
    ) external onlyAuthorized {
        require(products[_productId].manufacturer == address(0), "Product already registered");

        products[_productId] = Product({
            productId:       _productId,
            name:            _name,
            batchNumber:     _batchNumber,
            manufacturer:    msg.sender,
            manufacturedAt:  block.timestamp,
            status:          ProductStatus.MANUFACTURED,
            isAuthentic:     true,
            recalled:        false
        });

        currentCustodian[_productId] = msg.sender;
        totalProducts++;

        // Log initial event
        trackingHistory[_productId].push(TrackingEvent({
            actor:       msg.sender,
            status:      ProductStatus.MANUFACTURED,
            location:    _originLocation,
            timestamp:   block.timestamp,
            temperature: 0,
            humidity:    0,
            notes:       "Product manufactured and registered on blockchain"
        }));

        emit ProductRegistered(_productId, msg.sender, _name);
    }

    // ── Tracking Updates ──────────────────────────────────────────────
    /**
     * @notice Update product status with IoT sensor data
     */
    function updateStatus(
        bytes32       _productId,
        ProductStatus _newStatus,
        string        calldata _location,
        int256        _temperature,
        uint256       _humidity,
        string        calldata _notes
    ) external onlyAuthorized productExists(_productId) {
        require(!products[_productId].recalled, "Product is recalled");
        require(
            msg.sender == currentCustodian[_productId] || msg.sender == owner,
            "Not current custodian"
        );

        products[_productId].status = _newStatus;

        trackingHistory[_productId].push(TrackingEvent({
            actor:       msg.sender,
            status:      _newStatus,
            location:    _location,
            timestamp:   block.timestamp,
            temperature: _temperature,
            humidity:    _humidity,
            notes:       _notes
        }));

        emit StatusUpdated(_productId, _newStatus, msg.sender);
    }

    /**
     * @notice Transfer custody to next party in supply chain
     */
    function transferCustody(
        bytes32 _productId,
        address _newCustodian,
        string  calldata _location
    ) external productExists(_productId) {
        require(msg.sender == currentCustodian[_productId], "Not custodian");
        require(_newCustodian != address(0), "Invalid address");

        custodyChain[_productId].push(CustodyTransfer({
            from:      msg.sender,
            to:        _newCustodian,
            timestamp: block.timestamp,
            location:  _location
        }));

        currentCustodian[_productId] = _newCustodian;
        emit CustodyTransferred(_productId, msg.sender, _newCustodian);
    }

    /**
     * @notice Recall a product — marks as unsafe
     */
    function recallProduct(bytes32 _productId, string calldata _reason)
        external onlyOwner productExists(_productId)
    {
        products[_productId].recalled = true;
        products[_productId].status   = ProductStatus.RECALLED;
        emit ProductRecalled(_productId, _reason);
    }

    // ── Anti-Counterfeit ──────────────────────────────────────────────
    /**
     * @notice Verify product authenticity — returns full provenance
     */
    function verifyProduct(bytes32 _productId) external view returns (
        bool   isRegistered,
        bool   isAuthentic,
        bool   isRecalled,
        address manufacturer,
        uint256 manufacturedAt,
        ProductStatus status,
        uint256 trackingEventCount,
        uint256 custodyTransferCount
    ) {
        Product storage p = products[_productId];
        return (
            p.manufacturer != address(0),
            p.isAuthentic,
            p.recalled,
            p.manufacturer,
            p.manufacturedAt,
            p.status,
            trackingHistory[_productId].length,
            custodyChain[_productId].length
        );
    }

    function getTrackingHistory(bytes32 _productId)
        external view returns (TrackingEvent[] memory)
    {
        return trackingHistory[_productId];
    }

    function getCustodyChain(bytes32 _productId)
        external view returns (CustodyTransfer[] memory)
    {
        return custodyChain[_productId];
    }
}
