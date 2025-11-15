// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

/// @title FreelanceCreditScorer
/// @notice Aggregates multi-platform freelance payment history to produce
///         a deterministic credit decision that can be replayed on Arc testnet.
/// @dev Heuristics are intentionally transparent so off-chain services (such as
///      the Gmail CSV parser from https://github.com/JeremyC53/Encode_Hackathon_Loan_ShArc)
///      can mirror the same scoring logic before submitting to the contract.
contract FreelanceCreditScorer {
    /// @dev Arc testnet USDC ERC-20 interface address (6 decimals) as documented here:
    ///      https://docs.arc.network/arc/references/contract-addresses
    address public constant ARC_TESTNET_USDC = 0x3600000000000000000000000000000000000000;

    uint256 private constant BASIS_POINTS = 10_000;
    uint256 private constant MAX_SCORE = 1_000;

    struct PlatformReceipt {
        bytes32 platformId; // keccak256("upwork"), etc.
        uint256 totalEarnedUsdc; // 6 decimals, denominated in USDC
        uint16 csvSampleCount; // number of CSV rows parsed from Gmail exports
        uint40 lastPayoutEpoch; // unix timestamp for freshest CSV entry
        uint16 onTimeRatioBps; // punctual payout ratio scaled by 10_000
    }

    struct FreelanceHistory {
        PlatformReceipt[] platforms;
        uint256 lookbackMonths;
        uint40 snapshotTimestamp; // unix timestamp when the CSV snapshot was assembled
    }

    struct CreditDecision {
        uint256 creditScore; // 0 - 1_000
        uint256 borrowingLimit; // denominated in USDC (6 decimals)
        uint256 aprBps; // APR expressed in basis points
        uint256 repaymentPeriodDays; // total repayment duration
        uint256 repaymentCount; // number of equal installments
    }

    mapping(address => CreditDecision) public lastDecision;

    event CreditDecisionGenerated(
        address indexed freelancer,
        uint256 creditScore,
        uint256 borrowingLimit,
        uint256 aprBps
    );

    error InvalidHistory();

    function evaluateAndStore(
        FreelanceHistory calldata history
    ) external returns (CreditDecision memory decision) {
        decision = _buildDecision(history);
        lastDecision[msg.sender] = decision;
        emit CreditDecisionGenerated(
            msg.sender,
            decision.creditScore,
            decision.borrowingLimit,
            decision.aprBps
        );
    }

    function getLastDecision(
        address user
    ) external view returns (CreditDecision memory decision) {
        decision = lastDecision[user];
    }

    function previewDecision(
        FreelanceHistory calldata history
    ) external pure returns (CreditDecision memory decision) {
        decision = _buildDecision(history);
    }

    function _buildDecision(
        FreelanceHistory calldata history
    ) private pure returns (CreditDecision memory decision) {
        uint256 platformCount = history.platforms.length;
        if (
            platformCount == 0 ||
            history.lookbackMonths == 0 ||
            history.snapshotTimestamp == 0
        ) revert InvalidHistory();

        uint256 totalVolume;
        uint256 weightedOnTime;
        uint256 totalSamples;
        uint40 freshestPayout;

        for (uint256 i = 0; i < platformCount; i++) {
            PlatformReceipt calldata receipt = history.platforms[i];
            totalVolume += receipt.totalEarnedUsdc;
            weightedOnTime +=
                uint256(receipt.onTimeRatioBps) *
                receipt.totalEarnedUsdc;
            totalSamples += receipt.csvSampleCount;
            if (receipt.lastPayoutEpoch > freshestPayout) {
                freshestPayout = receipt.lastPayoutEpoch;
            }
        }

        uint256 avgMonthlyIncome = totalVolume / history.lookbackMonths;
        uint256 avgOnTimeBps = totalVolume == 0
            ? BASIS_POINTS
            : weightedOnTime / totalVolume;

        uint256 finalScore = _cap(
            (avgMonthlyIncome / 1e6) * 12,
            400
        );

        finalScore += _cap(history.lookbackMonths * 12, 150);
        finalScore += _cap(platformCount * 70, 200);
        finalScore += _cap((avgOnTimeBps * 150) / BASIS_POINTS, 150);
        finalScore += _cap(totalSamples * 5, 150);
        finalScore += _freshnessScore(history.snapshotTimestamp, freshestPayout);

        if (finalScore > MAX_SCORE) {
            finalScore = MAX_SCORE;
        }

        uint256 borrowingLimit = (totalVolume * 40) / 100;
        uint256 aprBps = _deriveApr(finalScore);
        (uint256 repaymentPeriodDays, uint256 repaymentCount) = _schedule(finalScore);

        decision = CreditDecision({
            creditScore: finalScore,
            borrowingLimit: borrowingLimit,
            aprBps: aprBps,
            repaymentPeriodDays: repaymentPeriodDays,
            repaymentCount: repaymentCount
        });
    }

    function _freshnessScore(
        uint40 snapshotTimestamp,
        uint40 lastPayoutEpoch
    ) private pure returns (uint256) {
        if (lastPayoutEpoch == 0 || snapshotTimestamp <= lastPayoutEpoch) {
            return 150;
        }
        uint256 daysStale = (snapshotTimestamp - lastPayoutEpoch) / 1 days;
        if (daysStale >= 90) {
            return 0;
        }
        uint256 penalty = (daysStale * 150) / 90;
        return 150 - penalty;
    }

    function _deriveApr(uint256 score) private pure returns (uint256) {
        uint256 aprReduction = (score * 1_500) / MAX_SCORE;
        uint256 aprBps = 2_500 - aprReduction;
        if (aprBps < 500) {
            aprBps = 500;
        }
        return aprBps;
    }

    function _schedule(
        uint256 score
    ) private pure returns (uint256 totalDays, uint256 installments) {
        if (score >= 800) {
            installments = 6;
        } else if (score >= 650) {
            installments = 4;
        } else {
            installments = 3;
        }
        totalDays = installments * 30;
    }

    function _cap(uint256 value, uint256 maxValue) private pure returns (uint256) {
        return value > maxValue ? maxValue : value;
    }
}

