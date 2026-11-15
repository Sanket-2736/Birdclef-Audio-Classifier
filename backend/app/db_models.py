"""
SQLAlchemy ORM models for BirdCLEF application.
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, 
    ForeignKey, JSON, Index, LargeBinary
)
from sqlalchemy.orm import relationship
from .db import Base


class User(Base):
    """User account model."""
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    recordings = relationship(
        "Recording",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    feedback = relationship(
        "Feedback",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<User {self.email}>"


class Recording(Base):
    """Audio recording metadata."""
    __tablename__ = "recordings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(50), nullable=False)
    sha256 = Column(String(64), nullable=False, unique=True, index=True)
    duration_sec = Column(Float, nullable=False)
    sample_rate = Column(Integer, nullable=False)
    site_id = Column(Integer, default=0, nullable=False)
    hour = Column(Integer, default=12, nullable=False)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    status = Column(
        String(20),
        default="queued",
        nullable=False,
        index=True,
    )  # queued, processing, done, failed
    progress_stage = Column(String(100), default="", nullable=False)
    error_message = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="recordings")
    prediction = relationship(
        "Prediction",
        back_populates="recording",
        uselist=False,
        cascade="all, delete-orphan",
    )
    detections = relationship(
        "Detection",
        back_populates="recording",
        cascade="all, delete-orphan",
    )
    feedback = relationship(
        "Feedback",
        back_populates="recording",
        cascade="all, delete-orphan",
    )
    
    # Indices for common queries
    __table_args__ = (
        Index("ix_recordings_user_created", "user_id", "created_at"),
        Index("ix_recordings_status_created", "status", "created_at"),
    )
    
    def __repr__(self):
        return f"<Recording {self.id} {self.original_filename}>"


class Prediction(Base):
    """Model predictions for a recording."""
    __tablename__ = "predictions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recording_id = Column(
        String(36),
        ForeignKey("recordings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    result_json = Column(JSON, nullable=False)
    top_species = Column(JSON, nullable=False)  # Cached top 10 for quick access
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    recording = relationship("Recording", back_populates="prediction")
    
    def __repr__(self):
        return f"<Prediction {self.id}>"


class Detection(Base):
    """Per-species detection within a recording."""
    __tablename__ = "detections"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recording_id = Column(
        String(36),
        ForeignKey("recordings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    species_code = Column(String(50), nullable=False, index=True)
    species_name = Column(String(255), nullable=False)
    taxon = Column(String(50), nullable=False)
    max_score = Column(Float, nullable=False)
    windows_detected = Column(Integer, nullable=False)
    
    # Relationships
    recording = relationship("Recording", back_populates="detections")
    
    __table_args__ = (
        Index("ix_detections_recording_species", "recording_id", "species_code"),
    )
    
    def __repr__(self):
        return f"<Detection {self.species_code}>"


class Feedback(Base):
    """User feedback on predictions."""
    __tablename__ = "feedback"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    recording_id = Column(
        String(36),
        ForeignKey("recordings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    species_code = Column(String(50), nullable=False)
    window_index = Column(Integer, nullable=True)
    is_correct = Column(Boolean, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    recording = relationship("Recording", back_populates="feedback")
    user = relationship("User", back_populates="feedback")
    
    __table_args__ = (
        Index("ix_feedback_recording_user", "recording_id", "user_id"),
    )
    
    def __repr__(self):
        return f"<Feedback {self.id}>"
