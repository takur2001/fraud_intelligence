from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.gemini_service import (
    GeminiAnalysisError,
    analyze_complaint,
)


router = APIRouter(
    prefix="/complaints",
    tags=["Customer Complaints"],
)


DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=schemas.ComplaintWithAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit and analyze a customer complaint",
)
def submit_complaint(
    complaint_data: schemas.ComplaintCreate,
    db: DatabaseSession,
) -> schemas.ComplaintWithAnalysisResponse:
    """
    Save the customer complaint and analyze it using Gemini.
    """

    new_complaint = models.Complaint(
        customer_name=complaint_data.customer_name.strip(),
        customer_email=str(complaint_data.customer_email).lower(),
        subject=complaint_data.subject.strip(),
        description=complaint_data.description.strip(),
        account_reference=(
            complaint_data.account_reference.strip()
            if complaint_data.account_reference
            else None
        ),
        status=models.ComplaintStatus.SUBMITTED,
    )

    try:
        db.add(new_complaint)
        db.commit()
        db.refresh(new_complaint)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The complaint could not be saved.",
        ) from exc

    saved_analysis: models.ComplaintAnalysis | None = None

    try:
        ai_result = analyze_complaint(
            subject=new_complaint.subject,
            description=new_complaint.description,
            account_reference=new_complaint.account_reference,
        )

        saved_analysis = models.ComplaintAnalysis(
            complaint_id=new_complaint.id,
            analysis_status="completed",
            summary=ai_result.summary,
            category=ai_result.category,
            subcategory=ai_result.subcategory,
            priority=ai_result.priority,
            sentiment=ai_result.sentiment,
            fraud_suspected=ai_result.fraud_suspected,
            fraud_risk_level=ai_result.fraud_risk_level,
            transaction_amount=ai_result.transaction_amount,
            currency=ai_result.currency,
            transaction_date=ai_result.transaction_date,
            merchant_name=ai_result.merchant_name,
            payment_channel=ai_result.payment_channel,
            recommended_department=ai_result.recommended_department,
            red_flags=ai_result.red_flags,
            recommended_actions=ai_result.recommended_actions,
            customer_requested_resolution=(
                ai_result.customer_requested_resolution
            ),
            confidence_score=ai_result.confidence_score,
            model_name="gemini-3.6-flash",
        )

        db.add(saved_analysis)
        db.commit()
        db.refresh(saved_analysis)

    except GeminiAnalysisError as exc:
        db.rollback()

        saved_analysis = models.ComplaintAnalysis(
            complaint_id=new_complaint.id,
            analysis_status="failed",
            model_name="gemini-3.6-flash",
            error_message=str(exc)[:1000],
        )

        try:
            db.add(saved_analysis)
            db.commit()
            db.refresh(saved_analysis)

        except SQLAlchemyError:
            db.rollback()
            saved_analysis = None

    return schemas.ComplaintWithAnalysisResponse(
        message=(
            "Complaint submitted successfully. "
            f"AI analysis status: "
            f"{saved_analysis.analysis_status if saved_analysis else 'unavailable'}."
        ),
        complaint=new_complaint,
        analysis=saved_analysis,
    )


@router.get(
    "/manager-view",
    response_model=list[schemas.ManagerComplaintView],
    summary="Display complaints with AI analysis",
)
def get_manager_complaint_view(
    db: DatabaseSession,
) -> list[schemas.ManagerComplaintView]:
    statement = (
        select(
            models.Complaint,
            models.ComplaintAnalysis,
        )
        .outerjoin(
            models.ComplaintAnalysis,
            models.Complaint.id
            == models.ComplaintAnalysis.complaint_id,
        )
        .order_by(models.Complaint.created_at.desc())
    )

    rows = db.execute(statement).all()

    results: list[schemas.ManagerComplaintView] = []

    for complaint, analysis in rows:
        results.append(
            schemas.ManagerComplaintView(
                complaint_id=complaint.id,
                customer_name=complaint.customer_name,
                customer_email=complaint.customer_email,
                subject=complaint.subject,
                original_description=complaint.description,
                complaint_status=complaint.status,
                created_at=complaint.created_at,
                analysis_status=(
                    analysis.analysis_status if analysis else None
                ),
                summary=analysis.summary if analysis else None,
                category=analysis.category if analysis else None,
                subcategory=analysis.subcategory if analysis else None,
                priority=analysis.priority if analysis else None,
                sentiment=analysis.sentiment if analysis else None,
                fraud_suspected=(
                    analysis.fraud_suspected if analysis else None
                ),
                fraud_risk_level=(
                    analysis.fraud_risk_level if analysis else None
                ),
                transaction_amount=(
                    analysis.transaction_amount if analysis else None
                ),
                currency=analysis.currency if analysis else None,
                transaction_date=(
                    analysis.transaction_date if analysis else None
                ),
                merchant_name=(
                    analysis.merchant_name if analysis else None
                ),
                payment_channel=(
                    analysis.payment_channel if analysis else None
                ),
                recommended_department=(
                    analysis.recommended_department if analysis else None
                ),
                red_flags=analysis.red_flags if analysis else None,
                recommended_actions=(
                    analysis.recommended_actions if analysis else None
                ),
                customer_requested_resolution=(
                    analysis.customer_requested_resolution
                    if analysis
                    else None
                ),
                confidence_score=(
                    analysis.confidence_score if analysis else None
                ),
            )
        )

    return results