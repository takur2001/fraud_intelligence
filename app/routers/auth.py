from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app import models, schemas
from app.dependencies import (
    CurrentUser,
    DatabaseSession,
)
from app.services.security import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post(
    "/register",
    response_model=schemas.UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a customer account",
)
def register_user(
    registration_data: schemas.UserRegister,
    db: DatabaseSession,
) -> schemas.UserRegistrationResponse:
    """
    Register a new customer account.

    Public registration cannot create manager accounts.
    """

    normalized_email = str(
        registration_data.email
    ).strip().lower()

    existing_user_statement = select(models.User).where(
        models.User.email == normalized_email
    )

    existing_user = db.scalar(existing_user_statement)

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    new_user = models.User(
        full_name=registration_data.full_name.strip(),
        email=normalized_email,
        hashed_password=hash_password(
            registration_data.password
        ),
        role=models.UserRole.CUSTOMER,
        is_active=True,
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The user account could not be created.",
        ) from exc

    return schemas.UserRegistrationResponse(
        message="Customer account created successfully.",
        user=new_user,
    )


@router.post(
    "/login",
    response_model=schemas.TokenResponse,
    summary="Log in and receive an access token",
)
def login(
    db: DatabaseSession,
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> schemas.TokenResponse:
    """
    Authenticate a user using email and password.

    OAuth2 calls the email field 'username'.
    """

    normalized_email = form_data.username.strip().lower()

    statement = select(models.User).where(
        models.User.email == normalized_email
    )

    user = db.scalar(statement)

    invalid_credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if user is None:
        raise invalid_credentials_error

    if not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise invalid_credentials_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive.",
        )

    access_token = create_access_token(
        subject=user.email,
        role=user.role.value,
    )

    return schemas.TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )