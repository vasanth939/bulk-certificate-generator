def test_job_progress_fields_are_returned(client):
    payload = {
        "event_name": "Progress Workshop",
        "event_date": "2026-10-12",
        "recipients": [
            {"name": "One User", "email": "one@example.com"},
            {"name": "Two User", "email": "two@example.com"},
        ],
    }

    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert set(["job_id", "status", "total", "successful", "failed"]).issubset(data)
    assert data["total"] == 2
    assert data["successful"] == 0
    assert data["failed"] == 0

    status = client.get(f"/api/jobs/{data['job_id']}").json()
    assert status["total"] == 2
    assert status["successful"] + status["failed"] == status["total"]
    assert status["status"] == "completed"
