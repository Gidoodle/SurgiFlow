from datetime import date
from pydantic import BaseModel

class CaseEpisodeBase(BaseModel):
    patient_id: int
    joint_type: str
    date_of_surgery: date

    cutting_time: str | None = None
    closing_time: str | None = None

    surgeon_name: str | None = None
    procedure_type: str | None = None
    implant_notes: str | None = None


class CaseEpisodeCreate(CaseEpisodeBase):
    pass


class CaseEpisodeOut(CaseEpisodeBase):
    id: int

    class Config:
        orm_mode = True
