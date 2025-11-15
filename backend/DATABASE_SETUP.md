# Database Setup Guide

## 📊 Database Recommendation

**Recommended: PostgreSQL** (for production) or **SQLite** (for development)

### Why SQL/Relational Database?
- **Structured Data**: Transaction history has clear relationships (users → loans → transactions)
- **Query Performance**: Fast filtering, sorting, and aggregation
- **Data Integrity**: Foreign keys and constraints ensure data consistency
- **ACID Compliance**: Reliable transaction handling
- **Mature Ecosystem**: Excellent tooling and libraries

### Why Not JSON/Document Stores?
- Less efficient for relational queries (user's all transactions, loans with transactions)
- Harder to maintain data integrity across related records
- More complex querying for analytics

---

## 🆓 Free Database Options

### 1. **SQLite** (Recommended for Development)
- ✅ **Free**: Built into Python
- ✅ **Zero Configuration**: No server setup needed
- ✅ **Perfect for Development**: Single file database
- ❌ **Not for Production**: Limited concurrency, no network access

**Already configured as default!** Just run the app and it creates `loan_sharc.db`

### 2. **PostgreSQL** (Recommended for Production)
- ✅ **Free & Open Source**: Most popular open-source database
- ✅ **Production Ready**: Handles high concurrency, ACID compliant
- ✅ **Free Hosting Options**:
  - [Supabase](https://supabase.com) - Free tier: 500MB database
  - [Neon](https://neon.tech) - Free tier: 3GB storage
  - [Railway](https://railway.app) - Free tier: $5 credit/month
  - [Render](https://render.com) - Free tier: 90 days
  - [ElephantSQL](https://www.elephantsql.com) - Free tier: 20MB

### 3. **MySQL/MariaDB**
- ✅ **Free & Open Source**: Alternative to PostgreSQL
- ✅ **Similar Features**: Good for production use
- Free hosting: [PlanetScale](https://planetscale.com), [Aiven](https://aiven.io)

---

## 🚀 Quick Start

### Option 1: SQLite (Development - Easiest)

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Run the app** (database auto-creates on first run):
   ```bash
   uvicorn app.main:app --reload
   ```

   The database file `loan_sharc.db` will be created automatically in the backend directory.

### Option 2: PostgreSQL (Production)

#### Using Supabase (Recommended for Free Hosting)

1. **Create a Supabase account**: https://supabase.com
2. **Create a new project**
3. **Get your connection string** from Project Settings → Database
   - Format: `postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres`

4. **Set environment variable**:
   ```bash
   # Windows PowerShell
   $env:DATABASE_URL="postgresql://postgres:your_password@db.xxxxx.supabase.co:5432/postgres"
   
   # Linux/Mac
   export DATABASE_URL="postgresql://postgres:your_password@db.xxxxx.supabase.co:5432/postgres"
   
   # Or create a .env file in backend/
   DATABASE_URL=postgresql://postgres:your_password@db.xxxxx.supabase.co:5432/postgres
   ```

5. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

6. **Initialize database**:
   ```bash
   python -m app.init_db
   ```

7. **Run the app**:
   ```bash
   uvicorn app.main:app --reload
   ```

#### Using Local PostgreSQL

1. **Install PostgreSQL**: https://www.postgresql.org/download/
2. **Create database**:
   ```bash
   createdb loansharc
   ```

3. **Set connection string**:
   ```bash
   export DATABASE_URL="postgresql://postgres:password@localhost:5432/loansharc"
   ```

4. **Initialize and run** (same as above)

---

## 📁 Database Schema

### Tables Created

1. **`transactions`** - All loan-related transactions
   - Borrows, repayments, loan issuances
   - Links to users and loans
   - Stores on-chain transaction hashes

2. **`loan_history`** - Loan records synced from blockchain
   - Loan terms (principal, fees, APR)
   - Repayment status
   - Credit score at issuance

3. **`credit_score_history`** - Credit score tracking over time
   - Historical credit scores
   - Score calculation metadata

---

## 🔌 API Endpoints

### Create Transaction
```bash
POST /api/transactions
Content-Type: application/json

{
  "user_address": "0x1234...",
  "transaction_type": "borrow",
  "amount": 1000.50,
  "currency": "USDC",
  "loan_id": 1,
  "tx_hash": "0xabc...",
  "transaction_timestamp": "2025-01-15T10:30:00Z",
  "status": "confirmed"
}
```

### Get Transactions
```bash
# All transactions
GET /api/transactions?page=1&page_size=50

# Filter by user
GET /api/transactions?user_address=0x1234...

# Filter by type
GET /api/transactions?transaction_type=repay

# Filter by loan
GET /api/transactions?loan_id=1
```

### Get User Transactions
```bash
GET /api/users/0x1234.../transactions
```

### Get Loan Transactions
```bash
GET /api/loans/1/transactions
```

### Get Loans
```bash
# All loans
GET /api/loans

# User's loans
GET /api/users/0x1234.../loans

# Active loans only
GET /api/loans?is_active=true
```

---

## 🔧 Database Management

### Initialize Database
```bash
python -m app.init_db
```

### Drop All Tables (⚠️ Destructive!)
```bash
python -m app.init_db --drop
python -m app.init_db
```

### Using SQLAlchemy Shell
```python
from app.database import SessionLocal, Transaction
db = SessionLocal()

# Query transactions
transactions = db.query(Transaction).filter(
    Transaction.user_address == "0x1234..."
).all()
```

---

## 🔄 Syncing with Blockchain

To sync on-chain transactions to the database, you can:

1. **Listen to blockchain events** from your smart contracts
2. **Call the API** when transactions occur:
   ```python
   import requests
   
   # When a loan is issued
   requests.post("http://localhost:8000/api/transactions", json={
       "user_address": borrower_address,
       "transaction_type": "loan_issued",
       "amount": principal_amount,
       "loan_id": loan_id,
       "tx_hash": tx_hash,
       "transaction_timestamp": datetime.utcnow().isoformat() + "Z",
       "status": "confirmed"
   })
   ```

3. **Periodic sync job**: Query blockchain for recent transactions and sync to DB

---

## 📊 Example Queries

### Get total borrowed by user
```python
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Transaction

db = SessionLocal()
total = db.query(func.sum(Transaction.amount)).filter(
    Transaction.user_address == "0x1234...",
    Transaction.transaction_type == "borrow"
).scalar()
```

### Get repayment history for a loan
```python
repayments = db.query(Transaction).filter(
    Transaction.loan_id == 1,
    Transaction.transaction_type == "repay"
).order_by(Transaction.transaction_timestamp).all()
```

---

## 🛠️ Troubleshooting

### SQLite: "database is locked"
- Close other connections to the database file
- Ensure only one process is accessing it

### PostgreSQL: Connection refused
- Check if PostgreSQL is running: `pg_isready`
- Verify connection string format
- Check firewall settings

### Import errors
- Ensure you're in the `backend` directory
- Install dependencies: `pip install -r requirements.txt`

---

## 📚 Additional Resources

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Database Guide](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)
- [Supabase Documentation](https://supabase.com/docs)


