import logging
from email.message import EmailMessage
from smtplib import SMTP_SSL

from app.core.config import settings

logger = logging.getLogger("app.mail_sender")


def send_code(to_email: str, code: str) -> None:
    html = f"""<!doctype html>
                <html><body style="margin:0;background:#f6f9fc;">
                <div style="max-width:560px;margin:24px auto;padding:24px;border:1px 
                solid #e6e9ef;border-radius:12px;background:#fff;">
                    <h1 style="margin:0 0 8px 0;font:600 20px 'Segoe UI',Arial,sans-serif;
                    color:#0f172a;">
                    Verify your email
                    </h1>
                    <p style="margin:0 0 16px 0;font:400 14px 'Segoe UI',Arial,sans-serif;
                    color:#334155;">
                    Use the code below to finish signing in. It will expire in <b>5 minutes</b>.
                    </p>
                    <div style="display:inline-block;padding:12px 18px;border:1px solid #e2e8f0;
                    border-radius:12px;background:#f8fafc;
                                font:700 24px 'Segoe UI',Arial,sans-serif;
                                letter-spacing:2px;color:#0f172a;">
                    {code}
                    </div>
                    <p style="margin:16px 0 0 0;font:400 12px 'Segoe UI',Arial,sans-serif;
                    color:#64748b;">
                    If you didn’t request this code, ignore this email.
                    </p>
                </div>
                </body></html>"""

    message = EmailMessage()
    message["Subject"] = "Code verification"
    message["From"] = "Swaga Company"
    message["To"] = to_email
    message.set_content(html)
    message.add_alternative(html, subtype="html")

    with SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(settings.smtp_login, settings.smtp_password)
        server.send_message(message)
    logger.info(f"Email sender sent verification code to user: {to_email}")
    return
