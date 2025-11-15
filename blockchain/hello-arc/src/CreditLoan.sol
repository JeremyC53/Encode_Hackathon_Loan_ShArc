// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

interface ICreditScore {
    function getCreditScore(address user) external view returns (uint256 score, uint256 updatedAt);
}

/**
 * @title CreditLoanUSDC
 * @notice On-chain credit loan system using USDC with multiple loans per user.
 */
contract CreditLoan is Ownable {
    using SafeERC20 for IERC20;

    IERC20 public immutable USDC;

    // Service fee percentage in basis points (1000 = 10%)
    uint256 public serviceFeeRate;

    // Credit score contract reference
    ICreditScore public creditScoreContract;

    // Minimum credit score required for loans (0 = disabled)
    uint256 public minCreditScore;

    struct Loan {
        uint256 id;             // unique loan id
        address borrower;       // borrower address
        uint256 principal;      // principal in USDC (6 decimals)
        uint256 serviceFee;     // fixed service fee in USDC (6 decimals)
        uint256 totalOwed;      // principal + service fee
        uint256 amountRepaid;   // repaid so far
        uint256 timestamp;      // creation time
        bool active;            // true if not fully repaid / not cancelled
    }

    // Auto-incrementing loan ID
    uint256 public nextLoanId;

    // All loans by ID
    mapping(uint256 => Loan) public loans;

    // Borrower => list of their loan IDs
    mapping(address => uint256[]) public borrowerLoans;

    // Events
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

    // Errors
    error NoActiveLoan();
    error InvalidAmount();
    error OverpaymentNotAllowed();
    error InsufficientLiquidity();
    error NotBorrower();
    error InvalidServiceFeeRate();
    error InsufficientCreditScore();

    constructor() Ownable(msg.sender) {
        USDC = IERC20(0x3600000000000000000000000000000000000000);
        serviceFeeRate = 1000; // 10% default
    }


    /**
     * @notice Owner funds the contract with USDC
     * @dev Owner must approve the contract for `amount` before calling.
     */
    function fund(uint256 amount) external onlyOwner {
        if (amount == 0) revert InvalidAmount();

        USDC.safeTransferFrom(msg.sender, address(this), amount);

        emit Funded(msg.sender, amount);
    }

    /**
     * @notice Issue a USDC loan to a borrower (no restriction on existing loans)
     * @param borrower Borrower address
     * @param principal Principal amount in USDC smallest units (1 USDC = 1e6)
     * @dev Service fee is automatically calculated based on serviceFeeRate
     * @dev Checks credit score if minCreditScore > 0
     */
    function issueLoan(
        address borrower,
        uint256 principal
    ) external onlyOwner {
        if (principal == 0) revert InvalidAmount();

        uint256 contractBalance = USDC.balanceOf(address(this));
        if (principal > contractBalance) revert InsufficientLiquidity();

        // Check credit score if enabled
        if (minCreditScore > 0 && address(creditScoreContract) != address(0)) {
            (uint256 score, ) = creditScoreContract.getCreditScore(borrower);
            if (score < minCreditScore) revert InsufficientCreditScore();
        }

        // Calculate service fee based on serviceFeeRate (basis points)
        uint256 serviceFee = (principal * serviceFeeRate) / 10000;
        uint256 totalOwed = principal + serviceFee;

        uint256 loanId = nextLoanId++;
        loans[loanId] = Loan({
            id: loanId,
            borrower: borrower,
            principal: principal,
            serviceFee: serviceFee,
            totalOwed: totalOwed,
            amountRepaid: 0,
            timestamp: block.timestamp,
            active: true
        });

        borrowerLoans[borrower].push(loanId);

        // send principal from contract to borrower
        USDC.safeTransfer(borrower, principal);

        emit LoanIssued(
            loanId,
            borrower,
            principal,
            serviceFee,
            totalOwed,
            block.timestamp
        );
    }

    /**
     * @notice Repay a specific loan in USDC
     * @dev Borrower must approve contract for `amount` first.
     * @param loanId ID of the loan to repay
     * @param amount Amount of USDC to repay
     */
    function repay(uint256 loanId, uint256 amount) external {
        if (amount == 0) revert InvalidAmount();

        Loan storage loan = loans[loanId];
        if (!loan.active) revert NoActiveLoan();
        if (loan.borrower != msg.sender) revert NotBorrower();

        uint256 remainingBalance = loan.totalOwed - loan.amountRepaid;
        if (amount > remainingBalance) revert OverpaymentNotAllowed();

        // pull USDC from borrower → contract
        USDC.safeTransferFrom(msg.sender, address(this), amount);

        loan.amountRepaid += amount;
        remainingBalance = loan.totalOwed - loan.amountRepaid;

        emit RepaymentMade(loanId, msg.sender, amount, remainingBalance);

        if (remainingBalance == 0) {
            loan.active = false;
            emit LoanFullyRepaid(loanId, msg.sender, block.timestamp);
        }
    }

    /**
     * @notice Cancel an active loan (owner only)
     */
    function cancelLoan(uint256 loanId) external onlyOwner {
        Loan storage loan = loans[loanId];
        if (!loan.active) revert NoActiveLoan();

        loan.active = false;
        emit LoanCancelled(loanId, loan.borrower, block.timestamp);
    }

    /**
     * @notice Withdraw USDC from contract to owner
     */
    function withdraw(uint256 amount) external onlyOwner {
        if (amount == 0) revert InvalidAmount();

        uint256 balance = USDC.balanceOf(address(this));
        if (amount > balance) revert InvalidAmount();

        USDC.safeTransfer(owner(), amount);

        emit Withdrawn(owner(), amount);
    }

    /**
     * @notice Update the service fee rate (admin only)
     * @param newRate New service fee rate in basis points (e.g., 1000 = 10%)
     * @dev Maximum rate is 50% (5000 basis points) for safety
     */
    function updateServiceFeeRate(uint256 newRate) external onlyOwner {
        if (newRate > 5000) revert InvalidServiceFeeRate(); // Max 50%
        
        uint256 oldRate = serviceFeeRate;
        serviceFeeRate = newRate;

        emit ServiceFeeRateUpdated(oldRate, newRate);
    }

    /**
     * @notice Set the credit score contract address (admin only)
     * @param _creditScoreContract Address of the credit score contract
     */
    function setCreditScoreContract(address _creditScoreContract) external onlyOwner {
        address oldContract = address(creditScoreContract);
        creditScoreContract = ICreditScore(_creditScoreContract);

        emit CreditScoreContractUpdated(oldContract, _creditScoreContract);
    }

    /**
     * @notice Update the minimum credit score required for loans (admin only)
     * @param _minScore Minimum credit score (set to 0 to disable credit check)
     */
    function updateMinCreditScore(uint256 _minScore) external onlyOwner {
        uint256 oldScore = minCreditScore;
        minCreditScore = _minScore;

        emit MinCreditScoreUpdated(oldScore, _minScore);
    }

    /**
     * @notice Get remaining balance for a specific loan
     */
    function getRemainingBalance(uint256 loanId) external view returns (uint256) {
        Loan memory loan = loans[loanId];
        if (!loan.active) return 0;
        return loan.totalOwed - loan.amountRepaid;
    }

    /**
     * @notice Get all loan IDs for a borrower
     */
    function getBorrowerLoans(address borrower) external view returns (uint256[] memory) {
        return borrowerLoans[borrower];
    }

    /**
     * @notice Get contract's USDC balance
     */
    function getBalance() external view returns (uint256) {
        return USDC.balanceOf(address(this));
    }
}
