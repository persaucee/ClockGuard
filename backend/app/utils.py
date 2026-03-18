import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_payroll_email(
    employee_email: str,
    total_pay: float,
    hours: float,
    sender_email: str
) -> dict:
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
        msg["From"] = sender_email
        msg["To"] = employee_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, GMAIL_APP_PASSWORD)
            server.sendmail(sender_email, employee_email, msg.as_string())

        return {"success": True, "message": f"Email sent to {employee_email}"}

    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Authentication failed. Check your email/app password."}
    except smtplib.SMTPException as e:
        return {"success": False, "message": f"SMTP error: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}