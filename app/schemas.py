from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import ComplaintStatus
from typing import Literal


class ComplaintCreate(BaseModel):
    """
    Data accepted from the customer.
    """

    customer_name: str = Field(
        min_length=2,
        max_length=100,
        examples=["John Smith"],
    )

    customer_email: EmailStr = Field(
        examples=["john.smith@example.com"],
    )

    subject: str = Field(
        min_length=5,
        max_length=200,
        examples=["Duplicate debit card transaction"],
    )

    description: str = Field(
        min_length=20,
        max_length=5000,
        examples=[
            "I noticed that a transaction of $125 was charged twice "
            "to my checking account."
        ],
    )

    account_reference: str | None = Field(
        default=None,
        min_length=4,
        max_length=20,
        examples=["XXXX1234"],
        description="Only provide a masked account reference.",
    )


class ComplaintResponse(BaseModel):
    """
    Complaint data returned by the API.
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    customer_email: EmailStr
    subject: str
    description: str
    account_reference: str | None
    status: ComplaintStatus
    created_at: datetime
    updated_at: datetime


class ComplaintSubmissionResponse(BaseModel):
    message: str
    complaint: ComplaintResponse

class GeminiComplaintAnalysis(BaseModel):
    """
    Structured information Gemini must extract
    from the customer's complaint.
    """

    summary: str = Field(
        min_length=5,
        max_length=1000,
        description="A concise factual summary of the complaint.",
    )

    category: Literal[
        "card_transaction",
        "bank_transfer",
        "cash_withdrawal",
        "deposit",
        "account_access",
        "fees_and_charges",
        "loan_or_credit",
        "identity_theft",
        "customer_service",
        "other",
    ] = Field(
        description="Main category of the complaint.",
    )

    subcategory: str = Field(
        max_length=200,
        description="A more specific classification of the issue.",
    )

    priority: Literal[
        "low",
        "medium",
        "high",
        "critical",
    ] = Field(
        description="Operational priority based on urgency and possible loss.",
    )

    sentiment: Literal[
        "calm",
        "concerned",
        "frustrated",
        "angry",
        "distressed",
    ] = Field(
        description="Customer's apparent sentiment.",
    )

    fraud_suspected: bool = Field(
        description="True only when the complaint contains possible fraud indicators.",
    )

    fraud_risk_level: Literal[
        "none",
        "low",
        "medium",
        "high",
    ] = Field(
        description="Possible fraud risk level based only on the complaint.",
    )

    transaction_amount: float | None = Field(
        default=None,
        ge=0,
        description="Transaction amount mentioned by the customer, without currency symbols.",
    )

    currency: str | None = Field(
        default=None,
        max_length=10,
        description="Currency code or currency name if explicitly mentioned.",
    )

    transaction_date: str | None = Field(
        default=None,
        max_length=50,
        description="Transaction date exactly as stated or normalized when clearly known.",
    )

    merchant_name: str | None = Field(
        default=None,
        max_length=200,
        description="Merchant, company, ATM, or recipient mentioned.",
    )

    payment_channel: Literal[
        "debit_card",
        "credit_card",
        "atm",
        "ach",
        "wire_transfer",
        "check",
        "cash",
        "online_banking",
        "mobile_banking",
        "unknown",
    ] = Field(
        description="Payment or account-access channel involved.",
    )

    recommended_department: Literal[
        "fraud_team",
        "card_disputes",
        "bank_transfer_disputes",
        "account_security",
        "fees_department",
        "loan_department",
        "customer_service",
        "branch_operations",
        "other",
    ] = Field(
        description="Department that should review the complaint.",
    )

    red_flags: list[str] = Field(
        description="Potential fraud, safety, or operational warning signs.",
    )

    recommended_actions: list[str] = Field(
        description="Recommended manager actions.",
    )

    customer_requested_resolution: str | None = Field(
        default=None,
        max_length=500,
        description="What the customer is asking the bank to do.",
    )

    confidence_score: float = Field(
        ge=0,
        le=1,
        description="Confidence in the extraction, between 0 and 1.",
    )


class ComplaintAnalysisResponse(GeminiComplaintAnalysis):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_id: int
    analysis_status: str
    model_name: str | None
    error_message: str | None
    analyzed_at: datetime


class ComplaintWithAnalysisResponse(BaseModel):
    message: str
    complaint: ComplaintResponse
    analysis: ComplaintAnalysisResponse | None

class ManagerComplaintView(BaseModel):
    complaint_id: int
    customer_name: str
    customer_email: EmailStr
    subject: str
    original_description: str
    complaint_status: ComplaintStatus
    created_at: datetime

    analysis_status: str | None = None
    summary: str | None = None
    category: str | None = None
    subcategory: str | None = None
    priority: str | None = None
    sentiment: str | None = None
    fraud_suspected: bool | None = None
    fraud_risk_level: str | None = None
    transaction_amount: float | None = None
    currency: str | None = None
    transaction_date: str | None = None
    merchant_name: str | None = None
    payment_channel: str | None = None
    recommended_department: str | None = None
    red_flags: list[str] | None = None
    recommended_actions: list[str] | None = None
    customer_requested_resolution: str | None = None
    confidence_score: float | None = None