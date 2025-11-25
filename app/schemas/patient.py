from pydantic import BaseModel

class PatientBase(BaseModel):
    full_name: str
    preferred_name: str | None = None
    id_number: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    medical_aid: str | None = None
    medical_aid_number: str | None = None

class PatientCreate(PatientBase):
    pass

class PatientOut(PatientBase):
    id: int

    class Config:
        orm_mode = True
