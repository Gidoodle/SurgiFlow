from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.core.db import get_db

from app.schemas.patient_file import PatientFileOut
from app.models.patient_file import PatientFile
from app.models.patient import Patient

from app.utils.pdf_parser import ocr_first_page, parse_patient_data

import shutil
import os


router = APIRouter(prefix="/patient-files", tags=["Patient Files"])

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------
# OLD ENDPOINT (OCR VERSION)
# Still available for future autofill mode
# ---------------------------------------------------------
@router.post("/", response_model=PatientFileOut)
async def upload_patient_file(
    uploaded_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    OCR VERSION:
    1. Save file
    2. OCR page 1
    3. Extract patient data
    4. Create new patient
    5. Link patient file
    """

    # 1. SAVE THE PDF
    save_path = f"{UPLOAD_DIR}/{uploaded_file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

    # 2. OCR PAGE 1
    text = ocr_first_page(save_path)

    print("---- OCR START ----")
    print(text)
    print("---- OCR END ----")

    # 3. PARSE OCR TEXT
    parsed = parse_patient_data(text)

    # 4. CREATE PATIENT
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

    # 5. CREATE PATIENT FILE RECORD
    record = PatientFile(
        patient_id=patient.id,
        file_path=save_path,
        filename=uploaded_file.filename
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record



# ---------------------------------------------------------
# NEW ENDPOINT (RAW UPLOAD VERSION FOR MVP)
# No OCR, No patient created — clean & stable
# ---------------------------------------------------------
@router.post("/upload-raw")
async def upload_raw_patient_file(
    uploaded_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    RAW UPLOAD VERSION (NO OCR, NO PATIENT CREATION)
    1. Save file to disk
    2. Create PatientFile with patient_id = None
    3. Return file_id so frontend/backend can later link patient
    """

    # 1. SAVE FILE
    save_path = f"{UPLOAD_DIR}/{uploaded_file.filename}"
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(uploaded_file.file, buffer)

    # 2. CREATE PATIENT FILE RECORD (patient_id empty)
    record = PatientFile(
        patient_id=None,
        file_path=save_path,
        filename=uploaded_file.filename
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    # 3. RETURN FILE ID (frontend/backend uses this to assign patient)
    return {
        "file_id": record.id,
        "filename": record.filename,
        "file_path": record.file_path
    }



# ---------------------------------------------------------
# NEW ENDPOINT:
# ASSIGN FILE → PATIENT AND SAVE PATIENT INFO
# ---------------------------------------------------------
@router.patch("/assign/{file_id}")
async def assign_file_to_patient(
    file_id: int,
    full_name: str,
    age: int | None = None,
    sex: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    id_number: str | None = None,
    db: Session = Depends(get_db)
):
    """
    Assign a raw-uploaded file to a new patient AND save patient details.
    This is the heart of the MVP flow.
    """

    # 1. GET FILE RECORD
    file_record = db.query(PatientFile).filter(PatientFile.id == file_id).first()

    if not file_record:
        return {"error": "File not found"}

    # 2. CREATE PATIENT WITH MANUAL INFO
    patient = Patient(
        full_name=full_name,
        preferred_name=None,
        id_number=id_number,
        email=email,
        phone=phone,
        age=age,
        sex=sex
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    # 3. ATTACH FILE TO PATIENT
    file_record.patient_id = patient.id
    db.commit()
    db.refresh(file_record)

    # 4. RETURN CLEAN RESPONSE
    return {
        "patient": {
            "id": patient.id,
            "full_name": patient.full_name,
            "age": patient.age,
            "sex": patient.sex,
            "email": patient.email,
            "phone": patient.phone,
            "id_number": patient.id_number
        },
        "file": {
            "id": file_record.id,
            "filename": file_record.filename,
            "file_path": file_record.file_path
        }
    }
