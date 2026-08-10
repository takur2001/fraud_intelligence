from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


class APIClientError(Exception):
    """
    Custom exception raised when the FastAPI backend
    returns an error or cannot be reached.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)

        self.status_code = status_code
        self.details = details


@dataclass
class APIClient:
    """
    Handles communication between Streamlit and FastAPI.
    """

    base_url: str
    timeout_seconds: int = 60

    def __post_init__(self) -> None:
        """
        Remove a trailing slash from the API URL.

        Example:
        http://127.0.0.1:8000/
        becomes:
        http://127.0.0.1:8000
        """

        self.base_url = self.base_url.rstrip("/")

    def _create_headers(
        self,
        token: str | None = None,
    ) -> dict[str, str]:
        """
        Create HTTP headers for an API request.

        When a JWT token is provided, it is added as a
        Bearer token.
        """

        headers = {
            "Accept": "application/json",
        }

        if token:
            headers["Authorization"] = (
                f"Bearer {token}"
            )

        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json_data: dict[str, Any] | None = None,
        form_data: dict[str, Any] | None = None,
        expected_statuses: set[int] | None = None,
    ) -> Any:
        """
        Send an HTTP request to FastAPI.

        All frontend API methods use this common method.
        """

        if expected_statuses is None:
            expected_statuses = {200}

        url = f"{self.base_url}{path}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._create_headers(token),
                json=json_data,
                data=form_data,
                timeout=self.timeout_seconds,
            )

        except requests.ConnectionError as exc:
            raise APIClientError(
                "Could not connect to the FastAPI backend. "
                "Make sure Uvicorn is running."
            ) from exc

        except requests.Timeout as exc:
            raise APIClientError(
                "The backend request took too long. "
                "Gemini or Gmail SMTP may still be processing."
            ) from exc

        except requests.RequestException as exc:
            raise APIClientError(
                f"An API request error occurred: {exc}"
            ) from exc

        try:
            response_body = response.json()

        except ValueError:
            response_body = response.text

        if response.status_code not in expected_statuses:
            error_message = self._extract_error_message(
                response_body=response_body,
                status_code=response.status_code,
            )

            raise APIClientError(
                error_message,
                status_code=response.status_code,
                details=response_body,
            )

        return response_body

    @staticmethod
    def _extract_error_message(
        *,
        response_body: Any,
        status_code: int,
    ) -> str:
        """
        Convert FastAPI error responses into readable messages.
        """

        if isinstance(response_body, str):
            return response_body

        if not isinstance(response_body, dict):
            return (
                f"The backend returned HTTP "
                f"{status_code}."
            )

        detail = response_body.get("detail")

        if isinstance(detail, str):
            return detail

        if isinstance(detail, dict):
            message = detail.get("message")
            allowed_statuses = detail.get(
                "allowed_next_statuses"
            )

            if message and allowed_statuses is not None:
                allowed_text = (
                    ", ".join(allowed_statuses)
                    if allowed_statuses
                    else "none"
                )

                return (
                    f"{message} "
                    f"Allowed next statuses: "
                    f"{allowed_text}."
                )

            return str(detail)

        if isinstance(detail, list):
            messages: list[str] = []

            for validation_error in detail:
                if not isinstance(
                    validation_error,
                    dict,
                ):
                    messages.append(
                        str(validation_error)
                    )
                    continue

                location_parts = (
                    validation_error.get(
                        "loc",
                        [],
                    )
                )

                location = " → ".join(
                    str(part)
                    for part in location_parts
                )

                message = validation_error.get(
                    "msg",
                    "Invalid value.",
                )

                if location:
                    messages.append(
                        f"{location}: {message}"
                    )
                else:
                    messages.append(message)

            return "\n".join(messages)

        return (
            f"The backend returned HTTP "
            f"{status_code}."
        )

    def health_check(self) -> dict[str, Any]:
        """
        Check whether the FastAPI backend is running.

        Backend route:
        GET /health
        """

        return self._request(
            method="GET",
            path="/health",
            expected_statuses={200},
        )

    def register_customer(
        self,
        *,
        full_name: str,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        """
        Register a customer account.

        Backend route:
        POST /auth/register
        """

        return self._request(
            method="POST",
            path="/auth/register",
            json_data={
                "full_name": full_name,
                "email": email,
                "password": password,
            },
            expected_statuses={201},
        )

    def login(
        self,
        *,
        email: str,
        password: str,
    ) -> dict[str, Any]:
        """
        Log in and receive a JWT access token.

        Backend route:
        POST /auth/login

        OAuth2PasswordRequestForm requires form data,
        not a JSON request body.

        The email must be sent using the field name
        "username".
        """

        return self._request(
            method="POST",
            path="/auth/login",
            form_data={
                "username": email,
                "password": password,
            },
            expected_statuses={200},
        )

    def submit_complaint(
        self,
        *,
        customer_name: str,
        customer_email: str,
        subject: str,
        description: str,
        account_reference: str | None,
    ) -> dict[str, Any]:
        """
        Submit a complaint and run Gemini analysis.

        Backend route:
        POST /complaints
        """

        return self._request(
            method="POST",
            path="/complaints",
            json_data={
                "customer_name": customer_name,
                "customer_email": customer_email,
                "subject": subject,
                "description": description,
                "account_reference": (
                    account_reference
                    if account_reference
                    else None
                ),
            },
            expected_statuses={201},
        )

    def get_manager_complaints(
        self,
        *,
        token: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve complaints with Gemini analysis.

        Only managers can use this endpoint.

        Backend route:
        GET /complaints/manager-view
        """

        return self._request(
            method="GET",
            path="/complaints/manager-view",
            token=token,
            expected_statuses={200},
        )

    def update_complaint_status(
        self,
        *,
        token: str,
        complaint_id: int,
        new_status: str,
        manager_note: str | None,
    ) -> dict[str, Any]:
        """
        Update complaint status and generate an AI email.

        Only managers can use this endpoint.

        Backend route:
        PATCH /complaints/{complaint_id}/status
        """

        return self._request(
            method="PATCH",
            path=(
                f"/complaints/"
                f"{complaint_id}/status"
            ),
            token=token,
            json_data={
                "status": new_status,
                "manager_note": (
                    manager_note
                    if manager_note
                    else None
                ),
            },
            expected_statuses={200},
        )

    def send_complaint_email(
        self,
        *,
        token: str,
        complaint_id: int,
        email_id: int,
    ) -> dict[str, Any]:
        """
        Send a stored AI-generated email through Gmail SMTP.

        Only managers can use this endpoint.

        Backend route:
        POST /complaints/{complaint_id}/emails/{email_id}/send
        """

        return self._request(
            method="POST",
            path=(
                f"/complaints/{complaint_id}"
                f"/emails/{email_id}/send"
            ),
            token=token,
            expected_statuses={200},
        )