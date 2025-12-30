# Alembic Setup Guide

This guide will walk you through setting up Alembic for database migrations.

## Prerequisites

- PostgreSQL database is running
- Database `hr_ai_agent` is created (or use your preferred database name)
- `.env` file is configured with `DATABASE_URL`

## Step-by-Step Setup

### Step 1: Create the Database

First, create the PostgreSQL database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create the database
CREATE DATABASE hr_ai_agent;

# Exit psql
\q
```

Or if you're using a different database name, update `DATABASE_URL` in your `.env` file.

### Step 2: Initialize Alembic (First Time Only)

If Alembic is not already initialized, run:

```bash
cd backend
alembic init alembic
```

**Note:** Alembic is already initialized in this project, so you can skip this step.

### Step 3: Configure Alembic

The `alembic.ini` file is already configured. Verify that the `sqlalchemy.url` line is present (it will be overridden by `env.py`).

The `alembic/env.py` file is already configured to:
- Use settings from `app.config`
- Import all models from `app.models`
- Use the `DATABASE_URL` from environment variables

### Step 4: Create Initial Migration

Generate the initial migration based on your models:

```bash
cd backend
alembic revision --autogenerate -m "Initial migration - users, hr_requests, chat_sessions"
```

This will:
- Scan your SQLAlchemy models in `app/models/`
- Compare them with the current database state
- Generate a migration file in `alembic/versions/`

### Step 5: Review the Migration

Open the generated migration file in `alembic/versions/` and review it. It should create:
- `users` table
- `hr_requests` table
- `chat_sessions` table
- All indexes and foreign keys

**Important:** Always review auto-generated migrations before applying them!

### Step 6: Apply the Migration

Apply the migration to create the tables:

```bash
alembic upgrade head
```

This will:
- Connect to your database using `DATABASE_URL` from `.env`
- Execute the migration
- Create all tables, indexes, and constraints

### Step 7: Verify Tables Created

Verify that tables were created:

```bash
# Connect to PostgreSQL
psql -U postgres -d hr_ai_agent

# List tables
\dt

# You should see:
# - users
# - hr_requests
# - chat_sessions

# Exit
\q
```

## Creating New Migrations

When you modify models, create a new migration:

```bash
# Generate migration
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file

# Apply migration
alembic upgrade head
```

## Common Commands

```bash
# Show current migration status
alembic current

# Show migration history
alembic history

# Rollback last migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Upgrade to latest
alembic upgrade head

# Create empty migration (manual)
alembic revision -m "Description"
```

## Troubleshooting

### Error: "Target database is not up to date"

If you get this error, it means there are pending migrations:

```bash
# Check current status
alembic current

# Apply pending migrations
alembic upgrade head
```

### Error: "Can't locate revision identified by"

This happens when the database and migration files are out of sync. You may need to:

1. Check what's in the database:
```bash
alembic current
```

2. If needed, stamp the database with the current revision:
```bash
alembic stamp head
```

### Error: "No such table"

If tables don't exist, make sure:
1. Migration was created: `alembic revision --autogenerate -m "Initial migration"`
2. Migration was applied: `alembic upgrade head`
3. Database connection is correct in `.env`

### Reset Database (Development Only)

**Warning:** This will delete all data!

```bash
# Drop all tables
alembic downgrade base

# Recreate from scratch
alembic upgrade head
```

## Next Steps

After setting up Alembic:

1. Seed the database with sample users:
```bash
python -m app.seeds.seed_users
```

2. Initialize Qdrant and ingest policies:
```bash
python -c "from app.services.rag_service import ingest_policy_documents; ingest_policy_documents()"
```

3. Start the server:
```bash
uvicorn app.main:app --reload
```


