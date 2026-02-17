from sqlalchemy import Column, Integer, String, Date, ForeignKey
from app.core.config import Base


class PromSchedule(Base):
    __tablename__ = "prom_schedules"

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("case_episodes.id"), nullable=False)

    prom_name = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)

    status = Column(String, default="pending")  # pending / completed
    completed_date = Column(Date, nullable=True)
