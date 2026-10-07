from app.models import Certificate


def test_certificate_generation_and_status(client):
    payload = {
        "event_name": "AI Workshop",
        "event_date": "2026-10-11",
        "recipients": [
            {"name": "Test User", "email": "test@example.com"},
        ],
    }

    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 201

    job_id = response.json()["job_id"]

    # BackgroundTasks execute before TestClient returns the response.
    status_response = client.get(f"/api/jobs/{job_id}")
    assert status_response.status_code == 200

    status = status_response.json()
    assert status["total"] == 1
    assert status["successful"] == 1
    assert status["failed"] == 0
    assert status["status"] == "completed"

    certs = client.get(f"/api/jobs/{job_id}/certificates")
    assert certs.status_code == 200
    data = certs.json()
    assert len(data) == 1
    assert data[0]["status"] == "completed"

    download = client.get(f"/api/certificates/{data[0]['certificate_id']}/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"


def test_missing_job(client):
    response = client.get("/api/jobs/99999")
    assert response.status_code == 404
