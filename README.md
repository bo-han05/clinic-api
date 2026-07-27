# clinic-api

A FastAPI healthcare API using Snowflake Snowpark, SQLModel schemas, Pytest, and Postman.

### Features
- FastAPI REST API
- Snowflake Snowpark session created on API startup (via lifespan events)
- Temporary Snowflake tables/views created from SQLModel-backed schema definitions
- Seed healthcare test data on startup
- Dev/prod environment split
  - `dev`: prescription table excludes `cost`
  - `prod`: prescription table includes `cost`
- Role-based authorization
  - patients
  - providers
  - admins
- Ownership-based patient data update rules
- Appointment booking with fake event trigger
- CSV/XLSX prescription report generation
- Pytest and Postman validation examples

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.dev.example .env.dev
cp .env.prod.example .env.prod
