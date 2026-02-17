from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.case_episode import CaseEpisode
from app.models.patient import Patient
from app.schemas.case_episode import CaseEpisodeCreate, CaseEpisodeOut, CaseEpisodeUpdate

router = APIRouter(prefix="/cases", tags=["Cases"])


def now_hhmm() -> str:
    # Server/device time (no typing on frontend)
    return datetime.now().strftime("%H:%M")


def compute_duration_minutes(cutting_time: str | None, closing_time: str | None) -> int | None:
    if not cutting_time or not closing_time:
        return None
    start = datetime.strptime(cutting_time, "%H:%M")
    end = datetime.strptime(closing_time, "%H:%M")
    diff = int((end - start).total_seconds() / 60)
    if diff < 0:
        return None
    return diff


def recompute_and_set_duration(case: CaseEpisode) -> None:
    case.duration_minutes = compute_duration_minutes(case.cutting_time, case.closing_time)


def to_out(case: CaseEpisode) -> CaseEpisodeOut:
    # Prefer stored duration_minutes, but keep a safe fallback for older rows
    out = CaseEpisodeOut.model_validate(case)
    if out.duration_minutes is None:
        out.duration_minutes = compute_duration_minutes(case.cutting_time, case.closing_time)
    return out


def try_trigger_prom_schedule(db: Session, case_id: int) -> None:
    """
    MVP-safe stub.
    Later, when PROMs wiring is ready, replace this with a real call.

    For now: do nothing, but keep the hook here so we don't forget.
    """
    return


@router.post("/", response_model=CaseEpisodeOut)
def create_case_episode(
    case_in: CaseEpisodeCreate,
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(Patient.id == case_in.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    case = CaseEpisode(
        patient_id=case_in.patient_id,
        joint_type=case_in.joint_type,
        date_of_surgery=case_in.date_of_surgery,
        cutting_time=case_in.cutting_time,
        closing_time=case_in.closing_time,
        surgeon_name=case_in.surgeon_name,
        procedure_type=case_in.procedure_type,
        implant_notes=case_in.implant_notes,
        case_status=case_in.case_status,
    )

    recompute_and_set_duration(case)

    # If both times were provided but invalid (closing before cutting), reject
    if case_in.cutting_time and case_in.closing_time and case.duration_minutes is None:
        raise HTTPException(status_code=422, detail="closing_time must be after cutting_time")

    db.add(case)
    db.commit()
    db.refresh(case)

    # If created already completed (rare), trigger hook
    if case.case_status == "COMPLETED":
        try_trigger_prom_schedule(db, case.id)

    return to_out(case)


@router.patch("/{case_id}", response_model=CaseEpisodeOut)
def update_case_episode(
    case_id: int,
    patch: CaseEpisodeUpdate,
    db: Session = Depends(get_db),
):
    case = db.query(CaseEpisode).filter(CaseEpisode.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case episode not found")

    prev_status = case.case_status

    data = patch.model_dump(exclude_unset=True)

    for k, v in data.items():
        setattr(case, k, v)

    # Always recompute duration if either time changed
    if "cutting_time" in data or "closing_time" in data:
        recompute_and_set_duration(case)
        if case.cutting_time and case.closing_time and case.duration_minutes is None:
            raise HTTPException(status_code=422, detail="closing_time must be after cutting_time")

    db.commit()
    db.refresh(case)

    # Trigger when status transitions to COMPLETED
    if prev_status != "COMPLETED" and case.case_status == "COMPLETED":
        try_trigger_prom_schedule(db, case.id)

    return to_out(case)


@router.post("/{case_id}/start", response_model=CaseEpisodeOut)
def start_case_episode(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = db.query(CaseEpisode).filter(CaseEpisode.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case episode not found")

    # Only allow start from PLANNED (and optionally IN_PROGRESS idempotent)
    if case.case_status == "COMPLETED":
        raise HTTPException(status_code=409, detail="Case already completed")
    if case.case_status == "CANCELLED":
        raise HTTPException(status_code=409, detail="Case is cancelled")

    if case.case_status != "IN_PROGRESS":
        case.case_status = "IN_PROGRESS"

    # Auto-capture cutting time if not already set
    if not case.cutting_time:
        case.cutting_time = now_hhmm()

    # Starting a case typically clears any accidental stop time
    if case.closing_time:
        case.closing_time = None

    recompute_and_set_duration(case)

    db.commit()
    db.refresh(case)

    return to_out(case)


@router.post("/{case_id}/stop", response_model=CaseEpisodeOut)
def stop_case_episode(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = db.query(CaseEpisode).filter(CaseEpisode.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case episode not found")

    if case.case_status == "CANCELLED":
        raise HTTPException(status_code=409, detail="Case is cancelled")

    prev_status = case.case_status

    # Ensure we have a start time - if user stops without starting, we still capture both
    if not case.cutting_time:
        case.cutting_time = now_hhmm()

    # Auto-capture closing time
    case.closing_time = now_hhmm()

    # Mark completed
    case.case_status = "COMPLETED"

    recompute_and_set_duration(case)
    if case.duration_minutes is None:
        raise HTTPException(status_code=422, detail="closing_time must be after cutting_time")

    db.commit()
    db.refresh(case)

    if prev_status != "COMPLETED":
        try_trigger_prom_schedule(db, case.id)

    return to_out(case)


@router.get("/{case_id}", response_model=CaseEpisodeOut)
def get_case_episode(
    case_id: int,
    db: Session = Depends(get_db),
):
    case = db.query(CaseEpisode).filter(CaseEpisode.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case episode not found")
    return to_out(case)


@router.get("/by-patient/{patient_id}", response_model=list[CaseEpisodeOut])
def list_cases_for_patient(
    patient_id: int,
    db: Session = Depends(get_db),
):
    cases = (
        db.query(CaseEpisode)
        .filter(CaseEpisode.patient_id == patient_id)
        .order_by(CaseEpisode.date_of_surgery.desc())
        .all()
    )
    return [to_out(c) for c in cases]
