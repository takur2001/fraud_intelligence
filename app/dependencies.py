from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.services.security import decode_access_token


DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DatabaseSession,
) -> models.User:
    """
    Validate the JWT and retrieve the authenticated user.
    """

    authentication_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)

        email = payload.get("sub")

        if not isinstance(email, str) or not email:
            raise authentication_error

    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    except jwt.InvalidTokenError as exc:
        raise authentication_error from exc

    statement = select(models.User).where(
        models.User.email == email.lower()
    )

    user = db.scalar(statement)

    if user is None:
        raise authentication_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account is inactive.",
        )

    return user


CurrentUser = Annotated[
    models.User,
    Depends(get_current_user),
]


def require_manager(
    current_user: CurrentUser,
) -> models.User:
    """
    Allow access only to users with the manager role.
    """

    if current_user.role != models.UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access is required.",
        )

    return current_user


ManagerUser = Annotated[
    models.User,
    Depends(require_manager),
]