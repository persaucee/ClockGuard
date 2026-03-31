import os
from typing import Optional
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

load_dotenv()
GMAIL_APP_EMAIL = os.getenv("GMAIL_APP_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

import logging

logger = logging.getLogger(__name__)

def send_payroll_email(
    employee_email: str,
    total_pay: float,
    hours: float
) -> None:
    try:
        subject = "Your Pay Period Summary"
        body = (
            f"Hello,\n\n"
            f"The pay period has ended. Here is your summary:\n\n"
            f"  Hours Worked: {hours}\n"
            f"  Total Earnings: ${total_pay:.2f}\n\n"
            f"Thank you."
        )

        msg = MIMEMultipart()
        msg["From"] = GMAIL_APP_EMAIL
        msg["To"] = employee_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10) as server:
            server.login(GMAIL_APP_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_APP_EMAIL, employee_email, msg.as_string())

        logger.info(f"Payroll email sent to {employee_email}")

    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed — check credentials")

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending email to {employee_email}: {e}")

    except Exception as e:
        logger.exception(f"Unexpected error sending email to {employee_email}")

def create_response(
    success: bool,
    data = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> JSONResponse:
    from app.schemas import APIResponse
    
    response = APIResponse(
        success=success,
        data=data,
        message=message,
        status_code=status_code
    )
    
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(response)
    )