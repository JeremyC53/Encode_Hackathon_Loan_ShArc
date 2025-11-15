// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "forge-std/Test.sol";
import "../src/FreelanceCreditScorer.sol";

contract FreelanceCreditScorerTest is Test {
    FreelanceCreditScorer private scorer;

    function setUp() public {
        scorer = new FreelanceCreditScorer();
    }

    function testEvaluateAndStoreDecision() public {
        FreelanceCreditScorer.FreelanceHistory memory history = _richHistory();

        vm.expectEmit(false, true, false, false);
        emit FreelanceCreditScorer.CreditDecisionGenerated(
            address(this),
            0,
            0,
            0
        );

        FreelanceCreditScorer.CreditDecision memory decision = scorer
            .evaluateAndStore(history);

        assertGe(decision.creditScore, 700);
        assertLe(decision.aprBps, 1500);
        assertEq(decision.repaymentCount, 6);
        assertEq(decision.repaymentPeriodDays, 180);

        FreelanceCreditScorer.CreditDecision memory stored = scorer.getLastDecision(
            address(this)
        );
        assertEq(stored.creditScore, decision.creditScore);
        assertEq(stored.borrowingLimit, decision.borrowingLimit);
    }

    function testPreviewMatchesEvaluate() public {
        FreelanceCreditScorer.FreelanceHistory memory history = _leanHistory();

        FreelanceCreditScorer.CreditDecision memory preview = scorer.previewDecision(
            history
        );
        FreelanceCreditScorer.CreditDecision memory stored = scorer.evaluateAndStore(
            history
        );

        assertEq(preview.creditScore, stored.creditScore);
        assertEq(preview.borrowingLimit, stored.borrowingLimit);
        assertEq(preview.aprBps, stored.aprBps);
    }

    function testRevertsWithoutPlatforms() public {
        FreelanceCreditScorer.PlatformReceipt[] memory receipts = new FreelanceCreditScorer.PlatformReceipt[](
            0
        );
        FreelanceCreditScorer.FreelanceHistory memory history = FreelanceCreditScorer
            .FreelanceHistory({
            platforms: receipts,
            lookbackMonths: 12,
            snapshotTimestamp: 1_700_000_000
        });

        vm.expectRevert(FreelanceCreditScorer.InvalidHistory.selector);
        scorer.evaluateAndStore(history);
    }

    function _richHistory()
        internal
        pure
        returns (FreelanceCreditScorer.FreelanceHistory memory history)
    {
        FreelanceCreditScorer.PlatformReceipt[] memory receipts = new FreelanceCreditScorer.PlatformReceipt[](
            3
        );

        receipts[0] = FreelanceCreditScorer.PlatformReceipt({
            platformId: keccak256("upwork"),
            totalEarnedUsdc: 12_500e6,
            csvSampleCount: 26,
            lastPayoutEpoch: 1_759_872_000,
            onTimeRatioBps: 9700
        });
        receipts[1] = FreelanceCreditScorer.PlatformReceipt({
            platformId: keccak256("fiverr"),
            totalEarnedUsdc: 6_200e6,
            csvSampleCount: 24,
            lastPayoutEpoch: 1_759_857_600,
            onTimeRatioBps: 9300
        });
        receipts[2] = FreelanceCreditScorer.PlatformReceipt({
            platformId: keccak256("uber"),
            totalEarnedUsdc: 9_800e6,
            csvSampleCount: 28,
            lastPayoutEpoch: 1_759_886_400,
            onTimeRatioBps: 9900
        });

        history = FreelanceCreditScorer.FreelanceHistory({
            platforms: receipts,
            lookbackMonths: 12,
            snapshotTimestamp: 1_759_900_800
        });
    }

    function _leanHistory()
        internal
        pure
        returns (FreelanceCreditScorer.FreelanceHistory memory history)
    {
        FreelanceCreditScorer.PlatformReceipt[] memory receipts = new FreelanceCreditScorer.PlatformReceipt[](
            1
        );

        receipts[0] = FreelanceCreditScorer.PlatformReceipt({
            platformId: keccak256("upwork"),
            totalEarnedUsdc: 3_000e6,
            csvSampleCount: 8,
            lastPayoutEpoch: 1_759_814_400,
            onTimeRatioBps: 8700
        });

        history = FreelanceCreditScorer.FreelanceHistory({
            platforms: receipts,
            lookbackMonths: 6,
            snapshotTimestamp: 1_759_900_800
        });
    }
}

