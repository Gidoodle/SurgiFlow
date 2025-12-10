from pydantic import BaseModel
from datetime import date
from typing import List, Dict, Any


class PromFormOut(BaseModel):
    schedule_id: int
    prom_name: str
    due_date: date

    patient_id: int
    case_id: int

    # Optional extras for display
    patient_name: str | None = None
    joint_type: str | None = None

    # Questions come straight from the JSON template
    questions: List[Dict[str, Any]]

    class Config:
        orm_mode = True
