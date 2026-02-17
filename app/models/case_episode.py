from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.core.config import Base


class CaseEpisode(Base):
    __tablename__ = "case_episodes"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)

    joint_type = Column(String, nullable=False)
    date_of_surgery = Column(Date, nullable=False)

    # Keep as HH:MM strings for MVP
    cutting_time = Column(String, nullable=True)   # "10:15"
    closing_time = Column(String, nullable=True)   # "11:05"

    # Stored duration (minutes) - auto-calculated when times are set
    duration_minutes = Column(Integer, nullable=True)

    # Consistent name across DB + schemas + routes
    case_status = Column(String, nullable=False, default="PLANNED")  # PLANNED / IN_PROGRESS / COMPLETED / CANCELLED

    surgeon_name = Column(String, nullable=True)
    procedure_type = Column(String, nullable=True)
    implant_notes = Column(String, nullable=True)
