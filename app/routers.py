import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app import db
from app.auth import get_current_user, is_staff
from app.reports import build_prescription_report


router = APIRouter()


class AppointmentCreate(BaseModel):
    provider_id: int


class PrescriptionUpdate(BaseModel):
    medication: Optional[str] = None
    dosage: Optional[str] = None
    status: Optional[str] = None
    cost: Optional[float] = None


class InsuranceUpdate(BaseModel):
    insurance_policy_number: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/appointments", status_code=201)
def create_appointment(
    payload: AppointmentCreate,
    request: Request,
    user=Depends(get_current_user),
):
    if user["role"] != "patient":
        raise HTTPException(status_code=403, detail="Only patients can book appointments")

    patient = db.row(
        request.app.state.sf,
        f"select id from patients where user_id = {user['id']}",
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found")

    provider = db.row(
        request.app.state.sf,
        f"select id from users where id = {payload.provider_id} and role = 'provider'",
    )

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    appointment_id = int(time.time() * 1000)

    db.execute(
        request.app.state.sf,
        f"""
        insert into appointments (id, patient_id, provider_id, status)
        values ({appointment_id}, {patient['id']}, {payload.provider_id}, 'pending')
        """,
    )

    print(f"EVENT: notify provider {payload.provider_id} for appointment {appointment_id}")

    return {
        "id": appointment_id,
        "patient_id": patient["id"],
        "provider_id": payload.provider_id,
        "status": "pending",
    }


@router.get("/appointments")
def list_appointments(request: Request, user=Depends(get_current_user)):
    return db.rows(
        request.app.state.sf,
        "select id, patient_id, provider_id, status from appointments order by id",
    )


@router.get("/prescriptions")
def list_prescriptions(request: Request, user=Depends(get_current_user)):
    return db.rows(
        request.app.state.sf,
        "select * from prescriptions order by id",
    )


@router.patch("/prescriptions/{prescription_id}")
def update_prescription(
    prescription_id: int,
    payload: PrescriptionUpdate,
    request: Request,
    user=Depends(get_current_user),
):
    if not is_staff(user):
        raise HTTPException(
            status_code=403,
            detail="Only providers/admins can update prescriptions",
        )

    updates = []

    if payload.medication is not None:
        updates.append(f"medication = {db.q(payload.medication)}")

    if payload.dosage is not None:
        updates.append(f"dosage = {db.q(payload.dosage)}")

    if payload.status is not None:
        updates.append(f"status = {db.q(payload.status)}")

    if payload.cost is not None:
        if request.app.state.env != "prod":
            raise HTTPException(status_code=400, detail="Cost is prod-only")
        updates.append(f"cost = {payload.cost}")

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    existing = db.row(
        request.app.state.sf,
        f"select id from prescriptions where id = {prescription_id}",
    )

    if not existing:
        raise HTTPException(status_code=404, detail="Prescription not found")

    db.execute(
        request.app.state.sf,
        f"update prescriptions set {', '.join(updates)} where id = {prescription_id}",
    )

    return {"id": prescription_id, "updated": True}


@router.patch("/patients/{patient_id}/insurance")
def update_insurance(
    patient_id: int,
    payload: InsuranceUpdate,
    request: Request,
    user=Depends(get_current_user),
):
    patient = db.row(
        request.app.state.sf,
        f"select id, user_id from patients where id = {patient_id}",
    )

    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    owns_record = patient["user_id"] == user["id"]

    if not owns_record and not is_staff(user):
        raise HTTPException(
            status_code=403,
            detail="Cannot update another patient's insurance",
        )

    db.execute(
        request.app.state.sf,
        f"""
        update patients
        set insurance_policy_number = {db.q(payload.insurance_policy_number)}
        where id = {patient_id}
        """,
    )

    return {"patient_id": patient_id, "updated": True}


@router.get("/reports/prescriptions")
def prescription_report(
    request: Request,
    fmt: str = "csv",
    user=Depends(get_current_user),
):
    if fmt not in {"csv", "xlsx"}:
        raise HTTPException(status_code=400, detail="fmt must be csv or xlsx")

    path, media_type = build_prescription_report(request.app.state.sf, fmt)

    filename = f"prescription_report.{fmt}"

    return FileResponse(
        path,
        filename=filename,
        media_type=media_type,
    )