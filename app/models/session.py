from sqlalchemy import Column, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)

    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    end_time = Column(DateTime(timezone=True), nullable=True)

    # One-to-One with Patient
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), unique=True, nullable=True)
    patient = relationship(
        "Patient",
        back_populates="session",
        uselist=False
    )

    # One-to-Many with Attempt
    attempts = relationship(
        "Attempt",
        back_populates="session",
        cascade="all, delete-orphan"
    )
    
    stored_thresholds = relationship(
        "StoredThreshold",
        back_populates="session",
        cascade="all, delete-orphan"
    )