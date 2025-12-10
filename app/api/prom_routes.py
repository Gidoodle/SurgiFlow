from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import timedelta, date

from app.core.db import get_db
from app.models.case_episode import CaseEpisode
from app.models.prom_schedule import PromSchedule
from app.models.patient import Patient
from app.models.prom_response import PromResponse

from app.utils.prom_loader import load_prom_template
from app.schemas.prom_forms import PromFormOut
from app.schemas.prom_submit import PromSubmitIn

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
# 2. GENERATE PROM SCHEDULE FOR A CASE
# --------------------------------------------------------
@router.post("/schedule/{case_id}")
def generate_schedule(case_id: int, db: Session = Depends(get_db)):

    case = db.query(CaseEpisode).filter(CaseEpisode.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    prom_name = "OxfordKneeScore"

    try:
        load_prom_template(prom_name)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="PROM template missing")

    surgery_date = case.date_of_surgery

    intervals = [
        -14,
        42,
        90,
        180,
        365,
        730,
    ]

    schedules = []

    for days in intervals:
        due = surgery_date + timedelta(days=days)
        entry = PromSchedule(
            patient_id=case.patient_id,
            case_id=case.id,
            prom_name=prom_name,
            due_date=due,
            status="pending",
        )
        db.add(entry)
        schedules.append(entry)

    db.commit()

    return {"message": "Schedule created", "count": len(schedules)}


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
# 5. SUBMIT PROM ANSWERS
# --------------------------------------------------------
@router.post("/submit/{schedule_id}")
def submit_prom_answers(
    schedule_id: int,
    data: PromSubmitIn,
    db: Session = Depends(get_db)
):
    schedule = db.query(PromSchedule).filter(PromSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")

    try:
        template = load_prom_template(schedule.prom_name)
    except FileNotFoundError:
        raise HTTPException(status_code=400, detail="PROM template missing")

    valid_ids = {str(q["id"]) for q in template.get("questions", [])}

    for answer in data.answers:
        qid = str(answer.id)

        if qid not in valid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid question ID: {qid}",
            )

        db.add(
            PromResponse(
                prom_instance_id=schedule.id,
                question_id=qid,
                answer_value=answer.value,
            )
        )

    schedule.status = "completed"
    schedule.completed_date = date.today()

    db.commit()

    return {"message": "PROM submitted successfully", "schedule_id": schedule.id}
