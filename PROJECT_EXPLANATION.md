# Loan ShArc - Project Explanation

## 🎯 Project Overview

**Loan ShArc** is a decentralized lending platform designed specifically for freelancers. It uses blockchain technology (Arc Network) to provide credit-based loans in USDC by analyzing freelancers' payment history across multiple platforms (Upwork, Fiverr, Uber, etc.).

### Key Innovation
Instead of traditional credit checks, the platform calculates creditworthiness by analyzing real payment data extracted from freelancers' email receipts and transaction histories.

---

## 🏗️ System Architecture

The project consists of **three main components**:

### 1. **Backend API** (FastAPI - Python)
- **Location**: `backend/app/`
- **Purpose**: Data ingestion and processing layer
- **Key Features**:
  - Accepts freelancer payment history data
  - Validates and processes multi-platform transaction data
  - Provides preview endpoints to check credit scores before on-chain submission
  - Integrates with Gmail API to extract payment receipts

**Main Endpoints**:
- `GET /api/health` - Health check
- `GET /api/freelancers/sample` - Returns sample freelancer history
- `POST /api/freelancers/preview` - Preview credit decision before submitting to blockchain
- `POST /run-google-mail` - Triggers Gmail data extraction
- `GET /uber-earnings` - Returns extracted Uber earnings CSV

### 2. **Blockchain Smart Contracts** (Solidity - Arc Network)
- **Location**: `blockchain/hello-arc/src/`
- **Network**: Arc Testnet
- **Three Main Contracts**:

#### a) `FreelanceCreditScorer.sol`
**Purpose**: Calculates credit scores and loan terms based on payment history

**Key Features**:
- Accepts `FreelanceHistory` struct containing payment data from multiple platforms
- Calculates a credit score (0-1000) using transparent, deterministic algorithms
- Determines borrowing limits, APR, and repayment schedules
- Stores credit decisions on-chain for verification

**Scoring Algorithm** (Total: 1000 points max):
- **Annual Income Score** (max 400 pts): Based on average monthly income × 12
- **History Length** (max 150 pts): Points for each month of payment history
- **Platform Diversity** (max 200 pts): More platforms = higher score (70 pts per platform)
- **Payment Reliability** (max 150 pts): On-time payment ratio (weighted by volume)
- **Data Quality** (max 150 pts): Number of transaction samples (5 pts per sample)
- **Data Freshness** (max 150 pts): How recent the last payment was (penalizes stale data)

**Loan Terms Calculation**:
- **Borrowing Limit**: 40% of total earnings in the lookback period
- **APR**: 2.5% - 0.5% (inversely related to credit score, minimum 0.5%)
- **Repayment Schedule**:
  - Score ≥ 800: 6 installments (180 days)
  - Score ≥ 650: 4 installments (120 days)
  - Score < 650: 3 installments (90 days)

#### b) `CreditLoan.sol`
**Purpose**: Manages the actual loan issuance and repayment in USDC

**Key Features**:
- Issues USDC loans to borrowers
- Tracks multiple loans per borrower
- Calculates service fees (default 10%, configurable)
- Handles loan repayments in installments
- Integrates with `CreditScore` contract for eligibility checks
- Owner-controlled funding and withdrawal

**Loan Lifecycle**:
1. Owner funds contract with USDC
2. Owner issues loan to borrower (checks credit score if enabled)
3. Borrower receives principal amount
4. Borrower repays in installments
5. Loan marked as inactive when fully repaid

#### c) `CreditScore.sol`
**Purpose**: Stores credit scores on-chain for quick lookup

**Key Features**:
- Admin-controlled score updates
- Stores score + last update timestamp
- Provides read interface for other contracts
- Emits events when scores are updated

### 3. **Frontend** (React + TypeScript)
- **Location**: `frontend/src/`
- **Purpose**: User interface for freelancers
- **Key Screens**:
  - **Login Screen**: User authentication
  - **Dashboard**: Overview of balance, active loans, next payment
  - **Loans Screen**: List of all loans with status and payment schedule
  - **Settings Screen**: User preferences

---

## 📊 Data Flow

### Step 1: Data Collection
1. **Gmail Integration** (`data_sources/google_mail.py`):
   - Connects to Gmail API
   - Searches for payment receipts from platforms (Uber, Upwork, etc.)
   - Extracts earnings amounts and dates from email bodies
   - Generates CSV files with transaction history

### Step 2: Data Processing
1. **Backend receives** `FreelanceHistoryPayload` containing:
   - Freelancer wallet address
   - Payment history from multiple platforms
   - Transaction details (amounts, dates, clients)
   - Platform summaries (total earned, on-time ratio, etc.)

2. **Backend validates** and summarizes data:
   - Calculates total earnings across platforms
   - Aggregates metrics (platform count, average monthly income, etc.)
   - Returns preview response

### Step 3: On-Chain Credit Scoring
1. **Frontend/Backend calls** `FreelanceCreditScorer.evaluateAndStore()`:
   - Submits `FreelanceHistory` struct to smart contract
   - Contract calculates credit score using deterministic algorithm
   - Contract determines loan terms (limit, APR, schedule)
   - Decision stored on-chain and emitted as event

2. **Credit score stored** in `CreditScore` contract:
   - Backend updates score for quick future lookups
   - Other contracts can query score for eligibility checks

### Step 4: Loan Issuance
1. **Owner calls** `CreditLoan.issueLoan()`:
   - Checks borrower's credit score (if enabled)
   - Calculates service fee
   - Transfers USDC principal to borrower
   - Creates loan record

2. **Borrower repays** via `CreditLoan.repay()`:
   - Makes installment payments
   - Contract tracks remaining balance
   - Loan marked complete when fully repaid

---

## 🔑 Key Technical Features

### 1. **Multi-Platform Support**
- Aggregates payment history from multiple freelance platforms
- Handles different currencies (with FX conversion to USDC)
- Weighted scoring based on platform diversity

### 2. **Transparent Credit Scoring**
- All scoring logic is on-chain and verifiable
- Deterministic algorithm ensures consistent results
- Off-chain services can preview scores before submission

### 3. **USDC Integration**
- All loans denominated in USDC (6 decimals)
- Uses Arc Testnet USDC address: `0x3600000000000000000000000000000000000000`
- Safe ERC20 transfers using OpenZeppelin's SafeERC20

### 4. **Flexible Loan Management**
- Multiple loans per borrower
- Configurable service fees
- Optional credit score requirements
- Owner-controlled funding and withdrawal

### 5. **Data Privacy & Verification**
- Payment data extracted from user's own Gmail
- On-chain storage of credit decisions for transparency
- Verifiable scoring algorithm

---

## 📈 Example Credit Score Calculation

Given a freelancer with:
- **Total Earnings**: $28,500 USDC over 12 months
- **Platforms**: 3 (Upwork, Fiverr, Uber)
- **On-Time Ratio**: 96.35% (9635 basis points)
- **Transaction Samples**: 78
- **Last Payment**: 1 day ago

**Score Breakdown**:
- Annual Income: ($28,500 / 12) × 12 = $28,500 → **400 pts** (capped)
- History Length: 12 months × 12 = **144 pts**
- Platform Diversity: 3 × 70 = **210 pts** → **200 pts** (capped)
- Payment Reliability: (9635 × 150) / 10000 = **144 pts**
- Data Quality: 78 × 5 = **390 pts** → **150 pts** (capped)
- Data Freshness: **150 pts** (very recent)

**Total Score**: 400 + 144 + 200 + 144 + 150 + 150 = **1,188** → **1,000** (capped)

**Loan Terms**:
- Borrowing Limit: $28,500 × 40% = **$11,400 USDC**
- APR: 2500 - (1000 × 1500 / 1000) = **1,000 bps (10%)**
- Repayment: **6 installments over 180 days**

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.x
- **APIs**: Gmail API, Google OAuth
- **Data Processing**: BeautifulSoup, regex

### Blockchain
- **Network**: Arc Testnet
- **Language**: Solidity ^0.8.30
- **Framework**: Foundry
- **Libraries**: OpenZeppelin Contracts
- **Token**: USDC (ERC-20, 6 decimals)

### Frontend
- **Framework**: React + TypeScript
- **Build Tool**: Vite
- **Styling**: Inline CSS (dark theme)

---

## 🎯 Use Cases

1. **Freelancer Needs Quick Cash Flow**:
   - Connects Gmail account
   - System extracts payment history
   - Gets instant credit score and loan offer
   - Receives USDC loan within minutes

2. **Multiple Income Streams**:
   - Works on Upwork, Fiverr, and drives for Uber
   - All platforms aggregated for better credit score
   - Higher borrowing limit due to diversified income

3. **Transparent Lending**:
   - All credit decisions verifiable on-chain
   - No hidden algorithms or black-box scoring
   - Freelancers can preview scores before applying

---

## 🔒 Security Features

- **Owner Controls**: Critical functions (funding, loan issuance) restricted to owner
- **Safe Token Transfers**: Uses OpenZeppelin's SafeERC20
- **Input Validation**: Comprehensive checks for invalid amounts, overpayments
- **Credit Score Checks**: Optional minimum score requirements
- **Liquidity Checks**: Prevents loan issuance if insufficient funds

---

## 📝 Key Files Reference

- **Backend API**: `backend/app/main.py`, `backend/app/routes.py`
- **Data Models**: `backend/app/schemas.py`
- **Gmail Parser**: `data_sources/google_mail.py`
- **Credit Scorer**: `blockchain/hello-arc/src/FreelanceCreditScorer.sol`
- **Loan Contract**: `blockchain/hello-arc/src/CreditLoan.sol`
- **Score Storage**: `blockchain/hello-arc/src/CreditScore.sol`
- **Frontend**: `frontend/src/App.tsx`, `frontend/src/screens/`

---

## 🚀 Future Enhancements (Potential)

- Automated Gmail parsing on a schedule
- Integration with more platforms (Stripe, PayPal, etc.)
- Decentralized identity verification
- Peer-to-peer lending pools
- Credit score improvement recommendations
- Mobile app for easier access

---

This project demonstrates how blockchain technology can democratize access to credit by using alternative data sources (freelance payment history) instead of traditional credit bureaus, making financial services more accessible to the growing gig economy workforce.

