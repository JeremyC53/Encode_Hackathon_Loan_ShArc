// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {Test} from "forge-std/Test.sol";
import {CreditLoan} from "../src/CreditLoan.sol";
import {CreditScore} from "../src/CreditScore.sol";
import {MockUSDC} from "./mocks/MockUSDC.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract CreditLoanTest is Test {
    CreditLoan public creditLoan;
    CreditScore public creditScore;
    MockUSDC public usdc;
    address public owner;
    address public borrower1;
    address public borrower2;

    // USDC has 6 decimals
    uint256 constant USDC_UNIT = 1e6;

    event LoanIssued(
        uint256 indexed loanId,
        address indexed borrower,
        uint256 principal,
        uint256 serviceFee,
        uint256 totalOwed,
        uint256 timestamp
    );

    event RepaymentMade(
        uint256 indexed loanId,
        address indexed borrower,
        uint256 amount,
        uint256 remainingBalance
    );

    event LoanFullyRepaid(uint256 indexed loanId, address indexed borrower, uint256 timestamp);
    event LoanCancelled(uint256 indexed loanId, address indexed borrower, uint256 timestamp);
    event Funded(address indexed from, uint256 amount);
    event Withdrawn(address indexed to, uint256 amount);
    event ServiceFeeRateUpdated(uint256 oldRate, uint256 newRate);
    event CreditScoreContractUpdated(address indexed oldContract, address indexed newContract);
    event MinCreditScoreUpdated(uint256 oldScore, uint256 newScore);

    function setUp() public {
        owner = address(this);
        borrower1 = makeAddr("borrower1");
        borrower2 = makeAddr("borrower2");

        // Deploy MockUSDC at the hardcoded address using vm.etch
        MockUSDC mockUSDC = new MockUSDC();
        bytes memory mockUSDCCode = address(mockUSDC).code;
        vm.etch(0x3600000000000000000000000000000000000000, mockUSDCCode);
        
        // Now use the USDC at the hardcoded address
        usdc = MockUSDC(0x3600000000000000000000000000000000000000);

        // Deploy CreditScore contract
        creditScore = new CreditScore();

        // Deploy CreditLoan contract (it will use the hardcoded USDC address)
        creditLoan = new CreditLoan();

        // Set up credit score contract in loan contract
        creditLoan.setCreditScoreContract(address(creditScore));

        // Mint USDC to owner for funding
        usdc.mint(owner, 1_000_000 * USDC_UNIT);
        
        // Fund the contract with USDC
        usdc.approve(address(creditLoan), 1_000_000 * USDC_UNIT);
        creditLoan.fund(100_000 * USDC_UNIT);

        // Give borrowers some USDC for repayments
        usdc.mint(borrower1, 50_000 * USDC_UNIT);
        usdc.mint(borrower2, 50_000 * USDC_UNIT);

        // Set default credit scores for borrowers (500 is a good score)
        creditScore.setCreditScore(borrower1, 700);
        creditScore.setCreditScore(borrower2, 650);
    }

    // ============ Fund Tests ============

    function testFund() public {
        uint256 balanceBefore = creditLoan.getBalance();
        uint256 fundAmount = 10_000 * USDC_UNIT;

        usdc.approve(address(creditLoan), fundAmount);

        vm.expectEmit(true, true, true, true);
        emit Funded(owner, fundAmount);

        creditLoan.fund(fundAmount);

        assertEq(creditLoan.getBalance(), balanceBefore + fundAmount);
    }

    function testCannotFundZeroAmount() public {
        vm.expectRevert(CreditLoan.InvalidAmount.selector);
        creditLoan.fund(0);
    }

    function testOnlyOwnerCanFund() public {
        vm.prank(borrower1);
        vm.expectRevert();
        creditLoan.fund(1000 * USDC_UNIT);
    }

    // ============ Loan Issuance Tests ============

    function testIssueLoan() public {
        uint256 principal = 10_000 * USDC_UNIT;
        uint256 expectedServiceFee = 1_000 * USDC_UNIT; // 10% of 10,000

        uint256 borrowerBalanceBefore = usdc.balanceOf(borrower1);

        vm.expectEmit(true, true, true, true);
        emit LoanIssued(0, borrower1, principal, expectedServiceFee, 11_000 * USDC_UNIT, block.timestamp);

        creditLoan.issueLoan(borrower1, principal);

        // Check loan details
        (
            uint256 id,
            address borrower,
            uint256 loanPrincipal,
            uint256 serviceFee,
            uint256 totalOwed,
            uint256 amountRepaid,
            ,  // timestamp (unused)
            bool active
        ) = creditLoan.loans(0);

        assertEq(id, 0);
        assertEq(borrower, borrower1);
        assertEq(loanPrincipal, principal);
        assertEq(serviceFee, expectedServiceFee);
        assertEq(totalOwed, 11_000 * USDC_UNIT); // 10,000 + 10%
        assertEq(amountRepaid, 0);
        assertTrue(active);

        // Check borrower received USDC
        assertEq(usdc.balanceOf(borrower1), borrowerBalanceBefore + principal);

        // Check borrower loans array
        uint256[] memory loans = creditLoan.getBorrowerLoans(borrower1);
        assertEq(loans.length, 1);
        assertEq(loans[0], 0);
    }

    function testIssueMultipleLoansToSameBorrower() public {
        creditLoan.issueLoan(borrower1, 5_000 * USDC_UNIT);
        creditLoan.issueLoan(borrower1, 3_000 * USDC_UNIT);

        uint256[] memory loans = creditLoan.getBorrowerLoans(borrower1);
        assertEq(loans.length, 2);
        assertEq(loans[0], 0);
        assertEq(loans[1], 1);

        // Check both loans are active
        (, , , , , , , bool active0) = creditLoan.loans(0);
        (, , , , , , , bool active1) = creditLoan.loans(1);
        assertTrue(active0);
        assertTrue(active1);
    }

    function testCannotIssueLoanWithZeroPrincipal() public {
        vm.expectRevert(CreditLoan.InvalidAmount.selector);
        creditLoan.issueLoan(borrower1, 0);
    }

    function testCannotIssueLoanWithInsufficientLiquidity() public {
        uint256 contractBalance = creditLoan.getBalance();

        vm.expectRevert(CreditLoan.InsufficientLiquidity.selector);
        creditLoan.issueLoan(borrower1, contractBalance + 1);
    }

    function testOnlyOwnerCanIssueLoan() public {
        vm.prank(borrower1);
        vm.expectRevert();
        creditLoan.issueLoan(borrower2, 10_000 * USDC_UNIT);
    }

    // ============ Repayment Tests ============

    function testPartialRepayment() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT); // Total: 11,000 (10% fee)

        vm.startPrank(borrower1);
        usdc.approve(address(creditLoan), 5_000 * USDC_UNIT);

        vm.expectEmit(true, true, true, true);
        emit RepaymentMade(0, borrower1, 5_000 * USDC_UNIT, 6_000 * USDC_UNIT);

        creditLoan.repay(0, 5_000 * USDC_UNIT);
        vm.stopPrank();

        (, , , , , uint256 amountRepaid, , bool active) = creditLoan.loans(0);
        assertEq(amountRepaid, 5_000 * USDC_UNIT);
        assertEq(creditLoan.getRemainingBalance(0), 6_000 * USDC_UNIT);
        assertTrue(active);
    }

    function testFullRepayment() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT); // Total: 11,000 (10% fee)

        vm.startPrank(borrower1);
        usdc.approve(address(creditLoan), 11_000 * USDC_UNIT);

        vm.expectEmit(true, true, true, true);
        emit RepaymentMade(0, borrower1, 11_000 * USDC_UNIT, 0);
        vm.expectEmit(true, true, true, true);
        emit LoanFullyRepaid(0, borrower1, block.timestamp);

        creditLoan.repay(0, 11_000 * USDC_UNIT);
        vm.stopPrank();

        (, , , , , uint256 amountRepaid, , bool active) = creditLoan.loans(0);
        assertEq(amountRepaid, 11_000 * USDC_UNIT);
        assertEq(creditLoan.getRemainingBalance(0), 0);
        assertFalse(active);
    }

    function testMultiplePartialRepayments() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT); // Total: 11,000 (10% fee)

        vm.startPrank(borrower1);
        usdc.approve(address(creditLoan), 11_000 * USDC_UNIT);

        creditLoan.repay(0, 3_000 * USDC_UNIT);
        assertEq(creditLoan.getRemainingBalance(0), 8_000 * USDC_UNIT);

        creditLoan.repay(0, 4_000 * USDC_UNIT);
        assertEq(creditLoan.getRemainingBalance(0), 4_000 * USDC_UNIT);

        creditLoan.repay(0, 4_000 * USDC_UNIT);
        assertEq(creditLoan.getRemainingBalance(0), 0);

        vm.stopPrank();

        (, , , , , , , bool active) = creditLoan.loans(0);
        assertFalse(active);
    }

    function testCannotRepayInactiveLoan() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT); // Total: 11,000 (10% fee)

        vm.startPrank(borrower1);
        usdc.approve(address(creditLoan), 11_000 * USDC_UNIT);
        creditLoan.repay(0, 11_000 * USDC_UNIT);

        // Try to repay again
        vm.expectRevert(CreditLoan.NoActiveLoan.selector);
        creditLoan.repay(0, 1 * USDC_UNIT);
        vm.stopPrank();
    }

    function testCannotRepayZeroAmount() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);

        vm.prank(borrower1);
        vm.expectRevert(CreditLoan.InvalidAmount.selector);
        creditLoan.repay(0, 0);
    }

    function testCannotOverpay() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT); // Total: 11,000 (10% fee)

        vm.startPrank(borrower1);
        usdc.approve(address(creditLoan), 12_000 * USDC_UNIT);

        vm.expectRevert(CreditLoan.OverpaymentNotAllowed.selector);
        creditLoan.repay(0, 12_000 * USDC_UNIT);
        vm.stopPrank();
    }

    function testCannotRepayOtherBorrowerLoan() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);

        vm.startPrank(borrower2);
        usdc.approve(address(creditLoan), 5_000 * USDC_UNIT);

        vm.expectRevert(CreditLoan.NotBorrower.selector);
        creditLoan.repay(0, 5_000 * USDC_UNIT);
        vm.stopPrank();
    }

    // ============ Cancel Loan Tests ============

    function testCancelLoan() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);

        vm.expectEmit(true, true, true, true);
        emit LoanCancelled(0, borrower1, block.timestamp);

        creditLoan.cancelLoan(0);

        (, , , , , , , bool active) = creditLoan.loans(0);
        assertFalse(active);
    }

    function testCannotCancelInactiveLoan() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);
        creditLoan.cancelLoan(0);

        vm.expectRevert(CreditLoan.NoActiveLoan.selector);
        creditLoan.cancelLoan(0);
    }

    function testOnlyOwnerCanCancelLoan() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);

        vm.prank(borrower1);
        vm.expectRevert();
        creditLoan.cancelLoan(0);
    }

    // ============ Withdraw Tests ============

    function testWithdraw() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);

        vm.startPrank(borrower1);
        usdc.approve(address(creditLoan), 5_000 * USDC_UNIT);
        creditLoan.repay(0, 5_000 * USDC_UNIT);
        vm.stopPrank();

        uint256 ownerBalanceBefore = usdc.balanceOf(owner);
        uint256 contractBalanceBefore = creditLoan.getBalance();

        vm.expectEmit(true, true, true, true);
        emit Withdrawn(owner, 5_000 * USDC_UNIT);

        creditLoan.withdraw(5_000 * USDC_UNIT);

        assertEq(usdc.balanceOf(owner), ownerBalanceBefore + 5_000 * USDC_UNIT);
        assertEq(creditLoan.getBalance(), contractBalanceBefore - 5_000 * USDC_UNIT);
    }

    function testCannotWithdrawZeroAmount() public {
        vm.expectRevert(CreditLoan.InvalidAmount.selector);
        creditLoan.withdraw(0);
    }

    function testCannotWithdrawMoreThanBalance() public {
        uint256 balance = creditLoan.getBalance();

        vm.expectRevert(CreditLoan.InvalidAmount.selector);
        creditLoan.withdraw(balance + 1);
    }

    function testOnlyOwnerCanWithdraw() public {
        vm.prank(borrower1);
        vm.expectRevert();
        creditLoan.withdraw(1000 * USDC_UNIT);
    }

    // ============ Multiple Borrowers Tests ============

    function testMultipleBorrowersMultipleLoans() public {
        // Borrower1 gets 2 loans
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT); // Total: 11,000
        creditLoan.issueLoan(borrower1, 5_000 * USDC_UNIT);  // Total: 5,500

        // Borrower2 gets 1 loan
        creditLoan.issueLoan(borrower2, 20_000 * USDC_UNIT); // Total: 22,000

        // Check loan counts
        assertEq(creditLoan.getBorrowerLoans(borrower1).length, 2);
        assertEq(creditLoan.getBorrowerLoans(borrower2).length, 1);

        // Borrower1 repays first loan partially
        vm.startPrank(borrower1);
        usdc.approve(address(creditLoan), 5_000 * USDC_UNIT);
        creditLoan.repay(0, 5_000 * USDC_UNIT);
        vm.stopPrank();

        // Borrower2 repays their loan fully
        vm.startPrank(borrower2);
        usdc.approve(address(creditLoan), 22_000 * USDC_UNIT);
        creditLoan.repay(2, 22_000 * USDC_UNIT);
        vm.stopPrank();

        assertEq(creditLoan.getRemainingBalance(0), 6_000 * USDC_UNIT);
        assertEq(creditLoan.getRemainingBalance(1), 5_500 * USDC_UNIT);
        assertEq(creditLoan.getRemainingBalance(2), 0);
    }

    // ============ Service Fee Rate Tests ============

    function testUpdateServiceFeeRate() public {
        uint256 oldRate = creditLoan.serviceFeeRate();
        uint256 newRate = 500; // 5%

        vm.expectEmit(true, true, true, true);
        emit ServiceFeeRateUpdated(oldRate, newRate);

        creditLoan.updateServiceFeeRate(newRate);

        assertEq(creditLoan.serviceFeeRate(), newRate);

        // Issue a loan with new rate
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);
        (, , , uint256 serviceFee, uint256 totalOwed, , , ) = creditLoan.loans(0);
        assertEq(serviceFee, 500 * USDC_UNIT); // 5% of 10,000
        assertEq(totalOwed, 10_500 * USDC_UNIT);
    }

    function testCannotSetServiceFeeRateAboveMax() public {
        vm.expectRevert(CreditLoan.InvalidServiceFeeRate.selector);
        creditLoan.updateServiceFeeRate(5001); // > 50%
    }

    function testOnlyOwnerCanUpdateServiceFeeRate() public {
        vm.prank(borrower1);
        vm.expectRevert();
        creditLoan.updateServiceFeeRate(500);
    }

    // ============ Credit Score Tests ============

    function testSetCreditScoreContract() public {
        CreditScore newCreditScore = new CreditScore();
        
        vm.expectEmit(true, true, true, true);
        emit CreditScoreContractUpdated(address(creditScore), address(newCreditScore));

        creditLoan.setCreditScoreContract(address(newCreditScore));
    }

    function testUpdateMinCreditScore() public {
        vm.expectEmit(true, true, true, true);
        emit MinCreditScoreUpdated(0, 600);

        creditLoan.updateMinCreditScore(600);
        assertEq(creditLoan.minCreditScore(), 600);
    }

    function testCannotIssueLoanWithInsufficientCreditScore() public {
        // Set minimum credit score to 700
        creditLoan.updateMinCreditScore(700);

        // borrower2 has credit score of 650 (set in setUp)
        vm.expectRevert(CreditLoan.InsufficientCreditScore.selector);
        creditLoan.issueLoan(borrower2, 10_000 * USDC_UNIT);
    }

    function testCanIssueLoanWithSufficientCreditScore() public {
        // Set minimum credit score to 600
        creditLoan.updateMinCreditScore(600);

        // borrower1 has credit score of 700 (set in setUp)
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);

        (, , , , uint256 totalOwed, , , bool active) = creditLoan.loans(0);
        assertEq(totalOwed, 11_000 * USDC_UNIT);
        assertTrue(active);
    }

    function testCreditScoreCheckDisabledWhenMinScoreIsZero() public {
        // Min score is 0 by default, so anyone can get a loan
        address lowScoreBorrower = makeAddr("lowScore");
        creditScore.setCreditScore(lowScoreBorrower, 100); // Very low score
        usdc.mint(lowScoreBorrower, 50_000 * USDC_UNIT);

        // Should still be able to issue loan
        creditLoan.issueLoan(lowScoreBorrower, 5_000 * USDC_UNIT);

        (, , , , uint256 totalOwed, , , bool active) = creditLoan.loans(0);
        assertEq(totalOwed, 5_500 * USDC_UNIT);
        assertTrue(active);
    }

    // ============ Edge Cases ============

    function testGetRemainingBalanceForInactiveLoan() public {
        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);

        vm.startPrank(borrower1);
        usdc.approve(address(creditLoan), 11_000 * USDC_UNIT);
        creditLoan.repay(0, 11_000 * USDC_UNIT);
        vm.stopPrank();

        assertEq(creditLoan.getRemainingBalance(0), 0);
    }

    function testNextLoanIdIncrement() public {
        assertEq(creditLoan.nextLoanId(), 0);

        creditLoan.issueLoan(borrower1, 1_000 * USDC_UNIT);
        assertEq(creditLoan.nextLoanId(), 1);

        creditLoan.issueLoan(borrower2, 2_000 * USDC_UNIT);
        assertEq(creditLoan.nextLoanId(), 2);
    }

    function testGetBorrowerLoansEmpty() public {
        address nobody = makeAddr("nobody");
        uint256[] memory loans = creditLoan.getBorrowerLoans(nobody);
        assertEq(loans.length, 0);
    }

    function testZeroServiceFeeRate() public {
        creditLoan.updateServiceFeeRate(0); // 0% fee

        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);

        (, , , uint256 serviceFee, uint256 totalOwed, , , ) = creditLoan.loans(0);
        assertEq(serviceFee, 0);
        assertEq(totalOwed, 10_000 * USDC_UNIT); // No fee
    }

    function testMaxServiceFeeRate() public {
        creditLoan.updateServiceFeeRate(5000); // 50% fee

        creditLoan.issueLoan(borrower1, 10_000 * USDC_UNIT);

        (, , , uint256 serviceFee, uint256 totalOwed, , , ) = creditLoan.loans(0);
        assertEq(serviceFee, 5_000 * USDC_UNIT);
        assertEq(totalOwed, 15_000 * USDC_UNIT);
    }
}
