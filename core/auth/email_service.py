import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_USE_TLS, FROM_EMAIL, BASE_URL

logger = logging.getLogger(__name__)

class EmailService:
    def send_magic_link(self, email: str, token: str) -> bool:
        if not SMTP_USER or not SMTP_PASSWORD:
            logger.warning(f"[AUTH] SMTP not configured. Magic link for {email}: {BASE_URL}/api/v1/auth/verify?token={token}")
            print(f"\n{'='*80}")
            print(f"🔑 MAGIC LINK for {email}:")
            print(f"{BASE_URL}/api/v1/auth/verify?token={token}")
            print(f"{'='*80}\n")
            return True

        login_url = f"{BASE_URL}/api/v1/auth/verify?token={token}"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #10a37f;">Welcome to Codely AI</h2>
            <p>Click the button below to sign in to your account:</p>
            <a href="{login_url}"
               style="display: inline-block; padding: 12px 24px; background-color: #10a37f; color: white;
                      text-decoration: none; border-radius: 5px; margin: 20px 0;">
                Sign In to Codely
            </a>
            <p style="color: #666; font-size: 14px;">
                If the button doesn't work, copy and paste this link:<br>
                <a href="{login_url}">{login_url}</a>
            </p>
            <p style="color: #999; font-size: 12px; margin-top: 30px;">
                This link expires in 24 hours. If you didn't request this, you can safely ignore this email.
            </p>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Sign in to Codely AI"
        msg["From"] = FROM_EMAIL or SMTP_USER
        msg["To"] = email
        msg.attach(MIMEText(html_body, "html"))

        try:
            if SMTP_USE_TLS:
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
                server.starttls()
            else:
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)

            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(msg["From"], email, msg.as_string())
            server.quit()

            logger.info(f"[AUTH] Magic link email sent to {email}")
            return True

        except Exception as e:
            logger.error(f"[AUTH] Failed to send email to {email}: {type(e).__name__}: {e}")
            return False
