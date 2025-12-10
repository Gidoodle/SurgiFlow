from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import prom_schedule

from app.core.config import Base, engine

# Import models so SQLAlchemy registers tables
from app.models import (
    patient,
    patient_file,
    case_episode
)

# Routers
from app.api.patient_routes import router as patient_router
from app.api.patient_file_routes import router as patient_file_router
from app.api.patient_create_full import router as patient_full_router
from app.api.case_routes import router as case_router
from app.api.prom_routes import router as prom_router   # <-- NEW CLEAN PROM ROUTES

# Create DB tables
Base.metadata.create_all(bind=engine)

# FastAPI app
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
app.include_router(case_router, prefix="/api")
app.include_router(prom_router, prefix="/api")   # CLEAN JSON PROMS

@app.get("/")
def root():
    return {"status": "SurgiFlow backend online"}
