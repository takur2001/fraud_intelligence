import os
import smtplib
import ssl
from email.message import EmailMessage

from dotenv import load_dotenv


load_dotenv()


class EmailSendingError(Exception):
    """
    Raised when an email cannot be sent through SMTP.
    """

    pass


def get_required_environment_variable(
    variable_name: str,
) -> str:
    """
    Read a required environment variable.

    Raises EmailSendingError when the value is missing.
    """

    value = os.getenv(variable_name)

    if not value or not value.strip():
        raise EmailSendingError(
            f"{variable_name} is not configured."
        )

    return value.strip()


def send_customer_email(
    *,
    recipient_email: str,
    subject: str,
    email_body: str,
) -> None:
    """
    Send a plain-text customer email using SMTP.

    SMTP credentials are loaded from environment variables.
    The SMTP password is never placed inside the source code.
    """

    smtp_host = get_required_environment_variable(
        "SMTP_HOST"
    )

    smtp_username = get_required_environment_variable(
        "SMTP_USERNAME"
    )

    smtp_password = get_required_environment_variable(
        "SMTP_PASSWORD"
    )

    smtp_from_email = (
        os.getenv("SMTP_FROM_EMAIL", smtp_username)
        .strip()
    )

    smtp_from_name = (
        os.getenv(
            "SMTP_FROM_NAME",
            "Customer Support Team",
        )
        .strip()
    )

    try:
        smtp_port = int(
            os.getenv("SMTP_PORT", "587")
        )

    except ValueError as exc:
        raise EmailSendingError(
            "SMTP_PORT must be a valid integer."
        ) from exc

    use_tls = (
        os.getenv("SMTP_USE_TLS", "true")
        .strip()
        .lower()
        in {"true", "1", "yes"}
    )

    cleaned_recipient = recipient_email.strip().lower()
    cleaned_subject = subject.strip()
    cleaned_body = email_body.strip()

    if not cleaned_recipient:
        raise EmailSendingError(
            "The recipient email address is missing."
        )

    if not cleaned_subject:
        raise EmailSendingError(
            "The email subject is missing."
        )

    if not cleaned_body:
        raise EmailSendingError(
            "The email body is missing."
        )

    message = EmailMessage()

    message["From"] = (
        f"{smtp_from_name} <{smtp_from_email}>"
    )

    message["To"] = cleaned_recipient
    message["Subject"] = cleaned_subject

    message.set_content(cleaned_body)

    ssl_context = ssl.create_default_context()

    try:
        with smtplib.SMTP(
            host=smtp_host,
            port=smtp_port,
            timeout=30,
        ) as smtp_server:
            smtp_server.ehlo()

            if use_tls:
                smtp_server.starttls(
                    context=ssl_context
                )

                smtp_server.ehlo()

            smtp_server.login(
                smtp_username,
                smtp_password,
            )

            smtp_server.send_message(message)

    except smtplib.SMTPAuthenticationError as exc:
        raise EmailSendingError(
            "SMTP authentication failed. Check the SMTP "
            "username and app password."
        ) from exc

    except smtplib.SMTPRecipientsRefused as exc:
        raise EmailSendingError(
            "The recipient email address was refused "
            "by the SMTP server."
        ) from exc

    except smtplib.SMTPSenderRefused as exc:
        raise EmailSendingError(
            "The sender email address was refused "
            "by the SMTP server."
        ) from exc

    except smtplib.SMTPException as exc:
        raise EmailSendingError(
            f"The SMTP server could not send the email: {exc}"
        ) from exc

    except OSError as exc:
        raise EmailSendingError(
            "Could not connect to the SMTP server. "
            "Check the SMTP host, port, and internet connection."
        ) from exc