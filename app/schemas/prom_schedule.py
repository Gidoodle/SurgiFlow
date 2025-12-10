from pydantic import BaseModel
from datetime import date

class PromScheduleBase(BaseModel):
    patient_id: int
    case_id: int
    prom_name: str
    due_date: date
    status: str = "pending"

class PromScheduleOut(PromScheduleBase):
    id: int

    class Config:
        orm_mode = True
