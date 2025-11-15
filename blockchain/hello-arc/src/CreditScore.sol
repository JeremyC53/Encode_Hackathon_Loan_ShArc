// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

/// @title FreelancerCreditScore
/// @notice Stores off-chain computed credit scores on-chain for verification
contract CreditScore {
    /// @notice Address allowed to update scores (your backend wallet)
    address public admin;

    /// @notice creditScore[user] = current credit score (e.g. 300–900)
    mapping(address => uint256) private creditScore;

    /// @notice lastUpdated[user] = timestamp when score was last written
    mapping(address => uint256) public lastUpdated;

    /// @notice Emitted whenever a score is updated
    event CreditScoreUpdated(address indexed user, uint256 score, uint256 timestamp);

    constructor() {
        admin = msg.sender;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Not authorized");
        _;
    }

    /// @notice Change the admin (e.g. rotate backend wallet if needed)
    function setAdmin(address _newAdmin) external onlyAdmin {
        require(_newAdmin != address(0), "Invalid admin");
        admin = _newAdmin;
    }

    /// @notice Store/update the credit score for a freelancer
    /// @dev Call this from your backend after you calculate the score off-chain
    /// @param user The freelancer's wallet address
    /// @param score The computed credit score (e.g. 300–900)
    function setCreditScore(address user, uint256 score) external onlyAdmin {
        require(user != address(0), "Invalid user");
        require(score > 0, "Score must be > 0");

        creditScore[user] = score;
        lastUpdated[user] = block.timestamp;

        emit CreditScoreUpdated(user, score, block.timestamp);
    }

    /// @notice Read the current score + last updated time for a user
    function getCreditScore(address user)
        external
        view
        returns (uint256 score, uint256 updatedAt)
    {
        score = creditScore[user];
        updatedAt = lastUpdated[user];
    }
}
