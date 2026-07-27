import os
import pytest
import pandas as pd

os.environ["TESTING"] = "1"
os.environ["ENV"] = "prod"

from fastapi.testclient import TestClient
from app.main import app
from app import db


class FakeDB:
    def __init__(self):
        self.users = {
            1: {"id": 1, "name": "Alice Patient", "role": "patient"},
            2: {"id": 2, "name": "Bob Patient", "role": "patient"},
            3: {"id": 3, "name": "Dr. Smith", "role": "provider"},
            4: {"id": 4, "name": "Admin User", "role": "admin"},
        }

        self.patients = {
            1: {"id": 1, "user_id": 1, "insurance_policy_number": "POL-A111"},
            2: {"id": 2, "user_id": 2, "insurance_policy_number": "POL-B222"},
        }

        self.prescriptions = {
            1: {
                "id": 1,
                "patient_id": 1,
                "medication": "Atorvastatin",
                "dosage": "10mg",
                "status": "active",
                "cost": 12.5,
            }
        }

        self.appointments = {
            1: {"id": 1, "patient_id": 1, "provider_id": 3, "status": "confirmed"}
        }

    def row(self, sf, sql):
        sql = sql.lower()

        if "from users" in sql:
            for user in self.users.values():
                if f"id = {user['id']}" in sql and (
                    "role = 'provider'" not in sql or user["role"] == "provider"
                ):
                    return user

        if "from patients" in sql:
            if "where user_id" in sql:
                uid = int(sql.split("user_id =")[1].strip().split()[0])
                return next((p for p in self.patients.values() if p["user_id"] == uid), None)

            if "where id" in sql:
                pid = int(sql.split("id =")[1].strip().split()[0])
                return self.patients.get(pid)

        if "from prescriptions" in sql:
            pid = int(sql.split("id =")[1].strip().split()[0])
            return self.prescriptions.get(pid)

        return None

    def rows(self, sf, sql):
        sql = sql.lower()

        if "from appointments" in sql:
            return list(self.appointments.values())

        if "from prescriptions" in sql:
            return list(self.prescriptions.values())

        return []

    def execute(self, sf, sql):
        sql_low = sql.lower()

        if "insert into appointments" in sql_low:
            values = sql_low.split("values")[1]
            nums = [x.strip(" ()'\n") for x in values.split(",")]
            appointment_id = int(nums[0])
            patient_id = int(nums[1])
            provider_id = int(nums[2])
            self.appointments[appointment_id] = {
                "id": appointment_id,
                "patient_id": patient_id,
                "provider_id": provider_id,
                "status": "pending",
            }

        if "update prescriptions" in sql_low:
            if "dosage" in sql_low:
                self.prescriptions[1]["dosage"] = "20mg"
            if "cost" in sql_low:
                self.prescriptions[1]["cost"] = 15.0

        if "update patients" in sql_low:
            self.patients[1]["insurance_policy_number"] = "POL-NEW"

        return []

    def dataframe(self, sf, sql):
        return pd.DataFrame(
            [
                {
                    "PATIENT_ID": 1,
                    "PATIENT_NAME": "Alice Patient",
                    "PRESCRIPTION_COUNT": 1,
                    "TOTAL_COST": 12.5,
                }
            ]
        )


@pytest.fixture
def client(monkeypatch):
    fake = FakeDB()

    app.state.sf = object()
    app.state.env = "prod"

    monkeypatch.setattr(db, "row", fake.row)
    monkeypatch.setattr(db, "rows", fake.rows)
    monkeypatch.setattr(db, "execute", fake.execute)
    monkeypatch.setattr(db, "dataframe", fake.dataframe)

    return TestClient(app)