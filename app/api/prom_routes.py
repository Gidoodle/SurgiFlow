from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import date

from app.core.db import get_db
from app.models.case_episode import CaseEpisode
from app.models.prom_schedule import PromSchedule
from app.models.patient import Patient
from app.models.prom_response import PromResponse

from app.utils.prom_loader import load_prom_template
from app.schemas.prom_forms import PromFormOut
from app.schemas.prom_submit import PromSubmitIn

from app.services.prom_scheduler import schedule_proms_for_case

router = APIRouter(prefix="/proms", tags=["PROMs"])


# --------------------------------------------------------
# 1. GET PROM TEMPLATE FROM JSON
# --------------------------------------------------------
@router.get("/template/{prom_name}")
def get_prom_template(prom_name: str):
    try:
        return load_prom_template(prom_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")


# --------------------------------------------------------
# 2. GENERATE PROM SCHEDULE FOR A CASE (idempotent)
# --------------------------------------------------------
@router.post("/schedule/{case_id}")
def generate_schedule(case_id: int, db: Session = Depends(get_db)):
    try:
        result = schedule_proms_for_case(db, case_id)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="PROM template missing")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --------------------------------------------------------
# 3. LIST SCHEDULE FOR PATIENT
# --------------------------------------------------------
@router.get("/schedule/patient/{patient_id}")
def list_schedule(patient_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(PromSchedule)
        .filter(PromSchedule.patient_id == patient_id)
        .order_by(PromSchedule.due_date)
        .all()
    )
    return rows


# --------------------------------------------------------
# 4. GET PROM FORM FOR A SCHEDULED PROM
# --------------------------------------------------------
@router.get("/form/{schedule_id}", response_model=PromFormOut)
def get_prom_form(schedule_id: int, db: Session = Depends(get_db)):

    schedule = (
        db.query(PromSchedule)
        .filter(PromSchedule.id == schedule_id)
        .first()
    )

    if not schedule:
        raise HTTPException(status_code=404, detail="PROM schedule not found")

    case = (
        db.query(CaseEpisode)
        .filter(CaseEpisode.id == schedule.case_id)
        .first()
    )
    if not case:
        raise HTTPException(status_code=404, detail="Case episode not found")

    patient = (
        db.query(Patient)
        .filter(Patient.id == schedule.patient_id)
        .first()
    )
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    try:
        template = load_prom_template(schedule.prom_name)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="PROM template missing")

    return PromFormOut(
        schedule_id=schedule.id,
        prom_name=schedule.prom_name,
        due_date=schedule.due_date,
        patient_id=patient.id,
        case_id=case.id,
        patient_name=patient.full_name,
        joint_type=case.joint_type,
        questions=template.get("questions", []),
    )


# --------------------------------------------------------
# 5. SUBMIT PROM ANSWERS + COMPUTE SCORE
# --------------------------------------------------------
@router.post("/submit/{schedule_id}")
def submit_prom_answers(
    schedule_id: int,
    data: PromSubmitIn,
    db: Session = Depends(get_db),
):
    schedule = db.query(PromSchedule).filter(PromSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    if (schedule.status or "").lower() == "completed":
        raise HTTPException(status_code=400, detail="PROM already completed")

    try:
        template = load_prom_template(schedule.prom_name)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="PROM template missing")

    questions = template.get("questions", [])
    valid_ids = {str(q["id"]): q for q in questions}

    if not questions:
        raise HTTPException(status_code=400, detail="Template has no questions")

    existing = (
        db.query(PromResponse)
        .filter(PromResponse.prom_instance_id == schedule.id)
        .all()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Responses already exist for this PROM")

    total_score = 0
    answered_count = 0

    for answer in data.answers:
        qid = str(answer.id)

        if qid not in valid_ids:
            raise HTTPException(status_code=400, detail=f"Invalid question ID: {qid}")

        q_meta = valid_ids[qid]
        min_val = q_meta.get("range_min")
        max_val = q_meta.get("range_max")

        if min_val is not None and max_val is not None:
            if not (min_val <= answer.value <= max_val):
                raise HTTPException(
                    status_code=400,
                    detail=f"Answer for question {qid} out of range ({min_val}-{max_val})",
                )

        db.add(
            PromResponse(
                prom_instance_id=schedule.id,
                question_id=qid,
                answer_value=answer.value,
            )
        )

        total_score += answer.value
        answered_count += 1

    schedule.status = "completed"
    schedule.completed_date = date.today()

    db.commit()

    # Simple scoring for MVP - Oxford sum
    if schedule.prom_name == "OxfordKneeScore":
        max_possible = answered_count * (questions[0].get("range_max", 5) if questions else 5)
        score_payload = {
            "prom_name": "OxfordKneeScore",
            "type": "total",
            "value": total_score,
            "max_possible": max_possible,
        }
    else:
        score_payload = {
            "prom_name": schedule.prom_name,
            "type": "not_implemented",
            "value": None,
        }

    return {
        "message": "PROM submitted successfully",
        "schedule_id": schedule.id,
        "prom_name": schedule.prom_name,
        "status": schedule.status,
        "answered_questions": answered_count,
        "score": score_payload,
    }
