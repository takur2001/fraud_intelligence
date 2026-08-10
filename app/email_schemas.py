from pydantic import BaseModel, EmailStr


class EmailSendResponse(BaseModel):
    """
    Response returned after a stored customer email is sent.
    """

    message: str
    complaint_id: int
    email_id: int
    recipient: EmailStr
    subject: str