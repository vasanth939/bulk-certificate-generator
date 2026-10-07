from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Certificate, GenerationJob
from ..schemas import CertificateResponse, GenerationRequest, JobResponse
from ..services.job_processor import process_job

router = APIRouter(prefix="/api", tags=["Certificates"])


def _job_response(job: GenerationJob) -> JobResponse:
    return JobResponse(
        job_id=job.id,
        status=job.status,
        total=job.total,
        successful=job.successful,
        failed=job.failed,
    )


@router.post("/jobs", response_model=JobResponse, status_code=201)
def create_generation_job(
    request: GenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = GenerationJob(
        event_name=request.event_name,
        event_date=request.event_date.isoformat(),
        total=len(request.recipients),
        status="pending",
    )
    db.add(job)
    db.flush()

    for recipient in request.recipients:
        db.add(
            Certificate(
                job_id=job.id,
                recipient_name=recipient.name,
                recipient_email=str(recipient.email),
                status="pending",
            )
        )

    db.commit()
    db.refresh(job)
    background_tasks.add_task(process_job, job.id)
    return _job_response(job)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_response(job)


@router.get("/jobs/{job_id}/certificates", response_model=list[CertificateResponse])
def list_job_certificates(job_id: int, db: Session = Depends(get_db)):
    job = db.get(GenerationJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    certificates = (
        db.query(Certificate)
        .filter(Certificate.job_id == job_id)
        .order_by(Certificate.id)
        .all()
    )

    return [
        CertificateResponse(
            certificate_id=certificate.id,
            recipient_name=certificate.recipient_name,
            recipient_email=certificate.recipient_email,
            status=certificate.status,
            error_message=certificate.error_message,
            download_url=(
                f"/api/certificates/{certificate.id}/download"
                if certificate.status == "completed"
                else None
            ),
        )
        for certificate in certificates
    ]


@router.get("/certificates/{certificate_id}/download")
def download_certificate(certificate_id: int, db: Session = Depends(get_db)):
    certificate = db.get(Certificate, certificate_id)
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")

    if certificate.status != "completed" or not certificate.file_path:
        raise HTTPException(status_code=409, detail="Certificate is not ready for download")

    path = Path(certificate.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Generated file not found")

    return FileResponse(path=str(path), media_type="application/pdf", filename=path.name)
