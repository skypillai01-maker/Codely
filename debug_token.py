import os, sys
os.environ["CODELY_AUTH_SECRET_KEY"] = "test-fixed-key-12345"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.auth.database import init_db, get_db
from core.auth.token_service import TokenService

init_db()

svc = TokenService()
token = svc.generate_magic_token("debug@test.com")
print(f"Generated token: {token[:60]}...")

with get_db() as conn:
    rows = conn.execute("SELECT * FROM magic_tokens").fetchall()
    print(f"Tokens in DB: {len(rows)}")
    for r in rows:
        print(f"  token={r['token'][:60]}..., used={r['used']}")

user = svc.verify_magic_token(token)
print(f"Verify result: {user}")
