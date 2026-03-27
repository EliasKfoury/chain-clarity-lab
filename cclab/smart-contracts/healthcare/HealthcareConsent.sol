// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title HealthcareConsent
 * @author Elias Kfoury — @chainclar
 * @notice Patient-controlled healthcare data consent on blockchain
 * @dev Implements GDPR-compliant granular consent management
 */
contract HealthcareConsent {

    // ── Data Types ─────────────────────────────────────────────────────
    enum DataType {
        GENERAL,        // 0 - General health records
        PRESCRIPTIONS,  // 1 - Prescription history
        LAB_RESULTS,    // 2 - Laboratory results
        IMAGING,        // 3 - X-ray, MRI, CT scans
        MENTAL_HEALTH,  // 4 - Mental health records
        GENETIC,        // 5 - Genomic / genetic data
        EMERGENCY       // 6 - Emergency access (always allowed)
    }

    struct ConsentGrant {
        address  provider;
        DataType dataType;
        uint256  grantedAt;
        uint256  expiresAt;
        bool     active;
        string   purpose;    // Research, Treatment, Insurance, etc.
    }

    struct Patient {
        bytes32  identityHash;  // Hash of patient identifier (never store raw PII)
        bool     registered;
        uint256  registeredAt;
        address  emergencyContact;
    }

    // ── State ──────────────────────────────────────────────────────────
    mapping(address => Patient)                          public patients;
    mapping(address => ConsentGrant[])                   public consentGrants;
    mapping(address => mapping(address => bool))         public emergencyAccess;

    uint256 public totalPatients;
    uint256 public totalGrants;

    // ── Events ────────────────────────────────────────────────────────
    event PatientRegistered(address indexed patient, bytes32 identityHash);
    event ConsentGranted(
        address indexed patient,
        address indexed provider,
        DataType dataType,
        uint256 expiresAt,
        string  purpose
    );
    event ConsentRevoked(
        address indexed patient,
        address indexed provider,
        uint256 grantIndex
    );
    event EmergencyAccessUsed(
        address indexed provider,
        address indexed patient,
        uint256 timestamp
    );
    event DataAccessed(
        address indexed provider,
        address indexed patient,
        DataType dataType,
        uint256 timestamp
    );

    // ── Modifiers ─────────────────────────────────────────────────────
    modifier onlyRegistered() {
        require(patients[msg.sender].registered, "Patient not registered");
        _;
    }

    // ── Patient Registration ──────────────────────────────────────────
    /**
     * @notice Register as a patient with a hashed identity
     * @param _identityHash keccak256 hash of patient identifier
     * @param _emergencyContact Address of emergency contact / next of kin
     */
    function registerPatient(
        bytes32 _identityHash,
        address _emergencyContact
    ) external {
        require(!patients[msg.sender].registered, "Already registered");
        patients[msg.sender] = Patient({
            identityHash:     _identityHash,
            registered:       true,
            registeredAt:     block.timestamp,
            emergencyContact: _emergencyContact
        });
        totalPatients++;
        emit PatientRegistered(msg.sender, _identityHash);
    }

    // ── Consent Management ────────────────────────────────────────────
    /**
     * @notice Grant a healthcare provider access to specific data type
     * @param _provider Provider's wallet address
     * @param _dataType Type of data to share
     * @param _durationDays How long to grant access (0 = permanent)
     * @param _purpose Why this data is being shared
     */
    function grantConsent(
        address  _provider,
        DataType _dataType,
        uint256  _durationDays,
        string   calldata _purpose
    ) external onlyRegistered {
        require(_provider != address(0), "Invalid provider");
        uint256 expiry = _durationDays > 0
            ? block.timestamp + (_durationDays * 1 days)
            : type(uint256).max;

        consentGrants[msg.sender].push(ConsentGrant({
            provider:  _provider,
            dataType:  _dataType,
            grantedAt: block.timestamp,
            expiresAt: expiry,
            active:    true,
            purpose:   _purpose
        }));
        totalGrants++;
        emit ConsentGranted(msg.sender, _provider, _dataType, expiry, _purpose);
    }

    /**
     * @notice Revoke a consent grant immediately
     * @param _grantIndex Index of the grant to revoke
     */
    function revokeConsent(uint256 _grantIndex) external onlyRegistered {
        require(_grantIndex < consentGrants[msg.sender].length, "Invalid index");
        ConsentGrant storage grant = consentGrants[msg.sender][_grantIndex];
        require(grant.active, "Already revoked");
        grant.active = false;
        emit ConsentRevoked(msg.sender, grant.provider, _grantIndex);
    }

    /**
     * @notice Check if a provider has valid access to patient data
     * @param _patient Patient address
     * @param _provider Provider address
     * @param _dataType Data type to check
     */
    function hasAccess(
        address  _patient,
        address  _provider,
        DataType _dataType
    ) public view returns (bool) {
        // Emergency access always granted
        if (_dataType == DataType.EMERGENCY) return true;

        ConsentGrant[] storage grants = consentGrants[_patient];
        for (uint256 i = 0; i < grants.length; i++) {
            ConsentGrant storage g = grants[i];
            if (
                g.provider  == _provider &&
                g.dataType  == _dataType &&
                g.active                 &&
                block.timestamp <= g.expiresAt
            ) {
                return true;
            }
        }
        return false;
    }

    /**
     * @notice Log a data access event (called by provider's system)
     * @param _patient Patient whose data was accessed
     * @param _dataType Type of data accessed
     */
    function logDataAccess(
        address  _patient,
        DataType _dataType
    ) external {
        require(
            hasAccess(_patient, msg.sender, _dataType),
            "No consent for this access"
        );
        emit DataAccessed(msg.sender, _patient, _dataType, block.timestamp);
    }

    // ── View Functions ────────────────────────────────────────────────
    function getConsentCount(address _patient) external view returns (uint256) {
        return consentGrants[_patient].length;
    }

    function getActiveGrants(address _patient)
        external view returns (uint256[] memory activeIndexes)
    {
        ConsentGrant[] storage grants = consentGrants[_patient];
        uint256 count = 0;
        for (uint256 i = 0; i < grants.length; i++) {
            if (grants[i].active && block.timestamp <= grants[i].expiresAt) count++;
        }
        activeIndexes = new uint256[](count);
        uint256 j = 0;
        for (uint256 i = 0; i < grants.length; i++) {
            if (grants[i].active && block.timestamp <= grants[i].expiresAt) {
                activeIndexes[j++] = i;
            }
        }
    }
}
