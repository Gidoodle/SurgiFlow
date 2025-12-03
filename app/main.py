from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Base, engine

# Routers
from app.api.patient_routes import router as patient_router
from app.api.patient_file_routes import router as patient_file_router
from app.api.patient_create_full import router as patient_full_router

# Import models so SQLAlchemy registers tables
from app.models import patient, patient_file

# Create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow frontend to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under /api/*
app.include_router(patient_router, prefix="/api")
app.include_router(patient_file_router, prefix="/api")
app.include_router(patient_full_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "SurgiFlow backend online"}
