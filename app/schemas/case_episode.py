from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

ALLOWED_STATUSES = {"PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"}


def _validate_hhmm(v: Optional[str]) -> Optional[str]:
    if v is None or v == "":
        return None
    datetime.strptime(v, "%H:%M")  # raises if invalid
    return v


class CaseEpisodeBase(BaseModel):
    patient_id: int
    joint_type: str
    date_of_surgery: date

    cutting_time: Optional[str] = None
    closing_time: Optional[str] = None

    surgeon_name: Optional[str] = None
    procedure_type: Optional[str] = None
    implant_notes: Optional[str] = None

    case_status: str = "PLANNED"

    @field_validator("cutting_time", "closing_time")
    @classmethod
    def validate_time_format(cls, v):
        return _validate_hhmm(v)

    @field_validator("case_status")
    @classmethod
    def validate_status(cls, v):
        if v is None or v == "":
            return "PLANNED"
        v = v.strip().upper()
        if v not in ALLOWED_STATUSES:
            raise ValueError(f"case_status must be one of {sorted(ALLOWED_STATUSES)}")
        return v


class CaseEpisodeCreate(CaseEpisodeBase):
    pass


class CaseEpisodeUpdate(BaseModel):
    date_of_surgery: Optional[date] = None
    cutting_time: Optional[str] = None
    closing_time: Optional[str] = None
    surgeon_name: Optional[str] = None
    procedure_type: Optional[str] = None
    implant_notes: Optional[str] = None
    case_status: Optional[str] = None

    @field_validator("cutting_time", "closing_time")
    @classmethod
    def validate_time_format(cls, v):
        return _validate_hhmm(v)

    @field_validator("case_status")
    @classmethod
    def validate_status(cls, v):
        if v is None or v == "":
            return None
        v = v.strip().upper()
        if v not in ALLOWED_STATUSES:
            raise ValueError(f"case_status must be one of {sorted(ALLOWED_STATUSES)}")
        return v


class CaseEpisodeOut(CaseEpisodeBase):
    id: int
    duration_minutes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
