import logging
from datetime import datetime, timedelta, timezone
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from core.config import AUTH_SECRET_KEY, AUTH_TOKEN_EXPIRY
from core.auth.database import get_db, create_user, get_user_by_email

logger = logging.getLogger(__name__)

class TokenService:
    def __init__(self):
        self.serializer = URLSafeTimedSerializer(AUTH_SECRET_KEY)
        self.max_age = AUTH_TOKEN_EXPIRY

    def generate_magic_token(self, email: str) -> str:
        payload = {"email": email.lower(), "ts": datetime.now(timezone.utc).isoformat()}
        token = self.serializer.dumps(payload)

        now = datetime.now(timezone.utc).isoformat()
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=self.max_age)).isoformat()

        with get_db() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO magic_tokens (token, email, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (token, email.lower(), now, expires_at)
            )

        logger.info(f"[AUTH] Generated magic token for {email}")
        return token

    def verify_magic_token(self, token: str) -> dict | None:
        try:
            payload = self.serializer.loads(token, max_age=self.max_age)
        except SignatureExpired:
            logger.warning(f"[AUTH] Expired magic token used")
            return None
        except BadSignature:
            logger.warning(f"[AUTH] Invalid magic token signature")
            return None

        email = payload.get("email")
        if not email:
            return None

        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM magic_tokens WHERE token = ? AND used = 0",
                (token,)
            ).fetchone()

            if not row:
                logger.warning(f"[AUTH] Magic token not found or already used")
                return None

            conn.execute("UPDATE magic_tokens SET used = 1 WHERE token = ?", (token,))

        user = get_user_by_email(email)
        if not user:
            user = create_user(email)

        return user


