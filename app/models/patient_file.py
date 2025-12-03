from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.config import Base

class PatientFile(Base):
    __tablename__ = "patient_files"

    id = Column(Integer, primary_key=True, index=True)

    # Allow NULL for raw uploads (patient linked later)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)

    file_path = Column(String, nullable=False)
    filename = Column(String, nullable=False)
