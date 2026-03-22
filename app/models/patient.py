from sqlalchemy import Column, Float, Integer, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.enums import EarSideEnum, HearingTypeEnum, TestTypeEnum, PatientSourceEnum

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    source_type = Column(SQLEnum(PatientSourceEnum), nullable=False, default=PatientSourceEnum.REAL)
   
    ears = relationship(
        "Ear",
        back_populates="patient",
        cascade="all, delete-orphan"
    )
    session = relationship(
        "Session",
        back_populates="patient",
        uselist=False
    )
 
class Ear(Base):
    __tablename__ = "ears"
    __table_args__ = (
        UniqueConstraint("patient_id", "side", name="uq_ears_patient_side"),
    )

    id = Column(Integer, primary_key=True, index=True)

    patient_id = Column(
        Integer,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )

    side = Column(SQLEnum(EarSideEnum), nullable=False)  # left / right
    hearing_type = Column(SQLEnum(HearingTypeEnum), nullable=True)  # Normal, Conductive, Sensorineural, Mixed    

    patient = relationship("Patient", back_populates="ears")

    audiogram_points = relationship(
        "AudiogramPoint",
        back_populates="ear",
        cascade="all, delete-orphan"
    )
    
class AudiogramPoint(Base):
    __tablename__ = "audiogram_points"
    __table_args__ = (
        UniqueConstraint("ear_id", "test_type", "frequency", name="uq_points_ear_test_freq"),
    )

    id = Column(Integer, primary_key=True, index=True)

    ear_id = Column(
        Integer,
        ForeignKey("ears.id", ondelete="CASCADE"),
        nullable=False
    )

    test_type = Column(SQLEnum(TestTypeEnum), nullable=False)  # AC / AC_masked / BC / BC_masked
    frequency = Column(Integer, nullable=False)
    threshold_db = Column(Float, nullable=False)

    ear = relationship("Ear", back_populates="audiogram_points")
