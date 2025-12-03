from fastapi.testclient import TestClient
from sqlmodel import Session, select
from models import Job, Scan
from main import app, pin_attempts
import pytest


@pytest.fixture(autouse=True)
def reset_rate_limit():
    """Reset rate limit counters before each test"""
    pin_attempts.clear()
    yield
    pin_attempts.clear()


def test_race_condition_logic(client: TestClient):
    """Test that starting a second job fails (logic check for race condition)"""
    # 1. Start first job
    response = client.post(
        "/api/job/start", json={"expected_barcode": "JOB1", "pieces_per_shipper": 10}
    )
    assert response.status_code == 200

    # 2. Try to start second job immediately
    response = client.post(
        "/api/job/start", json={"expected_barcode": "JOB2", "pieces_per_shipper": 10}
    )
    assert response.status_code == 400
    assert "already active" in response.json()["error"]


def test_rate_limiting(client: TestClient):
    """Test PIN rate limiting"""
    # 1. Fail 5 times
    for _ in range(5):
        response = client.post("/api/verify_pin", json={"pin": "WRONG"})
        assert response.status_code == 403

    # 2. 6th attempt should be rate limited
    response = client.post("/api/verify_pin", json={"pin": "WRONG"})
    assert response.status_code == 429
    assert "Too many PIN attempts" in response.json()["error"]


def test_cached_counts(client: TestClient, session: Session):
    """Test that cached counts are updated correctly in the database"""
    # 1. Start job
    client.post("/api/job/start", json={"expected_barcode": "PASS123"})

    # 2. Scan items (3 PASS, 2 FAIL)
    client.post("/api/scan", json={"barcode": "PASS123"})  # Pass
    client.post("/api/scan", json={"barcode": "PASS123"})  # Pass
    client.post("/api/scan", json={"barcode": "FAIL001"})  # Fail
    client.post("/api/scan", json={"barcode": "PASS123"})  # Pass
    client.post("/api/scan", json={"barcode": "FAIL002"})  # Fail

    # 3. Verify via API first
    status = client.get("/api/status").json()
    assert status["active_job"]["pass_count"] == 3
    assert status["active_job"]["fail_count"] == 2
    assert status["active_job"]["total_scans"] == 5

    # 4. Verify directly in DB (to ensure cached columns are used)
    job = session.exec(select(Job).where(Job.is_active == True)).first()
    assert job.cached_pass_count == 3
    assert job.cached_fail_count == 2
    assert job.cached_total_scans == 5


def test_input_validation(client: TestClient):
    """Test input validation for XSS and invalid data"""

    # 1. XSS Attempt
    response = client.post(
        "/api/job/start",
        json={"expected_barcode": "<script>alert(1)</script>", "pieces_per_shipper": 1},
    )
    assert response.status_code == 422
    assert "invalid characters" in str(response.json())

    # 2. Too Long
    response = client.post(
        "/api/job/start", json={"expected_barcode": "A" * 201, "pieces_per_shipper": 1}
    )
    assert response.status_code == 422
    assert "200 characters or less" in str(response.json())

    # 3. Invalid Pieces
    response = client.post(
        "/api/job/start", json={"expected_barcode": "VALID", "pieces_per_shipper": 0}
    )
    assert response.status_code == 422
    assert "at least 1" in str(response.json())

    # 4. Empty Barcode
    response = client.post(
        "/api/job/start", json={"expected_barcode": "   ", "pieces_per_shipper": 1}
    )
    assert response.status_code == 422  # Or 400 depending on where it's caught


def test_persistent_lock(client: TestClient, session: Session):
    """Test that failed scan locks the line and persists"""
    # 1. Start job
    client.post("/api/job/start", json={"expected_barcode": "PASS123"})

    # 2. Scan FAIL
    response = client.post("/api/scan", json={"barcode": "WRONG"})
    assert response.status_code == 200
    assert response.json()["scan"]["status"] == "FAIL"

    # 3. Verify Locked State
    status = client.get("/api/status").json()
    assert status["active_job"]["is_locked"] is True

    # 4. Verify DB State
    job = session.exec(select(Job).where(Job.is_active == True)).first()
    assert job.is_locked is True

    # 5. Try to scan while locked (should be 423)
    response = client.post("/api/scan", json={"barcode": "PASS123"})
    assert response.status_code == 423
    assert "locked" in response.json()["error"]

    # 6. Unlock with PIN
    response = client.post(
        "/api/verify_pin", json={"pin": "1234"}
    )  # Assuming 1234 is SUPERVISOR_PIN
    assert response.status_code == 200

    # 7. Verify Unlocked
    status = client.get("/api/status").json()
    assert status["active_job"]["is_locked"] is False

    # 8. Scan should work again
    response = client.post("/api/scan", json={"barcode": "PASS123"})
    assert response.status_code == 200
