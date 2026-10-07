def test_create_generation_job(client):
    payload = {
        "event_name": "Python Workshop",
        "event_date": "2026-10-10",
        "recipients": [
            {"name": "Vasanth Kumar", "email": "vasanth@example.com"},
            {"name": "Rahul Kumar", "email": "rahul@example.com"},
        ],
    }

    response = client.post("/api/jobs", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["total"] == 2
    assert data["successful"] == 0
    assert data["failed"] == 0
    assert data["status"] == "pending"


def test_input_validation(client):
    payload = {
        "event_name": "Workshop",
        "event_date": "2026-10-10",
        "recipients": [
            {"name": "", "email": "not-an-email"},
        ],
    }

    response = client.post("/api/jobs", json=payload)
    assert response.status_code == 422
