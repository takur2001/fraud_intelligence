from __future__ import annotations

from typing import Any

import streamlit as st


DEFAULT_SESSION_STATE: dict[str, Any] = {
    "access_token": None,
    "authenticated": False,
    "user_email": None,
    "user_role": None,
    "manager_complaints": [],
    "selected_complaint_id": None,
    "generated_email": None,
    "last_submission": None,
}


def initialize_session_state() -> None:
    """
    Create all Streamlit Session State values used by the frontend.

    Streamlit reruns the entire Python script whenever the user
    clicks a button, submits a form, or changes an input.

    Session State keeps important values available between those reruns.
    """

    for key, default_value in DEFAULT_SESSION_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def create_login_session(
    *,
    access_token: str,
    email: str,
    role: str,
) -> None:
    """
    Save successful login information in Streamlit Session State.

    The JWT token is later sent to manager-protected FastAPI routes.
    """

    st.session_state.access_token = access_token
    st.session_state.authenticated = True
    st.session_state.user_email = email.strip().lower()
    st.session_state.user_role = role.strip().lower()

    # Clear old data from a previous login session.
    st.session_state.manager_complaints = []
    st.session_state.selected_complaint_id = None
    st.session_state.generated_email = None


def clear_login_session() -> None:
    """
    Remove authentication and temporary frontend data.

    This function is used when the user clicks Log out.
    """

    for key, default_value in DEFAULT_SESSION_STATE.items():
        st.session_state[key] = default_value


def is_authenticated() -> bool:
    """
    Return True when the current Streamlit session has a JWT token.
    """

    return bool(
        st.session_state.get("authenticated")
        and st.session_state.get("access_token")
    )


def is_manager() -> bool:
    """
    Return True when the frontend session belongs to a manager.

    This function controls what the frontend displays.

    FastAPI still performs the real authorization using the JWT
    and ManagerUser dependency.
    """

    return bool(
        is_authenticated()
        and st.session_state.get("user_role") == "manager"
    )


def get_access_token() -> str | None:
    """
    Return the JWT token stored after login.
    """

    token = st.session_state.get("access_token")

    if isinstance(token, str) and token:
        return token

    return None


def save_manager_complaints(
    complaints: list[dict[str, Any]],
) -> None:
    """
    Save complaints returned by the manager-view API.
    """

    st.session_state.manager_complaints = complaints


def get_manager_complaints() -> list[dict[str, Any]]:
    """
    Return complaints currently stored in Session State.
    """

    complaints = st.session_state.get(
        "manager_complaints",
        [],
    )

    if isinstance(complaints, list):
        return complaints

    return []


def select_complaint(
    complaint_id: int | None,
) -> None:
    """
    Save the complaint currently selected by the manager.
    """

    st.session_state.selected_complaint_id = complaint_id


def get_selected_complaint_id() -> int | None:
    """
    Return the complaint ID currently selected by the manager.
    """

    complaint_id = st.session_state.get(
        "selected_complaint_id"
    )

    if isinstance(complaint_id, int):
        return complaint_id

    return None


def save_generated_email(
    generated_email_response: dict[str, Any],
) -> None:
    """
    Save the response returned after a complaint status update.

    The response contains:
    - Updated complaint information
    - Previous and current status
    - Generated email ID
    - Generated email subject
    - Generated email body
    """

    st.session_state.generated_email = (
        generated_email_response
    )


def get_generated_email() -> dict[str, Any] | None:
    """
    Return the most recently generated customer email response.
    """

    generated_email = st.session_state.get(
        "generated_email"
    )

    if isinstance(generated_email, dict):
        return generated_email

    return None


def clear_generated_email() -> None:
    """
    Remove the currently displayed generated email.
    """

    st.session_state.generated_email = None


def save_last_submission(
    submission_response: dict[str, Any],
) -> None:
    """
    Save the latest customer complaint submission response.

    This allows the frontend to continue displaying the complaint
    and Gemini analysis after Streamlit reruns the page.
    """

    st.session_state.last_submission = (
        submission_response
    )


def get_last_submission() -> dict[str, Any] | None:
    """
    Return the latest complaint submission response.
    """

    submission = st.session_state.get(
        "last_submission"
    )

    if isinstance(submission, dict):
        return submission

    return None


def clear_last_submission() -> None:
    """
    Remove the latest complaint submission result.
    """

    st.session_state.last_submission = None