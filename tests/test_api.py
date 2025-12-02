from fastapi.testclient import TestClient
from sqlmodel import Session, select
from models import Job, ShiftStats

def test_status_initial(client: TestClient):
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["active_job"] is None
    assert data["shift"]["total_pieces"] == 0

def test_start_job(client: TestClient):
    response = client.post("/api/job/start", json={
        "expected_barcode": "123456",
        "pieces_per_shipper": 10,
        "target_quantity": 100
    })
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["job"]["expected_barcode"] == "123456"
    assert data["job"]["is_active"] is True

def test_scan_pass(client: TestClient):
    # Start job first
    client.post("/api/job/start", json={"expected_barcode": "ABC"})
    
    # Scan correct barcode
    response = client.post("/api/scan", json={"barcode": "ABC"})
    assert response.status_code == 200
    data = response.json()
    assert data["scan"]["status"] == "PASS"
    assert data["job"]["pass_count"] == 1
    assert data["job"]["fail_count"] == 0

def test_scan_fail(client: TestClient):
    # Start job first
    client.post("/api/job/start", json={"expected_barcode": "ABC"})
    
    # Scan wrong barcode
    response = client.post("/api/scan", json={"barcode": "XYZ"})
    assert response.status_code == 200
    data = response.json()
    assert data["scan"]["status"] == "FAIL"
    assert data["job"]["pass_count"] == 0
    assert data["job"]["fail_count"] == 1

def test_end_job(client: TestClient):
    # Start job
    client.post("/api/job/start", json={"expected_barcode": "ABC"})
    
    # End job with correct PIN
    response = client.post("/api/job/end", json={"pin": "1234"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["summary"]["pass_count"] == 0
    
    # Verify status is inactive
    status = client.get("/api/status").json()
    assert status["active_job"] is None

def test_end_job_wrong_pin(client: TestClient):
    client.post("/api/job/start", json={"expected_barcode": "ABC"})
    response = client.post("/api/job/end", json={"pin": "0000"})
    assert response.status_code == 403

def test_export_csv(client: TestClient):
    response = client.get("/api/export_csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")

def test_backup(client: TestClient):
    response = client.get("/api/backup")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
