from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.case_episode import CaseEpisode
from app.models.patient import Patient
from app.schemas.case_episode import CaseEpisodeCreate, CaseEpisodeOut

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.post("/", response_model=CaseEpisodeOut)
def create_case_episode(
    case_in: CaseEpisodeCreate,
    db: Session = Depends(get_db),
):
    # 1. ensure patient exists
    patient = db.query(Patient).filter(Patient.id == case_in.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # 2. create case episode
    case = CaseEpisode(
        patient_id=case_in.patient_id,
        joint_type=case_in.joint_type,
        date_of_surgery=case_in.date_of_surgery,
        cutting_time=case_in.cutting_time,
        closing_time=case_in.closing_time,
        surgeon_name=case_in.surgeon_name,
        procedure_type=case_in.procedure_type,
        implant_notes=case_in.implant_notes,
    )

    db.add(case)
    db.commit()
    db.refresh(case)

    return case


@router.get("/{case_id}", response_model=CaseEpisodeOut)
def get_case_episode(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = db.query(CaseEpisode).filter(CaseEpisode.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case episode not found")
    return case


@router.get("/by-patient/{patient_id}", response_model=list[CaseEpisodeOut])
def list_cases_for_patient(
    patient_id: int,
    db: Session = Depends(get_db),
):
    # optional: verify patient exists
    cases = (
        db.query(CaseEpisode)
        .filter(CaseEpisode.patient_id == patient_id)
        .order_by(CaseEpisode.date_of_surgery.desc())
        .all()
    )
    return cases
