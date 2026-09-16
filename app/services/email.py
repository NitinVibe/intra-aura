from email.message import EmailMessage
import smtplib

from app.config.settings import settings
from app.content.store import load_content


def smtp_configured() -> bool:
    return all(
        [
            settings.SMTP_HOST,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM_EMAIL,
        ]
    )


def send_auth_otp(email: str, otp: str, purpose: str) -> None:
    if not smtp_configured():
        raise RuntimeError("Customer OTP email service is not configured.")

    brand = str(load_content().get("site", {}).get("name", "Intra Aura")).strip() or "Intra Aura"

    if purpose == "signup":
        subject = f"Verify your {brand} account"
        heading = "Verify your account"
        action = f"complete your {brand} signup"
    else:
        subject = f"Reset your {brand} password"
        heading = "Reset your password"
        action = f"reset your {brand} password"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.set_content(
        f"{heading}\\n\\n"
        f"Your one-time verification code is: {otp}\\n\\n"
        f"Use this code to {action}. The code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\\n"
        "If you did not request this, you can safely ignore this email.\\n\\n"
        f"{brand}"
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        smtp.send_message(message)
