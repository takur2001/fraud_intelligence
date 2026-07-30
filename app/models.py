from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ComplaintStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        autoincrement=True,
    )

    customer_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    customer_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    subject: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    account_reference: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    status: Mapped[ComplaintStatus] = mapped_column(
        SQLEnum(ComplaintStatus),
        default=ComplaintStatus.SUBMITTED,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ComplaintAnalysis(Base):
    """
    Stores Gemini's structured analysis for a complaint.
    """

    __tablename__ = "complaint_analyses"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id"),
        unique=True,
        index=True,
        nullable=False,
    )

    analysis_status: Mapped[str] = mapped_column(
        String(30),
        default="completed",
        nullable=False,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    subcategory: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    priority: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    sentiment: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    fraud_suspected: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        index=True,
    )

    fraud_risk_level: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    transaction_amount: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    transaction_date: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    merchant_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    payment_channel: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    recommended_department: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    red_flags: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    recommended_actions: Mapped[list[str] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    customer_requested_resolution: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )