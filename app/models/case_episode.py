from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.core.config import Base

class CaseEpisode(Base):
    __tablename__ = "case_episodes"

    id = Column(Integer, primary_key=True, index=True)

    # Link to patient
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    # Copy of joint_type at time of case (shoulder / knee / hip etc)
    joint_type = Column(String, nullable=False)

    # Surgery date
    date_of_surgery = Column(Date, nullable=False)

    # These can be refined later (duration vs time-of-day etc)
    cutting_time = Column(String, nullable=True)   # e.g. "10:15"
    closing_time = Column(String, nullable=True)   # e.g. "11:05"

    # Optional metadata
    surgeon_name = Column(String, nullable=True)
    procedure_type = Column(String, nullable=True)  # e.g. "TKA", "RSA"
    implant_notes = Column(String, nullable=True)   # free text, can structure later
