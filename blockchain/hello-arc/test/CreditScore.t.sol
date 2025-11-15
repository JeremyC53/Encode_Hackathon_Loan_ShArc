// SPDX-License-Identifier: MIT
pragma solidity ^0.8.30;

import "forge-std/Test.sol";
import "../src/CreditScore.sol";

contract CreditScoreTest is Test {
    CreditScore private creditScore;
    
    address private admin;
    address private user1;
    address private user2;
    address private nonAdmin;

    event CreditScoreUpdated(address indexed user, uint256 score, uint256 timestamp);

    function setUp() public {
        admin = address(this);
        user1 = makeAddr("user1");
        user2 = makeAddr("user2");
        nonAdmin = makeAddr("nonAdmin");
        
        creditScore = new CreditScore();
    }

    // ============================================
    // Constructor Tests
    // ============================================

    function testConstructorSetsAdmin() public view {
        assertEq(creditScore.admin(), admin);
    }

    // ============================================
    // setCreditScore Tests
    // ============================================

    function testSetCreditScore() public {
        uint256 score = 750;
        
        vm.expectEmit(true, false, false, true);
        emit CreditScoreUpdated(user1, score, block.timestamp);
        
        creditScore.setCreditScore(user1, score);
        
        (uint256 storedScore, uint256 updatedAt) = creditScore.getCreditScore(user1);
        assertEq(storedScore, score);
        assertEq(updatedAt, block.timestamp);
    }

    function testSetCreditScoreMultipleUsers() public {
        uint256 score1 = 650;
        uint256 score2 = 800;
        
        creditScore.setCreditScore(user1, score1);
        creditScore.setCreditScore(user2, score2);
        
        (uint256 storedScore1,) = creditScore.getCreditScore(user1);
        (uint256 storedScore2,) = creditScore.getCreditScore(user2);
        
        assertEq(storedScore1, score1);
        assertEq(storedScore2, score2);
    }

    function testSetCreditScoreUpdate() public {
        uint256 initialScore = 600;
        uint256 updatedScore = 750;
        
        creditScore.setCreditScore(user1, initialScore);
        
        vm.warp(block.timestamp + 30 days);
        
        creditScore.setCreditScore(user1, updatedScore);
        
        (uint256 storedScore, uint256 updatedAt) = creditScore.getCreditScore(user1);
        assertEq(storedScore, updatedScore);
        assertEq(updatedAt, block.timestamp);
    }

    function testSetCreditScoreRevertsOnZeroAddress() public {
        vm.expectRevert("Invalid user");
        creditScore.setCreditScore(address(0), 700);
    }

    function testSetCreditScoreRevertsOnZeroScore() public {
        vm.expectRevert("Score must be > 0");
        creditScore.setCreditScore(user1, 0);
    }

    function testSetCreditScoreRevertsWhenNotAdmin() public {
        vm.prank(nonAdmin);
        vm.expectRevert("Not authorized");
        creditScore.setCreditScore(user1, 700);
    }

    function testSetCreditScoreEmitsEvent() public {
        uint256 score = 820;
        
        vm.expectEmit(true, false, false, true);
        emit CreditScoreUpdated(user1, score, block.timestamp);
        
        creditScore.setCreditScore(user1, score);
    }

    function testSetCreditScoreFuzz(uint256 score) public {
        vm.assume(score > 0 && score <= 10000);
        
        creditScore.setCreditScore(user1, score);
        
        (uint256 storedScore,) = creditScore.getCreditScore(user1);
        assertEq(storedScore, score);
    }

    // ============================================
    // getCreditScore Tests
    // ============================================

    function testGetCreditScoreDefaultValues() public view {
        (uint256 score, uint256 updatedAt) = creditScore.getCreditScore(user1);
        assertEq(score, 0);
        assertEq(updatedAt, 0);
    }

    function testGetCreditScoreAfterSet() public {
        uint256 expectedScore = 720;
        creditScore.setCreditScore(user1, expectedScore);
        
        (uint256 score, uint256 updatedAt) = creditScore.getCreditScore(user1);
        assertEq(score, expectedScore);
        assertEq(updatedAt, block.timestamp);
    }

    function testGetCreditScoreAnyoneCanRead() public {
        uint256 expectedScore = 700;
        creditScore.setCreditScore(user1, expectedScore);
        
        vm.prank(nonAdmin);
        (uint256 score, uint256 updatedAt) = creditScore.getCreditScore(user1);
        assertEq(score, expectedScore);
        assertGt(updatedAt, 0);
    }

    // ============================================
    // setAdmin Tests
    // ============================================

    function testSetAdmin() public {
        address newAdmin = makeAddr("newAdmin");
        
        creditScore.setAdmin(newAdmin);
        
        assertEq(creditScore.admin(), newAdmin);
    }

    function testSetAdminTransfersControl() public {
        address newAdmin = makeAddr("newAdmin");
        
        creditScore.setAdmin(newAdmin);
        
        // Old admin should not be able to set credit score
        vm.expectRevert("Not authorized");
        creditScore.setCreditScore(user1, 700);
        
        // New admin should be able to set credit score
        vm.prank(newAdmin);
        creditScore.setCreditScore(user1, 700);
        
        (uint256 score,) = creditScore.getCreditScore(user1);
        assertEq(score, 700);
    }

    function testSetAdminRevertsOnZeroAddress() public {
        vm.expectRevert("Invalid admin");
        creditScore.setAdmin(address(0));
    }

    function testSetAdminRevertsWhenNotAdmin() public {
        address newAdmin = makeAddr("newAdmin");
        
        vm.prank(nonAdmin);
        vm.expectRevert("Not authorized");
        creditScore.setAdmin(newAdmin);
    }

    function testSetAdminCanBeCalledByNewAdmin() public {
        address newAdmin1 = makeAddr("newAdmin1");
        address newAdmin2 = makeAddr("newAdmin2");
        
        creditScore.setAdmin(newAdmin1);
        
        vm.prank(newAdmin1);
        creditScore.setAdmin(newAdmin2);
        
        assertEq(creditScore.admin(), newAdmin2);
    }

    // ============================================
    // lastUpdated Tests
    // ============================================

    function testLastUpdatedIsPublic() public {
        creditScore.setCreditScore(user1, 700);
        
        uint256 lastUpdated = creditScore.lastUpdated(user1);
        assertEq(lastUpdated, block.timestamp);
    }

    function testLastUpdatedUpdatesOnScoreChange() public {
        creditScore.setCreditScore(user1, 700);
        uint256 firstUpdate = creditScore.lastUpdated(user1);
        
        vm.warp(block.timestamp + 10 days);
        
        creditScore.setCreditScore(user1, 750);
        uint256 secondUpdate = creditScore.lastUpdated(user1);
        
        assertGt(secondUpdate, firstUpdate);
        assertEq(secondUpdate, block.timestamp);
    }

    // ============================================
    // Integration Tests
    // ============================================

    function testFullWorkflow() public {
        // Admin sets initial score
        creditScore.setCreditScore(user1, 650);
        
        (uint256 score1, uint256 updatedAt1) = creditScore.getCreditScore(user1);
        assertEq(score1, 650);
        assertEq(updatedAt1, block.timestamp);
        
        // Time passes
        vm.warp(block.timestamp + 60 days);
        
        // Admin updates score after user's performance improves
        creditScore.setCreditScore(user1, 780);
        
        (uint256 score2, uint256 updatedAt2) = creditScore.getCreditScore(user1);
        assertEq(score2, 780);
        assertEq(updatedAt2, block.timestamp);
        assertGt(updatedAt2, updatedAt1);
    }

    function testMultipleUsersIndependentScores() public {
        creditScore.setCreditScore(user1, 600);
        
        vm.warp(block.timestamp + 5 days);
        creditScore.setCreditScore(user2, 850);
        
        (uint256 score1, uint256 updatedAt1) = creditScore.getCreditScore(user1);
        (uint256 score2, uint256 updatedAt2) = creditScore.getCreditScore(user2);
        
        assertEq(score1, 600);
        assertEq(score2, 850);
        assertLt(updatedAt1, updatedAt2);
    }
}

