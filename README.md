# clinic-api

A FastAPI healthcare API using Snowflake Snowpark, SQLModel schemas, Pytest, and Postman.

### Features
- FastAPI REST API
- Snowflake Snowpark session created on API startup (via lifespan events)
- Temporary Snowflake tables/views created from SQLModel-defined schemas
- Seed healthcare test data on startup
- dev/prod environment split
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
```

### Create Database and Set Up Environment Files
This project only creates schemas/tables/views automatically — it does not create the database itself. Run this once in a SQL file:
```sql
CREATE DATABASE IF NOT EXISTS CLINIC_DB;
```

Edit .env.dev and .env.prod files with your real Snowflake credentials:
- Use Account identifier for SNOWFLAKE_ACCOUNT
- For SNOWFLAKE_ROLE and SNOWFLAKE_WAREHOUSE, use:
  ```sql
  SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE();
  ```
- Use CLINIC_DB for SNOWFLAKE_DATABASE

### Run the App
```bash
ENV=dev uvicorn app.main:app --reload
```

This automatically creates the schema, tables, view, and seed data in Snowflake. Use `ENV=prod` instead of `ENV=dev` to run in prod mode (adds a `cost` field to prescriptions).

### Verify
Open a second terminal and run:
```bash
curl http://localhost:8000/health
curl -H "X-User-Id: 1" http://localhost:8000/prescriptions
```

You should get a healthy status and a list of prescriptions. In `prod` mode, prescriptions will also include a `cost` field.

### 8. Test Authorization Rules (server running in prod mode)
```bash
# Patient denied editing a prescription (expect 403)
curl -i -X PATCH -H "X-User-Id: 1" -H "Content-Type: application/json" -d '{"dosage": "20mg"}' http://localhost:8000/prescriptions/1

# Provider allowed (expect 200)
curl -i -X PATCH -H "X-User-Id: 3" -H "Content-Type: application/json" -d '{"dosage": "20mg", "cost": 15.0}' http://localhost:8000/prescriptions/1

# Patient denied editing someone else's insurance (expect 403)
curl -i -X PATCH -H "X-User-Id: 2" -H "Content-Type: application/json" -d '{"insurance_policy_number": "POL-HACK"}' http://localhost:8000/patients/1/insurance

# Patient allowed editing their own insurance (expect 200)
curl -i -X PATCH -H "X-User-Id: 1" -H "Content-Type: application/json" -d '{"insurance_policy_number": "POL-NEW"}' http://localhost:8000/patients/1/insurance
```

### Generate a Report
```bash
curl -H "X-User-Id: 4" "http://localhost:8000/reports/prescriptions?fmt=csv" -o report.csv
cat report.csv
```

### Run the Postman collection
Import `postman/collection.json` into Postman, then run all 10 requests against the running server. Confirm you see `200`/`201` for allowed actions and `403` for denied ones.

### Run the Automated Tests
```bash
pytest -v
```

Expected: 7 passed.
