from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from api_client import APIClient, APIClientError
from session_state import (
    clear_generated_email,
    clear_login_session,
    create_login_session,
    get_access_token,
    get_generated_email,
    get_last_submission,
    get_manager_complaints,
    initialize_session_state,
    is_authenticated,
    is_manager,
    save_generated_email,
    save_last_submission,
    save_manager_complaints,
)


load_dotenv()

st.set_page_config(
    page_title="Fraud Intelligence",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session_state()

if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"

FASTAPI_BASE_URL = os.getenv(
    "FASTAPI_BASE_URL",
    "http://127.0.0.1:8000",
)

api = APIClient(base_url=FASTAPI_BASE_URL)

STATUS_LABELS: dict[str, str] = {
    "submitted": "Submitted",
    "under_review": "Under Review",
    "resolved": "Resolved",
    "rejected": "Rejected",
}

VALID_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "submitted": ["under_review", "rejected"],
    "under_review": ["resolved", "rejected"],
    "resolved": [],
    "rejected": [],
}


def apply_custom_styles() -> None:
    """Apply the visual design used across the application."""

    st.html(
        """
        <style>
        .main .block-container {
            max-width: 1440px;
            padding-top: 1.25rem;
            padding-bottom: 4rem;
        }

        header[data-testid="stHeader"] {
            background: transparent;
        }

        h1, h2, h3 {
            letter-spacing: -0.02em;
        }

        p {
            line-height: 1.65;
        }

        .top-brand {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .brand-icon {
            width: 42px;
            height: 42px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            font-size: 1.3rem;
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
        }

        .brand-title {
            font-size: 1.05rem;
            font-weight: 750;
            color: #172033;
            margin: 0;
        }

        .brand-subtitle {
            font-size: 0.78rem;
            color: #64748b;
            margin: 0;
        }

        .hero-container {
            padding: 2.1rem 2.2rem;
            margin-top: 1.2rem;
            margin-bottom: 1.5rem;
            border-radius: 22px;
            color: white;
            background:
                radial-gradient(circle at top right, rgba(96, 165, 250, 0.30), transparent 32%),
                linear-gradient(135deg, #0f172a 0%, #172554 55%, #1d4ed8 100%);
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.18);
        }

        .hero-eyebrow {
            display: inline-block;
            padding: 0.38rem 0.75rem;
            border-radius: 999px;
            margin-bottom: 1rem;
            font-size: 0.78rem;
            font-weight: 650;
            letter-spacing: 0.04em;
            background: rgba(255, 255, 255, 0.13);
            border: 1px solid rgba(255, 255, 255, 0.20);
        }

        .hero-title {
            margin: 0;
            color: white;
            font-size: clamp(2rem, 4vw, 3.3rem);
            line-height: 1.08;
            letter-spacing: -0.04em;
        }

        .hero-description {
            max-width: 780px;
            margin-top: 1rem;
            margin-bottom: 0;
            color: #dbeafe;
            font-size: 1.05rem;
            line-height: 1.7;
        }

        .feature-card {
            min-height: 175px;
            padding: 1.25rem;
            border-radius: 17px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.22);
            box-shadow: 0 8px 25px rgba(15, 23, 42, 0.06);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .feature-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.10);
        }

        .feature-icon {
            width: 42px;
            height: 42px;
            margin-bottom: 1rem;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #eff6ff;
            font-size: 1.25rem;
        }

        .feature-title {
            margin: 0 0 0.45rem 0;
            font-size: 1rem;
            font-weight: 750;
            color: #172033;
        }

        .feature-description {
            margin: 0;
            color: #64748b;
            font-size: 0.9rem;
            line-height: 1.6;
        }

        .page-eyebrow {
            color: #2563eb;
            font-size: 0.78rem;
            font-weight: 750;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }

        .page-description {
            color: #64748b;
            max-width: 760px;
            margin-top: -0.5rem;
            margin-bottom: 1.5rem;
        }

        .security-notice {
            padding: 1rem 1.15rem;
            margin-top: 1.25rem;
            border-radius: 14px;
            color: #854d0e;
            background: #fffbeb;
            border: 1px solid #fde68a;
            font-size: 0.9rem;
        }

        .sidebar-brand {
            padding: 0.5rem 0 0.25rem 0;
        }

        .sidebar-brand-title {
            margin: 0;
            color: #f8fafc;
            font-size: 1.05rem;
            font-weight: 750;
        }

        .sidebar-brand-subtitle {
            margin-top: 0.4rem;
            color: #94a3b8;
            font-size: 0.78rem;
            line-height: 1.5;
        }

        .sidebar-section-label {
            margin: 1rem 0 0.5rem;
            color: #64748b;
            font-size: 0.7rem;
            font-weight: 750;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }

        .stButton > button {
            border-radius: 10px;
            font-weight: 650;
            min-height: 42px;
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 15px rgba(37, 99, 235, 0.16);
        }

        .stTextInput input,
        .stTextArea textarea {
            border-radius: 10px;
        }

        button[data-baseweb="tab"] {
            font-weight: 650;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 14px;
            overflow: hidden;
            border: 1px solid rgba(148, 163, 184, 0.22);
        }

        @media (max-width: 768px) {
            .main .block-container {
                padding-top: 0.75rem;
            }

            .hero-container {
                padding: 1.5rem;
            }

            .hero-title {
                font-size: 2rem;
            }
        }
        </style>
        """
    )


def set_current_page(page_name: str) -> None:
    """Change the current application page."""

    st.session_state.current_page = page_name


def get_current_page() -> str:
    """Return the currently selected page."""

    return str(st.session_state.get("current_page", "Home"))


def display_api_error(error: APIClientError) -> None:
    """Display readable API errors."""

    if error.status_code == 401:
        st.error("Your login session is invalid or expired. Please sign in again.")
    elif error.status_code == 403:
        st.error("Manager access is required for this action.")
    elif error.status_code == 404:
        st.error(f"The requested information was not found. {error}")
    elif error.status_code == 409:
        st.error(str(error))
    elif error.status_code == 422:
        st.error(f"Please review the information entered.\n\n{error}")
    elif error.status_code == 502:
        st.error(
            "The request reached the backend, but an external service failed.\n\n"
            f"{error}"
        )
    else:
        st.error(str(error))


def format_datetime(datetime_value: str | None) -> str:
    """Format an ISO datetime value for display."""

    if not datetime_value:
        return "Not available"

    try:
        parsed_datetime = datetime.fromisoformat(
            datetime_value.replace("Z", "+00:00")
        )
        return parsed_datetime.strftime("%b %d, %Y · %I:%M %p")
    except ValueError:
        return datetime_value


def format_status(status_value: str | None) -> str:
    """Convert API status values into readable labels."""

    if not status_value:
        return "Not available"

    return STATUS_LABELS.get(
        status_value,
        status_value.replace("_", " ").title(),
    )


def detect_user_role(access_token: str) -> str:
    """Detect whether the logged-in user is a manager."""

    try:
        api.get_manager_complaints(token=access_token)
        return "manager"
    except APIClientError as error:
        if error.status_code == 403:
            return "customer"
        raise


def render_top_navigation() -> None:
    """Display the application header."""

    with st.container(border=True):
        brand_column, _, action_column = st.columns(
            [5, 2, 3],
            vertical_alignment="center",
        )

        with brand_column:
            st.html(
                """
                <div class="top-brand">
                    <div class="brand-icon">🏦</div>
                    <div>
                        <p class="brand-title">Fraud Intelligence</p>
                        <p class="brand-subtitle">Secure banking complaint management</p>
                    </div>
                </div>
                """
            )

        with action_column:
            if not is_authenticated():
                login_column, register_column = st.columns(2)

                with login_column:
                    if st.button(
                        "Sign in",
                        key="top_sign_in",
                        use_container_width=True,
                    ):
                        set_current_page("Login")
                        st.rerun()

                with register_column:
                    if st.button(
                        "Create account",
                        key="top_create_account",
                        type="primary",
                        use_container_width=True,
                    ):
                        set_current_page("Register")
                        st.rerun()
            else:
                account_column, action_button_column = st.columns([1.25, 1])

                with account_column:
                    with st.popover("👤 Account", use_container_width=True):
                        user_email = st.session_state.get(
                            "user_email",
                            "Unknown user",
                        )
                        user_role = str(
                            st.session_state.get("user_role", "customer")
                        ).title()

                        st.write("**Signed in as**")
                        st.write(user_email)
                        st.caption(f"Role: {user_role}")
                        st.divider()

                        if st.button(
                            "Sign out",
                            key="account_sign_out",
                            use_container_width=True,
                        ):
                            clear_login_session()
                            set_current_page("Home")
                            st.rerun()

                with action_button_column:
                    if is_manager():
                        if st.button(
                            "Workspace",
                            key="top_workspace",
                            type="primary",
                            use_container_width=True,
                        ):
                            set_current_page("Manager Workspace")
                            st.rerun()
                    else:
                        if st.button(
                            "New complaint",
                            key="top_new_complaint",
                            type="primary",
                            use_container_width=True,
                        ):
                            set_current_page("Submit Complaint")
                            st.rerun()


def render_sidebar() -> None:
    """Display product navigation in the sidebar."""

    with st.sidebar:
        st.html(
            """
            <div class="sidebar-brand">
                <p class="sidebar-brand-title">🏦 Fraud Intelligence</p>
                <p class="sidebar-brand-subtitle">
                    AI-assisted complaint intake, fraud analysis,
                    and resolution workflow.
                </p>
            </div>
            """
        )

        try:
            health_response = api.health_check()

            if health_response.get("status") == "healthy":
                st.success("System operational", icon="✅")
            else:
                st.warning("Backend response requires attention.")
        except APIClientError:
            st.error("Backend unavailable", icon="🚫")

        st.divider()
        st.html('<div class="sidebar-section-label">Main navigation</div>')

        current_page = get_current_page()

        if st.button(
            "⌂  Home",
            key="sidebar_home",
            type="primary" if current_page == "Home" else "secondary",
            use_container_width=True,
        ):
            set_current_page("Home")
            st.rerun()

        if st.button(
            "✎  Submit Complaint",
            key="sidebar_submit_complaint",
            type=(
                "primary"
                if current_page == "Submit Complaint"
                else "secondary"
            ),
            use_container_width=True,
        ):
            set_current_page("Submit Complaint")
            st.rerun()

        if is_manager():
            if st.button(
                "▦  Manager Workspace",
                key="sidebar_manager_workspace",
                type=(
                    "primary"
                    if current_page == "Manager Workspace"
                    else "secondary"
                ),
                use_container_width=True,
            ):
                set_current_page("Manager Workspace")
                st.rerun()

        st.divider()

        if is_authenticated():
            st.html('<div class="sidebar-section-label">Current session</div>')
            st.caption(st.session_state.get("user_email", ""))
            user_role = str(st.session_state.get("user_role", "")).title()
            st.caption(f"Role: {user_role}")
        else:
            st.caption(
                "You can submit a complaint without signing in. "
                "Sign in or create an account using the buttons at the top-right."
            )

        st.divider()
        st.caption(f"API: {FASTAPI_BASE_URL}")


def render_home_page() -> None:
    """Display the public landing page."""

    st.html(
        """
        <div class="hero-container">
            <div class="hero-eyebrow">BANKING COMPLAINT INTELLIGENCE</div>
            <h1 class="hero-title">
                Resolve banking complaints with clarity and speed.
            </h1>
            <p class="hero-description">
                A secure AI-assisted platform for complaint intake,
                fraud-risk analysis, manager review, customer
                communication, and case resolution.
            </p>
        </div>
        """
    )

    customer_column, analysis_column, manager_column = st.columns(3)

    with customer_column:
        st.html(
            """
            <div class="feature-card">
                <div class="feature-icon">📝</div>
                <p class="feature-title">Simple complaint intake</p>
                <p class="feature-description">
                    Customers can submit complaint details using a guided form
                    that clearly explains what information is required.
                </p>
            </div>
            """
        )

    with analysis_column:
        st.html(
            """
            <div class="feature-card">
                <div class="feature-icon">✨</div>
                <p class="feature-title">Structured Gemini analysis</p>
                <p class="feature-description">
                    Gemini classifies the complaint, evaluates priority and
                    fraud indicators, and recommends appropriate manager actions.
                </p>
            </div>
            """
        )

    with manager_column:
        st.html(
            """
            <div class="feature-card">
                <div class="feature-icon">🛡️</div>
                <p class="feature-title">Controlled manager workflow</p>
                <p class="feature-description">
                    Authorized managers review complaints, update case status,
                    preview generated communications, and send emails securely.
                </p>
            </div>
            """
        )

    st.html(
        """
        <div class="security-notice">
            <strong>Human review required:</strong>
            Gemini fraud indicators and recommendations are preliminary
            decision-support information. A bank manager must verify the
            analysis before taking action.
        </div>
        """
    )

    st.write("")
    action_left, action_right, _ = st.columns([1.35, 1.35, 3])

    with action_left:
        if st.button(
            "Submit a complaint",
            key="home_submit_complaint",
            type="primary",
            use_container_width=True,
        ):
            set_current_page("Submit Complaint")
            st.rerun()

    with action_right:
        if not is_authenticated():
            if st.button(
                "Sign in to your account",
                key="home_sign_in",
                use_container_width=True,
            ):
                set_current_page("Login")
                st.rerun()


def render_register_page() -> None:
    """Display the customer registration page."""

    st.html('<div class="page-eyebrow">Customer account</div>')
    st.title("Create your account")
    st.html(
        """
        <p class="page-description">
            Create a customer account using a valid email address.
            Public registration cannot create manager accounts.
        </p>
        """
    )

    form_column, information_column = st.columns([1.25, 0.75], gap="large")

    with form_column:
        with st.container(border=True):
            with st.form("customer_registration_form"):
                full_name = st.text_input(
                    "Full name",
                    max_chars=100,
                    placeholder="John Smith",
                )
                email = st.text_input(
                    "Email address",
                    placeholder="john.smith@example.com",
                )
                password = st.text_input(
                    "Password",
                    type="password",
                    help=(
                        "Use at least 8 characters. A stronger password should "
                        "include letters, numbers, and symbols."
                    ),
                )
                confirm_password = st.text_input(
                    "Confirm password",
                    type="password",
                )
                submitted = st.form_submit_button(
                    "Create customer account",
                    type="primary",
                    use_container_width=True,
                )

        if submitted:
            if password != confirm_password:
                st.error("The passwords do not match.")
            else:
                try:
                    response = api.register_customer(
                        full_name=full_name.strip(),
                        email=email.strip(),
                        password=password,
                    )
                    st.success(
                        response.get(
                            "message",
                            "Account created successfully.",
                        )
                    )
                    st.info(
                        "Your account is ready. Use the Sign in button above to continue."
                    )
                except APIClientError as error:
                    display_api_error(error)

    with information_column:
        st.info(
            """
            **Why create an account?**

            Your account provides secure authentication and prepares the
            application for customer-specific complaint history and future
            notifications.
            """
        )
        st.warning(
            """
            Never enter banking passwords, PINs, CVVs, Social Security numbers,
            or complete account numbers in this application.
            """
        )


def render_login_page() -> None:
    """Display the login page."""

    st.html('<div class="page-eyebrow">Secure access</div>')
    st.title("Welcome back")
    st.html(
        """
        <p class="page-description">
            Sign in using your customer or manager account.
            Your permissions are verified by the FastAPI backend.
        </p>
        """
    )

    _, form_column, _ = st.columns([0.7, 1.2, 0.7])

    with form_column:
        with st.container(border=True):
            st.subheader("Sign in")

            with st.form("login_form"):
                email = st.text_input(
                    "Email address",
                    placeholder="manager@example.com",
                )
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Sign in securely",
                    type="primary",
                    use_container_width=True,
                )

            if submitted:
                try:
                    with st.spinner("Verifying your account..."):
                        login_response = api.login(
                            email=email.strip(),
                            password=password,
                        )
                        access_token = login_response.get("access_token")

                        if not access_token:
                            st.error("The backend did not return an access token.")
                            return

                        role = detect_user_role(access_token)
                        create_login_session(
                            access_token=access_token,
                            email=email,
                            role=role,
                        )

                    if role == "manager":
                        set_current_page("Manager Workspace")
                    else:
                        set_current_page("Submit Complaint")
                    st.rerun()
                except APIClientError as error:
                    display_api_error(error)

            st.divider()
            st.caption("New customer?")

            if st.button(
                "Create a customer account",
                key="login_create_account",
                use_container_width=True,
            ):
                set_current_page("Register")
                st.rerun()


def render_submit_complaint_page() -> None:
    """
    Display the customer complaint submission page.

    The form collects complaint information and sends it
    to the FastAPI backend for storage and Gemini analysis.
    """

    st.html(
        '<div class="page-eyebrow">Complaint intake</div>'
    )

    st.title("Tell us what happened")

    st.html(
        """
        <p class="page-description">
            Provide clear details about the banking issue.
            The complaint will be securely stored and analyzed
            by Gemini for manager review.
        </p>
        """
    )

    logged_in_email = (
        st.session_state.get("user_email")
        if is_authenticated()
        else ""
    )

    form_column, guidance_column = st.columns(
        [1.55, 0.75],
        gap="large",
    )

    with form_column:
        with st.container(border=True):
            with st.form(
                "complaint_submission_form",
                clear_on_submit=False,
            ):
                customer_name = st.text_input(
                    "Full name",
                    max_chars=100,
                    placeholder="John Smith",
                )

                customer_email = st.text_input(
                    "Email address",
                    value=logged_in_email or "",
                    placeholder="john.smith@example.com",
                    help=(
                        "Complaint status emails will be sent "
                        "to this address."
                    ),
                )

                subject = st.text_input(
                    "Complaint subject",
                    max_chars=200,
                    placeholder=(
                        "Duplicate debit card transaction"
                    ),
                )

                description = st.text_area(
                    "Describe the issue",
                    height=200,
                    max_chars=5000,
                    placeholder=(
                        "Explain what happened, when it happened, "
                        "the amount involved, and the resolution "
                        "you are requesting."
                    ),
                )

                account_reference = st.text_input(
                    "Masked account reference — optional",
                    max_chars=20,
                    placeholder="XXXX1234",
                    help=(
                        "Enter only a masked reference such as "
                        "XXXX1234. Never enter a complete card "
                        "or account number."
                    ),
                )

                consent = st.checkbox(
                    "I confirm that I have not included passwords, "
                    "PINs, CVVs, Social Security numbers, or complete "
                    "account/card numbers."
                )

                submitted = st.form_submit_button(
                    "Submit and analyze complaint",
                    type="primary",
                    use_container_width=True,
                )

        if submitted:
            cleaned_name = customer_name.strip()
            cleaned_email = customer_email.strip()
            cleaned_subject = subject.strip()
            cleaned_description = description.strip()
            cleaned_reference = account_reference.strip()

            validation_errors: list[str] = []

            if not consent:
                validation_errors.append(
                    "Please confirm the sensitive-information statement."
                )

            if len(cleaned_name) < 2:
                validation_errors.append(
                    "Full name must contain at least 2 characters."
                )

            if not cleaned_email:
                validation_errors.append(
                    "Email address is required."
                )

            if len(cleaned_subject) < 5:
                validation_errors.append(
                    "Complaint subject must contain at least 5 characters."
                )

            if len(cleaned_description) < 20:
                validation_errors.append(
                    "Complaint description must contain at least 20 characters."
                )

            if cleaned_reference:
                if len(cleaned_reference) < 4:
                    validation_errors.append(
                        "Masked account reference must contain "
                        "at least 4 characters."
                    )

                if (
                    cleaned_reference.isdigit()
                    and len(cleaned_reference) > 4
                ):
                    validation_errors.append(
                        "Do not enter a complete account number. "
                        "Use a masked reference such as XXXX1234."
                    )

            if validation_errors:
                st.error(
                    "Please correct the following information:"
                )

                for validation_error in validation_errors:
                    st.write(f"• {validation_error}")

            else:
                try:
                    with st.spinner(
                        "Saving your complaint and running "
                        "the Gemini analysis..."
                    ):
                        response = api.submit_complaint(
                            customer_name=cleaned_name,
                            customer_email=cleaned_email,
                            subject=cleaned_subject,
                            description=cleaned_description,
                            account_reference=(
                                cleaned_reference
                                if cleaned_reference
                                else None
                            ),
                        )

                    save_last_submission(response)

                    st.success(
                        response.get(
                            "message",
                            "Complaint submitted successfully.",
                        )
                    )

                except APIClientError as error:
                    display_api_error(error)

    with guidance_column:
        st.info(
            """
            **Include these details**

            • What happened  
            • Date or approximate time  
            • Amount involved  
            • Merchant, ATM, or recipient  
            • What resolution you expect
            """
        )

        st.warning(
            """
            **Do not include**

            • Passwords  
            • PINs or CVVs  
            • Social Security numbers  
            • Full account or card numbers
            """
        )

    last_submission = get_last_submission()

    if last_submission:
        render_complaint_submission_result(
            last_submission
        )


def render_complaint_submission_result(response: dict[str, Any]) -> None:
    """Display complaint submission and Gemini analysis results."""

    complaint = response.get("complaint", {})
    analysis = response.get("analysis")

    st.divider()
    st.subheader("Complaint received")

    id_column, status_column, analysis_column = st.columns(3)
    id_column.metric("Complaint reference", complaint.get("id", "—"))
    status_column.metric("Current status", format_status(complaint.get("status")))

    analysis_status = (
        analysis.get("analysis_status", "unavailable")
        if analysis
        else "unavailable"
    )
    analysis_column.metric("AI analysis", str(analysis_status).title())

    if not analysis:
        st.warning("No AI analysis record was returned.")
        return

    if analysis.get("analysis_status") != "completed":
        st.warning(
            "The complaint was saved, but Gemini analysis was not completed."
        )
        if analysis.get("error_message"):
            st.error(analysis["error_message"])
        return

    st.subheader("Preliminary AI analysis")

    priority_column, category_column, fraud_column, risk_column = st.columns(4)
    priority_column.metric(
        "Priority",
        str(analysis.get("priority", "Not available")).title(),
    )
    category_column.metric(
        "Category",
        str(analysis.get("category", "Not available"))
        .replace("_", " ")
        .title(),
    )

    fraud_value = analysis.get("fraud_suspected")
    fraud_column.metric(
        "Fraud suspected",
        "Yes"
        if fraud_value is True
        else "No"
        if fraud_value is False
        else "Not available",
    )
    risk_column.metric(
        "Fraud risk",
        str(analysis.get("fraud_risk_level", "Not available")).title(),
    )

    with st.container(border=True):
        st.write("**Summary**")
        st.write(analysis.get("summary", "No summary returned."))

    left_column, right_column = st.columns(2)

    with left_column:
        with st.container(border=True):
            st.write("**Red flags**")
            red_flags = analysis.get("red_flags") or []
            if red_flags:
                for red_flag in red_flags:
                    st.write(f"• {red_flag}")
            else:
                st.write("No red flags identified.")

    with right_column:
        with st.container(border=True):
            st.write("**Recommended actions**")
            actions = analysis.get("recommended_actions") or []
            if actions:
                for action in actions:
                    st.write(f"• {action}")
            else:
                st.write("No actions were returned.")


def load_manager_complaints() -> None:
    """Load complaints for the authenticated manager."""

    token = get_access_token()
    if not token:
        st.error("Please sign in as a manager.")
        return

    try:
        with st.spinner("Loading complaints..."):
            complaints = api.get_manager_complaints(token=token)
        save_manager_complaints(complaints)
    except APIClientError as error:
        display_api_error(error)


def render_manager_workspace() -> None:
    """Display the manager complaint workspace."""

    st.html('<div class="page-eyebrow">Manager operations</div>')
    st.title("Complaint workspace")
    st.html(
        """
        <p class="page-description">
            Review customer complaints and Gemini analysis, update complaint
            status, preview customer communications, and send approved emails.
        </p>
        """
    )

    if not is_manager():
        st.error("Manager access is required.")
        return

    refresh_column, _ = st.columns([1, 4])
    with refresh_column:
        if st.button("Refresh complaints", use_container_width=True):
            load_manager_complaints()

    complaints = get_manager_complaints()
    if not complaints:
        load_manager_complaints()
        complaints = get_manager_complaints()

    if not complaints:
        st.info("No complaints are currently available.")
        return

    complaint_table_rows = []
    for complaint in complaints:
        fraud_value = complaint.get("fraud_suspected")
        complaint_table_rows.append(
            {
                "ID": complaint.get("complaint_id"),
                "Customer": complaint.get("customer_name"),
                "Subject": complaint.get("subject"),
                "Status": format_status(complaint.get("complaint_status")),
                "Priority": str(
                    complaint.get("priority") or "Not available"
                ).title(),
                "Fraud": "Yes"
                if fraud_value is True
                else "No"
                if fraud_value is False
                else "Unknown",
                "Created": format_datetime(complaint.get("created_at")),
            }
        )

    st.dataframe(
        pd.DataFrame(complaint_table_rows),
        use_container_width=True,
        hide_index=True,
    )

    complaint_lookup = {
        int(complaint["complaint_id"]): complaint for complaint in complaints
    }
    complaint_ids = list(complaint_lookup.keys())

    selected_complaint_id = st.selectbox(
        "Choose a complaint to review",
        options=complaint_ids,
        format_func=lambda complaint_id: (
            f"#{complaint_id} · "
            f"{complaint_lookup[complaint_id]['customer_name']} · "
            f"{complaint_lookup[complaint_id]['subject']}"
        ),
    )

    render_selected_manager_complaint(
        complaint_lookup[selected_complaint_id]
    )


def render_selected_manager_complaint(complaint: dict[str, Any]) -> None:
    """Display a selected complaint."""

    st.divider()
    title_column, status_column = st.columns([4, 1])

    with title_column:
        st.subheader(f"Complaint #{complaint['complaint_id']}")
        st.write(f"**{complaint['subject']}**")
        st.caption(
            f"{complaint['customer_name']} · "
            f"{complaint['customer_email']} · "
            f"{format_datetime(complaint.get('created_at'))}"
        )

    with status_column:
        st.metric(
            "Status",
            format_status(complaint.get("complaint_status")),
        )

    complaint_tab, analysis_tab, action_tab = st.tabs(
        ["Complaint details", "Gemini analysis", "Manager action"]
    )

    with complaint_tab:
        with st.container(border=True):
            st.write("**Original complaint**")
            st.write(
                complaint.get(
                    "original_description",
                    "No description available.",
                )
            )

    with analysis_tab:
        render_manager_analysis(complaint)

    with action_tab:
        render_manager_action(complaint)


def render_manager_analysis(complaint: dict[str, Any]) -> None:
    """Display Gemini analysis to a manager."""

    priority_column, category_column, fraud_column, risk_column = st.columns(4)
    priority_column.metric(
        "Priority",
        str(complaint.get("priority") or "Not available").title(),
    )
    category_column.metric(
        "Category",
        str(complaint.get("category") or "Not available")
        .replace("_", " ")
        .title(),
    )

    fraud_value = complaint.get("fraud_suspected")
    fraud_column.metric(
        "Fraud suspected",
        "Yes"
        if fraud_value is True
        else "No"
        if fraud_value is False
        else "Not available",
    )
    risk_column.metric(
        "Risk level",
        str(complaint.get("fraud_risk_level") or "Not available").title(),
    )

    with st.container(border=True):
        st.write("**AI summary**")
        st.write(complaint.get("summary") or "No summary available.")

    red_flags_column, actions_column = st.columns(2)

    with red_flags_column:
        with st.container(border=True):
            st.write("**Red flags**")
            red_flags = complaint.get("red_flags") or []
            if red_flags:
                for item in red_flags:
                    st.write(f"• {item}")
            else:
                st.write("No red flags returned.")

    with actions_column:
        with st.container(border=True):
            st.write("**Recommended actions**")
            actions = complaint.get("recommended_actions") or []
            if actions:
                for item in actions:
                    st.write(f"• {item}")
            else:
                st.write("No actions returned.")


def render_manager_action(complaint: dict[str, Any]) -> None:
    """Update status, preview email, and send through Gmail."""

    current_status = complaint.get("complaint_status")
    allowed_statuses = VALID_STATUS_TRANSITIONS.get(current_status, [])

    if not allowed_statuses:
        st.info(
            f"This complaint is in the final status "
            f"'{format_status(current_status)}'."
        )
    else:
        with st.container(border=True):
            st.subheader("Update complaint status")

            with st.form(f"status_update_form_{complaint['complaint_id']}"):
                new_status = st.selectbox(
                    "New status",
                    options=allowed_statuses,
                    format_func=format_status,
                )
                manager_note = st.text_area(
                    "Manager note — optional",
                    height=120,
                    max_chars=2000,
                    placeholder=(
                        "Add only verified information that may be included "
                        "in the customer email."
                    ),
                )
                submitted = st.form_submit_button(
                    "Update status and generate email",
                    type="primary",
                    use_container_width=True,
                )

        if submitted:
            token = get_access_token()
            if not token:
                st.error("Your session is unavailable.")
                return

            try:
                with st.spinner(
                    "Updating the complaint and generating the email..."
                ):
                    response = api.update_complaint_status(
                        token=token,
                        complaint_id=int(complaint["complaint_id"]),
                        new_status=new_status,
                        manager_note=manager_note.strip() or None,
                    )

                save_generated_email(response)
                st.success(
                    response.get(
                        "message",
                        "Status updated successfully.",
                    )
                )
                load_manager_complaints()
            except APIClientError as error:
                display_api_error(error)

    generated_response = get_generated_email()
    if not generated_response:
        return

    generated_complaint = generated_response.get("complaint", {})
    generated_email = generated_response.get("generated_email", {})

    if generated_complaint.get("id") != complaint.get("complaint_id"):
        return

    st.divider()

    with st.container(border=True):
        st.subheader("Review customer email")
        st.caption("Confirm the recipient and content before sending.")

        st.text_input(
            "Recipient",
            value=generated_complaint.get(
                "customer_email",
                complaint.get("customer_email", ""),
            ),
            disabled=True,
            key=f"recipient_{complaint['complaint_id']}",
        )
        st.text_input(
            "Subject",
            value=generated_email.get("subject", ""),
            disabled=True,
            key=f"subject_{complaint['complaint_id']}",
        )
        st.text_area(
            "Email body",
            value=generated_email.get("email_body", ""),
            height=300,
            disabled=True,
            key=f"email_body_{complaint['complaint_id']}",
        )

        confirmed = st.checkbox(
            "I reviewed the recipient, subject, and message.",
            key=f"email_confirmation_{complaint['complaint_id']}",
        )
        send_clicked = st.button(
            "Send approved email",
            type="primary",
            use_container_width=True,
            disabled=not confirmed,
            key=f"send_email_{complaint['complaint_id']}",
        )

    if send_clicked:
        token = get_access_token()
        email_id = generated_email.get("id")

        if not token:
            st.error("Your login session is unavailable.")
            return

        if not email_id:
            st.error("The generated email ID is missing.")
            return

        try:
            with st.spinner("Sending the email securely..."):
                send_response = api.send_complaint_email(
                    token=token,
                    complaint_id=int(complaint["complaint_id"]),
                    email_id=int(email_id),
                )

            st.success(
                f"{send_response.get('message', 'Email sent.')} "
                f"Recipient: {send_response.get('recipient', 'Unknown')}"
            )
            clear_generated_email()
        except APIClientError as error:
            display_api_error(error)


apply_custom_styles()
render_sidebar()
render_top_navigation()

selected_page = get_current_page()

if selected_page == "Home":
    render_home_page()
elif selected_page == "Login":
    render_login_page()
elif selected_page == "Register":
    render_register_page()
elif selected_page == "Submit Complaint":
    render_submit_complaint_page()
elif selected_page == "Manager Workspace":
    render_manager_workspace()
else:
    set_current_page("Home")
    st.rerun()