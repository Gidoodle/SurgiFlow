from sqlalchemy import Column, Integer, String, ForeignKey
from app.core.config import Base


class PromResponse(Base):
    __tablename__ = "prom_responses"

    id = Column(Integer, primary_key=True, index=True)

    # This links each answer to a row in prom_schedules
    prom_instance_id = Column(Integer, ForeignKey("prom_schedules.id"), nullable=False)

    # Question ID from the template (e.g. 1, "P1", "Sy3")
    question_id = Column(String, nullable=False)

    # Numeric answer value (e.g. 0–4 or 1–5)
    answer_value = Column(Integer, nullable=False)
