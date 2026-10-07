from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator


class RecipientInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be blank")
        return value


class GenerationRequest(BaseModel):
    event_name: str = Field(min_length=2, max_length=200)
    event_date: date
    recipients: list[RecipientInput] = Field(min_length=1, max_length=500)

    @field_validator("event_name")
    @classmethod
    def validate_event_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Event name cannot be blank")
        return value


class JobResponse(BaseModel):
    job_id: int
    status: str
    total: int
    successful: int
    failed: int


class CertificateResponse(BaseModel):
    certificate_id: int
    recipient_name: str
    recipient_email: str
    status: str
    error_message: str | None = None
    download_url: str | None = None
