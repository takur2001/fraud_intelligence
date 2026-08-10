from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.dependencies import ManagerUser
from app.email_schemas import EmailSendResponse
from app.services.email_service import (
    EmailGenerationError,
    generate_customer_email,
)
from app.services.gemini_service import (
    GeminiAnalysisError,
    analyze_complaint,
)
from app.services.smtp_service import (
    EmailSendingError,
    send_customer_email,
)


router = APIRouter(
    prefix="/complaints",
    tags=["Customer Complaints"],
)


DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


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
        customer_email=str(
            complaint_data.customer_email
        ).lower(),
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
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="The complaint could not be saved.",
        ) from exc

    saved_analysis: (
        models.ComplaintAnalysis | None
    ) = None

    try:
        ai_result = analyze_complaint(
            subject=new_complaint.subject,
            description=new_complaint.description,
            account_reference=(
                new_complaint.account_reference
            ),
        )

        saved_analysis = models.ComplaintAnalysis(
            complaint_id=new_complaint.id,
            analysis_status="completed",
            summary=ai_result.summary,
            category=ai_result.category,
            subcategory=ai_result.subcategory,
            priority=ai_result.priority,
            sentiment=ai_result.sentiment,
            fraud_suspected=(
                ai_result.fraud_suspected
            ),
            fraud_risk_level=(
                ai_result.fraud_risk_level
            ),
            transaction_amount=(
                ai_result.transaction_amount
            ),
            currency=ai_result.currency,
            transaction_date=(
                ai_result.transaction_date
            ),
            merchant_name=ai_result.merchant_name,
            payment_channel=(
                ai_result.payment_channel
            ),
            recommended_department=(
                ai_result.recommended_department
            ),
            red_flags=ai_result.red_flags,
            recommended_actions=(
                ai_result.recommended_actions
            ),
            customer_requested_resolution=(
                ai_result.customer_requested_resolution
            ),
            confidence_score=(
                ai_result.confidence_score
            ),
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

    analysis_status = (
        saved_analysis.analysis_status
        if saved_analysis
        else "unavailable"
    )

    return schemas.ComplaintWithAnalysisResponse(
        message=(
            "Complaint submitted successfully. "
            f"AI analysis status: {analysis_status}."
        ),
        complaint=new_complaint,
        analysis=saved_analysis,
    )


@router.get(
    "/manager-view",
    response_model=list[
        schemas.ManagerComplaintView
    ],
    summary="Display complaints with AI analysis",
)
def get_manager_complaint_view(
    db: DatabaseSession,
    _current_manager: ManagerUser,
) -> list[schemas.ManagerComplaintView]:
    """
    Return complaints and AI analyses to a manager.
    """

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
        .order_by(
            models.Complaint.created_at.desc()
        )
    )

    rows = db.execute(statement).all()

    results: list[
        schemas.ManagerComplaintView
    ] = []

    for complaint, analysis in rows:
        results.append(
            schemas.ManagerComplaintView(
                complaint_id=complaint.id,
                customer_name=(
                    complaint.customer_name
                ),
                customer_email=(
                    complaint.customer_email
                ),
                subject=complaint.subject,
                original_description=(
                    complaint.description
                ),
                complaint_status=complaint.status,
                created_at=complaint.created_at,
                analysis_status=(
                    analysis.analysis_status
                    if analysis
                    else None
                ),
                summary=(
                    analysis.summary
                    if analysis
                    else None
                ),
                category=(
                    analysis.category
                    if analysis
                    else None
                ),
                subcategory=(
                    analysis.subcategory
                    if analysis
                    else None
                ),
                priority=(
                    analysis.priority
                    if analysis
                    else None
                ),
                sentiment=(
                    analysis.sentiment
                    if analysis
                    else None
                ),
                fraud_suspected=(
                    analysis.fraud_suspected
                    if analysis
                    else None
                ),
                fraud_risk_level=(
                    analysis.fraud_risk_level
                    if analysis
                    else None
                ),
                transaction_amount=(
                    analysis.transaction_amount
                    if analysis
                    else None
                ),
                currency=(
                    analysis.currency
                    if analysis
                    else None
                ),
                transaction_date=(
                    analysis.transaction_date
                    if analysis
                    else None
                ),
                merchant_name=(
                    analysis.merchant_name
                    if analysis
                    else None
                ),
                payment_channel=(
                    analysis.payment_channel
                    if analysis
                    else None
                ),
                recommended_department=(
                    analysis.recommended_department
                    if analysis
                    else None
                ),
                red_flags=(
                    analysis.red_flags
                    if analysis
                    else None
                ),
                recommended_actions=(
                    analysis.recommended_actions
                    if analysis
                    else None
                ),
                customer_requested_resolution=(
                    analysis.customer_requested_resolution
                    if analysis
                    else None
                ),
                confidence_score=(
                    analysis.confidence_score
                    if analysis
                    else None
                ),
            )
        )

    return results


@router.patch(
    "/{complaint_id}/status",
    response_model=(
        schemas.ComplaintStatusUpdateResponse
    ),
    summary="Update complaint status",
)
def update_complaint_status(
    complaint_id: int,
    status_data: schemas.ComplaintStatusUpdate,
    db: DatabaseSession,
    _current_manager: ManagerUser,
) -> schemas.ComplaintStatusUpdateResponse:
    """
    Update a complaint status and generate a customer email.

    The generated email is saved in the complaint_emails
    database table. It is not automatically sent.
    """

    complaint = db.get(
        models.Complaint,
        complaint_id,
    )

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Complaint with ID {complaint_id} "
                "was not found."
            ),
        )

    previous_status = complaint.status
    requested_status = status_data.status

    if requested_status == previous_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Complaint is already in "
                f"'{previous_status.value}' status."
            ),
        )

    allowed_transitions: dict[
        models.ComplaintStatus,
        set[models.ComplaintStatus],
    ] = {
        models.ComplaintStatus.SUBMITTED: {
            models.ComplaintStatus.UNDER_REVIEW,
            models.ComplaintStatus.REJECTED,
        },
        models.ComplaintStatus.UNDER_REVIEW: {
            models.ComplaintStatus.RESOLVED,
            models.ComplaintStatus.REJECTED,
        },
        models.ComplaintStatus.RESOLVED: set(),
        models.ComplaintStatus.REJECTED: set(),
    }

    allowed_next_statuses = (
        allowed_transitions.get(
            previous_status,
            set(),
        )
    )

    if requested_status not in allowed_next_statuses:
        allowed_values = [
            status_value.value
            for status_value in allowed_next_statuses
        ]

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": (
                    "Status cannot be changed from "
                    f"'{previous_status.value}' to "
                    f"'{requested_status.value}'."
                ),
                "allowed_next_statuses": (
                    allowed_values
                ),
            },
        )

    try:
        generated_email = generate_customer_email(
            customer_name=complaint.customer_name,
            complaint_subject=complaint.subject,
            complaint_description=(
                complaint.description
            ),
            complaint_status=(
                requested_status.value
            ),
            complaint_id=complaint.id,
            manager_note=status_data.manager_note,
        )

    except EmailGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    complaint.status = requested_status

    complaint_email = models.ComplaintEmail(
        complaint_id=complaint.id,
        subject=generated_email.subject,
        email_body=generated_email.email_body,
    )

    try:
        db.add(complaint_email)
        db.commit()

        db.refresh(complaint)
        db.refresh(complaint_email)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail=(
                "The complaint status and generated "
                "email could not be saved."
            ),
        ) from exc

    return schemas.ComplaintStatusUpdateResponse(
        message=(
            "Complaint status updated and customer "
            "email generated successfully."
        ),
        previous_status=previous_status,
        current_status=complaint.status,
        complaint=complaint,
        generated_email=complaint_email,
    )


@router.post(
    "/{complaint_id}/emails/{email_id}/send",
    response_model=EmailSendResponse,
    summary="Send a stored complaint email",
)
def send_stored_complaint_email(
    complaint_id: int,
    email_id: int,
    db: DatabaseSession,
    _current_manager: ManagerUser,
) -> EmailSendResponse:
    """
    Send one stored AI-generated email to the customer.

    The complaint email address stored during complaint
    submission is used as the recipient.

    Only managers can access this route.
    """

    complaint = db.get(
        models.Complaint,
        complaint_id,
    )

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Complaint with ID {complaint_id} "
                "was not found."
            ),
        )

    email_statement = select(
        models.ComplaintEmail
    ).where(
        models.ComplaintEmail.id == email_id,
        models.ComplaintEmail.complaint_id
        == complaint_id,
    )

    complaint_email = db.scalar(
        email_statement
    )

    if complaint_email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Email with ID {email_id} was not "
                f"found for complaint {complaint_id}."
            ),
        )

    try:
        send_customer_email(
            recipient_email=(
                complaint.customer_email
            ),
            subject=complaint_email.subject,
            email_body=(
                complaint_email.email_body
            ),
        )

    except EmailSendingError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return EmailSendResponse(
        message="Customer email sent successfully.",
        complaint_id=complaint.id,
        email_id=complaint_email.id,
        recipient=complaint.customer_email,
        subject=complaint_email.subject,
    )