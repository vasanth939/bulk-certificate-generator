# Bulk Certificate Generator API

A FastAPI backend that accepts a single bulk request, validates recipients, generates one PDF certificate per valid recipient, tracks progress, and exposes generated certificates for download.

## Assignment requirements covered

- Bulk certificate generation from one API request
- Recipient input validation
- One predefined certificate design
- Relational database using SQLAlchemy + SQLite
- Background processing using FastAPI `BackgroundTasks`
- Per-certificate status and error tracking
- Job-level progress: total, successful, failed
- Partial failure handling: one failed certificate does not stop other recipients
- Certificate retrieval/download
- Automated tests for all required areas
- Swagger/OpenAPI documentation at `/docs`

## Tech stack

- Python 3.10+
- FastAPI
- Pydantic v2
- SQLAlchemy 2
- SQLite
- ReportLab
- Pytest + HTTPX

## Project structure

```text
bulk-certificate-generator/
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes/
│   │   └── certificates.py
│   └── services/
│       ├── certificate_generator.py
│       └── job_processor.py
├── generated/
├── templates/
├── tests/
│   ├── conftest.py
│   ├── test_generation.py
│   ├── test_jobs.py
│   ├── test_failure_handling.py
│   └── test_progress.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup

Open a terminal in the project directory.

### 1. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the API

```bash
uvicorn app.main:app --reload
```

Open Swagger UI:

`http://127.0.0.1:8000/docs`

Health check:

`http://127.0.0.1:8000/health`

## API workflow

### 1. Create a bulk generation job

`POST /api/jobs`

Example:

```json
{
  "event_name": "Python Workshop",
  "event_date": "2026-10-10",
  "recipients": [
    {
      "name": "Vasanth Kumar",
      "email": "vasanth@example.com"
    },
    {
      "name": "Rahul Kumar",
      "email": "rahul@example.com"
    }
  ]
}
```

The request creates one job and one certificate record per recipient. The API returns a `job_id` immediately and schedules the generation work as a background task.

Example response:

```json
{
  "job_id": 1,
  "status": "pending",
  "total": 2,
  "successful": 0,
  "failed": 0
}
```

### 2. Check job progress

`GET /api/jobs/{job_id}`

Example completed response:

```json
{
  "job_id": 1,
  "status": "completed",
  "total": 2,
  "successful": 2,
  "failed": 0
}
```

Possible statuses:

- `pending`
- `processing`
- `completed`
- `completed_with_errors`
- `failed`

### 3. List certificates for a job

`GET /api/jobs/{job_id}/certificates`

Example:

```json
[
  {
    "certificate_id": 1,
    "recipient_name": "Vasanth Kumar",
    "recipient_email": "vasanth@example.com",
    "status": "completed",
    "error_message": null,
    "download_url": "/api/certificates/1/download"
  }
]
```

### 4. Download a generated certificate

`GET /api/certificates/{certificate_id}/download`

The endpoint returns the generated PDF file.

## Validation

Pydantic validates:

- Recipient name: 2 to 200 characters
- Recipient email: valid email format
- Event name: 2 to 200 characters
- Event date: valid ISO date such as `2026-10-10`
- Recipient list: 1 to 500 recipients

Invalid input returns HTTP `422`.

## Certificate generation

The project uses one predefined ReportLab design in `app/services/certificate_generator.py`.

The generated PDF contains:

- Certificate title
- Recipient name
- Event name
- Event date
- Fixed certificate footer

The assignment does not require a template editor or multiple designs, so keeping the design in code makes the project simple and reproducible.

## Failure handling

Each certificate is generated inside its own `try/except` block.

If one recipient fails:

1. That certificate is marked `failed`.
2. The error message is saved in the database.
3. The job's `failed` counter is incremented.
4. Processing continues with the remaining recipients.
5. If at least one certificate succeeds and another fails, the job ends as `completed_with_errors`.

This prevents a single bad certificate from unnecessarily cancelling the complete bulk request.

## Background processing decision

FastAPI `BackgroundTasks` is used because certificate creation is work that can happen after the API has returned the job ID.

This is appropriate for an interview assignment because it requires no extra infrastructure and clearly demonstrates asynchronous-style job processing and status tracking.

For a production system with very large workloads, I would move the processing to a durable queue such as Celery/RQ with Redis and use PostgreSQL instead of SQLite. Generated PDFs could be stored in object storage such as Amazon S3.

## Testing

Run all tests:

```bash
python -m pytest -q
```

The test suite covers:

- Creating a generation job
- Input validation
- PDF certificate generation
- Job status/progress
- Individual certificate failure without stopping the bulk job
- Listing generated certificates
- Certificate download
- Missing job handling

## Interview explanation

### Why FastAPI?

FastAPI provides automatic validation through Pydantic, OpenAPI/Swagger documentation, clean dependency injection, and a small amount of code for REST APIs.

### Why a relational database?

The assignment requires a relational database. The design uses two related tables: `generation_jobs` and `certificates`. One job has many certificates.

### Why store certificate status in the database?

The client needs to check progress after submitting a bulk request. Database status makes the job state persistent and allows the API to report successful and failed recipients.

### How does partial failure work?

Each certificate is processed independently. Exceptions are caught for an individual certificate, recorded, and processing continues with the next certificate.

### How would you scale it?

I would replace SQLite with PostgreSQL, use a persistent task queue such as Celery/RQ with Redis, and store PDFs in object storage. Multiple workers could then process certificates concurrently.

### What happens if the API process restarts?

With the current `BackgroundTasks` design, in-memory background work is not a durable queue. A production implementation would use a persistent queue so unfinished work can be retried after a restart.

## Example curl request

```bash
curl -X POST "http://127.0.0.1:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "event_name": "Python Workshop",
    "event_date": "2026-10-10",
    "recipients": [
      {"name": "Vasanth Kumar", "email": "vasanth@example.com"},
      {"name": "Rahul Kumar", "email": "rahul@example.com"}
    ]
  }'
```
