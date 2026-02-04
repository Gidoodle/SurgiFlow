from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
import shutil
import os

from app.core.db import get_db
from app.models.patient_file import PatientFile
from app.models.patient import Patient
from app.schemas.patient_file import PatientFileOut

# Optional / future
from app.utils.pdf_parser import ocr_first_page, parse_patient_data


router = APIRouter(prefix="/patient-files", tags=["Patient Files"])

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# =========================================================
# FUTURE: OCR / INTAKE MODE (KEEP, BUT DO NOT USE IN MVP)
# =========================================================
@router.post("/", response_model=PatientFileOut)
async def upload_patient_file_ocr(
    uploaded_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    FUTURE MODE (NOT USED IN MVP)
    Upload → OCR → auto-create patient → attach file
    """

    save_path = f"{UPLOAD_DIR}/{uploaded_file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

    text = ocr_first_page(save_path)
    parsed = parse_patient_data(text)

    patient = Patient(
        full_name=parsed.get("full_name"),
        preferred_name=parsed.get("preferred_name"),
        id_number=parsed.get("id_number"),
        email=parsed.get("email"),
        phone=parsed.get("phone"),
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    record = PatientFile(
        patient_id=patient.id,
        file_path=save_path,
        filename=uploaded_file.filename
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


# =========================================================
# MVP: UPLOAD FILE AND ATTACH TO EXISTING PATIENT
# =========================================================
@router.post("/upload-and-assign")
async def upload_and_assign_file(
    patient_id: int = Form(...),
    uploaded_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    MVP ENDPOINT (USED BY PATIENT DETAIL PAGE)

    - Upload file
    - Attach directly to existing patient
    - No OCR
    - No patient creation
    """

    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    save_path = f"{UPLOAD_DIR}/{uploaded_file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

    record = PatientFile(
        patient_id=patient.id,
        file_path=save_path,
        filename=uploaded_file.filename
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "id": record.id,
        "patient_id": record.patient_id,
        "filename": record.filename,
        "file_path": record.file_path
    }


# =========================================================
# LIST FILES FOR PATIENT (PATIENT DETAIL PAGE)
# =========================================================
@router.get("/by-patient/{patient_id}")
def list_files_for_patient(
    patient_id: int,
    db: Session = Depends(get_db)
):
    return (
        db.query(PatientFile)
        .filter(PatientFile.patient_id == patient_id)
        .all()
    )
