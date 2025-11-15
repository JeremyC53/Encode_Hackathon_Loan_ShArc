# Loan ShArc Backend

Backend API for the Loan ShArc platform with automatic transaction collection from blockchain events.

## Features

- ✅ **Supabase Integration** - Automatic connection to PostgreSQL database
- ✅ **Automatic Transaction Collection** - Listens to blockchain events and stores transactions
- ✅ **RESTful API** - Query transactions, loans, and credit scores
- ✅ **Real-time Sync** - Background task syncs blockchain events to database

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Create `.env` file in `backend/` directory:

```env
DATABASE_URL=postgresql://postgres.jmwhsuqhzdurrbynxuwd:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres

# Optional: Enable blockchain event listening
CREDIT_LOAN_CONTRACT=0xYourContractAddress
RPC_URL=https://your-rpc-url
```

Get your Supabase password from: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd → Settings → Database

### 3. Initialize Database

```bash
python -m app.init_db
```

### 4. Start Server

```bash
uvicorn app.main:app --reload
```

The server will:
- Connect to Supabase automatically
- Initialize database tables
- Start blockchain event listener (if configured)

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/transactions` - List transactions (with filters)
- `POST /api/transactions` - Create transaction
- `GET /api/users/{address}/transactions` - User's transactions
- `GET /api/loans` - List loans
- `GET /api/users/{address}/loans` - User's loans
- `GET /api/freelancers/sample` - Sample freelancer history
- `POST /api/freelancers/preview` - Preview credit decision

See interactive docs at: http://localhost:8000/docs

## Automatic Transaction Collection

When `CREDIT_LOAN_CONTRACT` is set in `.env`, the app automatically:
- Listens for `LoanIssued` events → stores loan transactions
- Listens for `RepaymentMade` events → stores repayment transactions
- Listens for `LoanFullyRepaid` events → updates loan status

Transactions are stored in Supabase in real-time.

## Database Schema

- **transactions** - All loan-related transactions
- **loan_history** - Loan records synced from blockchain
- **credit_score_history** - Credit score tracking

## Development

### Create Sample Data

```bash
python -m scripts.init_sample_data
```

### View Data in Supabase

1. Go to: https://supabase.com/dashboard/project/jmwhsuqhzdurrbynxuwd
2. Click **Table Editor**
3. Browse `transactions`, `loan_history`, `credit_score_history` tables

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app with blockchain listener
│   ├── routes.py            # API endpoints
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # Database connection (Supabase/SQLite)
│   └── blockchain_listener.py  # Background task for event listening
├── scripts/
│   └── init_sample_data.py  # Create sample data
├── requirements.txt
├── env.example              # Environment variables template
└── README.md
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (required)
- `CREDIT_LOAN_CONTRACT` - Smart contract address (optional, for event listening)
- `RPC_URL` - Blockchain RPC endpoint (optional, for event listening)

