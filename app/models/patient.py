from sqlalchemy import Column, Integer, String
from app.core.config import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)
    preferred_name = Column(String, nullable=True)

    id_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)

    age = Column(Integer, nullable=True)
    sex = Column(String, nullable=True)

    medical_aid = Column(String, nullable=True)
    medical_aid_number = Column(String, nullable=True)

    # NEW — needed for PROM routing
    joint_type = Column(String, nullable=True)  # "shoulder" | "knee" | "hip"
