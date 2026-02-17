from __future__ import annotations

from datetime import timedelta
from sqlalchemy.orm import Session

from app.models.case_episode import CaseEpisode
from app.models.prom_schedule import PromSchedule
from app.utils.prom_loader import load_prom_template


# Simple joint -> PROM mapping for MVP.
# Expand later as you add templates.
JOINT_PROM_MAP: dict[str, str] = {
    "KNEE": "OxfordKneeScore",
    # Examples for later:
    # "HIP": "OxfordHipScore",
    # "SHOULDER": "ASES",
    # "ELBOW": "MEPS",
}


DEFAULT_PROM_NAME = "OxfordKneeScore"


# Schedule offsets in days relative to surgery date
DEFAULT_INTERVALS_DAYS = [
    -14,   # 2 weeks pre-op
    42,    # 6 weeks
    90,    # 3 months
    180,   # 6 months
    365,   # 12 months
    730,   # 24 months
]


def pick_prom_name_for_case(case: CaseEpisode) -> str:
    jt = (case.joint_type or "").strip().upper()
    return JOINT_PROM_MAP.get(jt, DEFAULT_PROM_NAME)


def schedule_proms_for_case(db: Session, case_id: int) -> dict:
    """
    Idempotent scheduling:
    - If schedules already exist for this case -> do nothing.
    - Otherwise create schedules based on surgery date and mapping.

    Returns a small summary payload so callers can log or display it.
    """
    case = db.query(CaseEpisode).filter(CaseEpisode.id == case_id).first()
    if not case:
        raise ValueError("Case not found")

    # If already scheduled, return existing count and do nothing
    existing = db.query(PromSchedule).filter(PromSchedule.case_id == case_id).count()
    if existing > 0:
        return {
            "case_id": case_id,
            "prom_name": None,
            "created": 0,
            "existing": existing,
            "message": "Schedule already exists",
        }

    prom_name = pick_prom_name_for_case(case)

    # Ensure template exists (fail fast)
    load_prom_template(prom_name)

    surgery_date = case.date_of_surgery
    created = 0

    for days in DEFAULT_INTERVALS_DAYS:
        due = surgery_date + timedelta(days=days)
        entry = PromSchedule(
            patient_id=case.patient_id,
            case_id=case.id,
            prom_name=prom_name,
            due_date=due,
            status="pending",
            completed_date=None,
        )
        db.add(entry)
        created += 1

    db.commit()

    return {
        "case_id": case_id,
        "prom_name": prom_name,
        "created": created,
        "existing": 0,
        "message": "Schedule created",
    }
