from fastapi import FastAPI

# Import database + Base from config
from app.core.config import Base, engine

# Import routers
from app.api.patient_routes import router as patient_router

# Create tables
Base.metadata.create_all(bind=engine)

# Init app
app = FastAPI(title="SurgiFlow Backend")

# Register routers
app.include_router(patient_router, prefix="/patients", tags=["Patients"])


@app.get("/")
def root():
    return {"status": "SurgiFlow backend online"}
