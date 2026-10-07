from fastapi import FastAPI
from .database import Base, engine
from .routes.certificates import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator API",
    version="1.0.0",
    description="Backend API for bulk certificate generation and tracking.",
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Bulk Certificate Generator API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
