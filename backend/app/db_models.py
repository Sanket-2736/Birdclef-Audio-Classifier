
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


print("[DEBUG] Initializing SQLAlchemy ORM models...")
print(f"[DEBUG] SQLAlchemy Base: {Base}")


class User(Base):
    """User account model."""

    __tablename__ = "users"

    print("[DEBUG] Defining User model...")

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

    print("[DEBUG] User model columns and relationships configured.")

    def __repr__(self):
        return f"<User {self.email}>"


class Recording(Base):
    """Audio recording metadata."""

    __tablename__ = "recordings"

    print("[DEBUG] Defining Recording model...")

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

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

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

    print("[DEBUG] Recording model columns configured.")
    print("[DEBUG] Recording relationships configured.")
    print("[DEBUG] Recording indexes configured.")

    def __repr__(self):
        return f"<Recording {self.id} {self.original_filename}>"


class Prediction(Base):
    """Model predictions for a recording."""

    __tablename__ = "predictions"

    print("[DEBUG] Defining Prediction model...")

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    recording_id = Column(
        String(36),
        ForeignKey("recordings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    result_json = Column(JSON, nullable=False)

    top_species = Column(
        JSON,
        nullable=False,
    )  # Cached top 10 for quick access

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    recording = relationship("Recording", back_populates="prediction")

    print("[DEBUG] Prediction model columns configured.")
    print("[DEBUG] Prediction relationship configured.")

    def __repr__(self):
        return f"<Prediction {self.id}>"


class Detection(Base):
    """Per-species detection within a recording."""

    __tablename__ = "detections"

    print("[DEBUG] Defining Detection model...")

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
        Index(
            "ix_detections_recording_species",
            "recording_id",
            "species_code",
        ),
    )

    print("[DEBUG] Detection model columns configured.")
    print("[DEBUG] Detection relationship configured.")
    print("[DEBUG] Detection indexes configured.")

    def __repr__(self):
        return f"<Detection {self.species_code}>"


class Feedback(Base):
    """User feedback on predictions."""

    __tablename__ = "feedback"

    print("[DEBUG] Defining Feedback model...")

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
        Index(
            "ix_feedback_recording_user",
            "recording_id",
            "user_id",
        ),
    )

    print("[DEBUG] Feedback model columns configured.")
    print("[DEBUG] Feedback relationships configured.")
    print("[DEBUG] Feedback indexes configured.")

    def __repr__(self):
        return f"<Feedback {self.id}>"


print("\n" + "=" * 60)
print("[SUCCESS] ALL SQLALCHEMY MODELS INITIALIZED")
print("=" * 60)

print("[DEBUG] Registered ORM tables:")

for table_name, table in Base.metadata.tables.items():
    print(f"\n[DEBUG] Table: {table_name}")
    print(f"[DEBUG] Columns: {list(table.columns.keys())}")

    print(
        f"[DEBUG] Foreign keys: "
        f"{[fk.target_fullname for column in table.columns for fk in column.foreign_keys]}"
    )

print("\n[SUCCESS] SQLAlchemy model registration completed.")
