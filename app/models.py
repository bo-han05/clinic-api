from typing import Optional
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    role: str  # patient, provider, admin

class Patient(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    insurance_policy_number: str

class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int
    provider_id: int
    status: str

class Prescription(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    patient_id: int
    medication: str
    dosage: str
    status: str
    cost: Optional[float] = None  # prod-only column

MODELS = [User, Patient, Appointment, Prescription]


def table_name(model: type[SQLModel]) -> str:
    return model.__name__.lower() + "s"

def columns_for(model: type[SQLModel], env: str) -> list[str]:
    if model is User:
        return [
            "id number primary key",
            "name varchar",
            "role varchar",
        ]

    if model is Patient:
        return [
            "id number primary key",
            "user_id number",
            "insurance_policy_number varchar",
        ]

    if model is Appointment:
        return [
            "id number primary key",
            "patient_id number",
            "provider_id number",
            "status varchar",
        ]

    if model is Prescription:
        cols = [
            "id number primary key",
            "patient_id number",
            "medication varchar",
            "dosage varchar",
            "status varchar",
        ]
        if env == "prod":
            cols.append("cost float")
        return cols

    raise ValueError(f"Unknown model: {model}")