# Quick Fix Instructions

## The Problem
SQLAlchemy reserves the name `metadata`, so we renamed it to `extra_metadata`. Your database tables need to be updated.

## Quick Fix (One Command)

I've created a script that will automatically:
1. ✅ Check your database
2. ✅ Migrate the `metadata` column to `extra_metadata` (if needed)
3. ✅ Create sample data

### Run this:

```bash
cd backend
python fix_and_setup.py
```

Or on Windows:
```bash
cd backend
run_fix.bat
```

## What the Script Does

1. **Checks existing tables** - Sees if you have tables with the old `metadata` column
2. **Migrates if needed** - Renames `metadata` → `extra_metadata` in PostgreSQL
3. **Recreates if needed** - For SQLite, drops and recreates tables
4. **Creates sample data** - Adds test transactions and loans

## Manual Steps (If Script Doesn't Work)

### Option 1: Recreate Tables (Loses existing data)

```bash
python -m app.init_db --drop
python -m app.init_db
python scripts/create_sample_data.py
```

### Option 2: Migrate (Keeps existing data - PostgreSQL only)

```bash
python scripts/migrate_metadata_column.py
python scripts/create_sample_data.py
```

## Verify It Worked

After running the fix, test it:

```bash
python scripts/create_sample_data.py
```

You should see:
```
✅ Sample data created successfully!
```

Then check your Supabase dashboard - you should see data in the tables!

