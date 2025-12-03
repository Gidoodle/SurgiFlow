from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.patient import Patient
from app.models.patient_file import PatientFile

import shutil
import os

router = APIRouter(prefix="/patients", tags=["Patients"])

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/create-full")
async def create_full_patient(
    uploaded_file: UploadFile = File(...),

    full_name: str = Form(...),
    preferred_name: str | None = Form(None),

    id_number: str | None = Form(None),
    email: str | None = Form(None),
    phone: str | None = Form(None),
    address: str | None = Form(None),

    age: int | None = Form(None),
    sex: str | None = Form(None),

    medical_aid: str | None = Form(None),
    medical_aid_number: str | None = Form(None),

    joint_type: str = Form(...),  # REQUIRED for PROM routing

    db: Session = Depends(get_db)
):
    # 1. Save file
    save_path = f"{UPLOAD_DIR}/{uploaded_file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

    # 2. Create patient
    patient = Patient(
        full_name=full_name,
        preferred_name=preferred_name,

        id_number=id_number,
        email=email,
        phone=phone,
        address=address,

        age=age,
        sex=sex,

        medical_aid=medical_aid,
        medical_aid_number=medical_aid_number,

        joint_type=joint_type
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    # 3. Create patient file
    file_record = PatientFile(
        patient_id=patient.id,
        file_path=save_path,
        filename=uploaded_file.filename
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)

    return {
        "patient": patient,
        "file": file_record
    }
