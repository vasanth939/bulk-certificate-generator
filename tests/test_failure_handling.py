from app.models import Certificate


def test_individual_certificate_failure_does_not_stop_bulk_job(client, monkeypatch):
    import app.services.job_processor as job_processor

    original_generator = job_processor.generate_certificate

    def failing_generator(recipient_name, event_name, event_date, certificate_id):
        if recipient_name == "Bad Recipient":
            raise RuntimeError("simulated PDF generation failure")
        return original_generator(recipient_name, event_name, event_date, certificate_id)

    monkeypatch.setattr(job_processor, "generate_certificate", failing_generator)

    payload = {
        "event_name": "Failure Handling Workshop",
        "event_date": "2026-10-10",
        "recipients": [
            {"name": "Good Recipient", "email": "good@example.com"},
            {"name": "Bad Recipient", "email": "bad@example.com"},
            {"name": "Another Good", "email": "another@example.com"},
        ],
    }

    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 201
    job_id = response.json()["job_id"]

    status = client.get(f"/api/jobs/{job_id}").json()
    assert status["total"] == 3
    assert status["successful"] == 2
    assert status["failed"] == 1
    assert status["status"] == "completed_with_errors"

    certificates = client.get(f"/api/jobs/{job_id}/certificates").json()
    assert [item["status"] for item in certificates] == ["completed", "failed", "completed"]
    assert certificates[1]["error_message"] == "simulated PDF generation failure"
    assert certificates[0]["download_url"] is not None
    assert certificates[2]["download_url"] is not None
