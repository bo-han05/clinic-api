def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_patient_can_book_appointment(client):
    res = client.post(
        "/appointments",
        headers={"X-User-Id": "1"},
        json={"provider_id": 3},
    )

    assert res.status_code == 201
    assert res.json()["status"] == "pending"


def test_patient_cannot_update_prescription(client):
    res = client.patch(
        "/prescriptions/1",
        headers={"X-User-Id": "1"},
        json={"dosage": "20mg"},
    )

    assert res.status_code == 403


def test_provider_can_update_prescription(client):
    res = client.patch(
        "/prescriptions/1",
        headers={"X-User-Id": "3"},
        json={"dosage": "20mg", "cost": 15.0},
    )

    assert res.status_code == 200
    assert res.json()["updated"] is True


def test_patient_cannot_update_another_patient_insurance(client):
    res = client.patch(
        "/patients/1/insurance",
        headers={"X-User-Id": "2"},
        json={"insurance_policy_number": "POL-HACK"},
    )

    assert res.status_code == 403


def test_patient_can_update_own_insurance(client):
    res = client.patch(
        "/patients/1/insurance",
        headers={"X-User-Id": "1"},
        json={"insurance_policy_number": "POL-NEW"},
    )

    assert res.status_code == 200
    assert res.json()["updated"] is True


def test_report_csv(client):
    res = client.get(
        "/reports/prescriptions?fmt=csv",
        headers={"X-User-Id": "4"},
    )

    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]