from pydantic import BaseModel

class PatientFileBase(BaseModel):
    patient_id: int
    file_path: str
    filename: str

class PatientFileCreate(PatientFileBase):
    pass

class PatientFileOut(PatientFileBase):
    id: int

    class Config:
        orm_mode = True
