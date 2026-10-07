from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import Certificate, GenerationJob
from .certificate_generator import generate_certificate


def process_job(job_id: int) -> None:
    """Process every certificate independently so one failure does not stop the job."""
    db: Session = SessionLocal()
    try:
        job = db.get(GenerationJob, job_id)
        if not job:
            return

        job.status = "processing"
        db.commit()

        certificates = (
            db.query(Certificate)
            .filter(Certificate.job_id == job_id)
            .order_by(Certificate.id)
            .all()
        )

        for certificate in certificates:
            try:
                certificate.status = "processing"
                db.commit()

                file_path = generate_certificate(
                    recipient_name=certificate.recipient_name,
                    event_name=job.event_name,
                    event_date=job.event_date,
                    certificate_id=certificate.id,
                )

                certificate.status = "completed"
                certificate.file_path = file_path
                certificate.error_message = None
                job.successful += 1
                db.commit()

            except Exception as exc:
                certificate.status = "failed"
                certificate.error_message = str(exc)[:2000]
                job.failed += 1
                db.commit()

        if job.failed == 0:
            job.status = "completed"
        elif job.successful == 0:
            job.status = "failed"
        else:
            job.status = "completed_with_errors"
        db.commit()

    except Exception:
        # If a job-level database/unexpected error occurs, keep the state explicit.
        job = db.get(GenerationJob, job_id)
        if job:
            job.status = "failed"
            db.commit()
    finally:
        db.close()
