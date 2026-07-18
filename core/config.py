import os
import secrets
from dotenv import load_dotenv

load_dotenv()

PLATFORM_NAME = "Codely AI"
VERSION = "0.6.1"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("CODELY_CHAT_MODEL", "llama3")
EMBEDDING_MODEL = os.getenv("CODELY_EMBEDDING_MODEL", "nomic-embed-text")

API_HOST = os.getenv("CODELY_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("CODELY_API_PORT", "8889"))

BASE_STORAGE_PATH = "storage"
MEMORY_STORAGE_PATH = os.path.join(BASE_STORAGE_PATH, "memory")
TASK_STORAGE_PATH = os.path.join(BASE_STORAGE_PATH, "tasks")
MODEL_CONFIG_PATH = os.path.join(BASE_STORAGE_PATH, "model.json")
TEMP_STORAGE_PATH = os.path.join(BASE_STORAGE_PATH, "temp")
AUTH_DB_PATH = os.path.join(BASE_STORAGE_PATH, "auth.db")

AUTH_SECRET_KEY = os.getenv("CODELY_AUTH_SECRET_KEY", secrets.token_hex(32))
AUTH_TOKEN_EXPIRY = int(os.getenv("CODELY_AUTH_TOKEN_EXPIRY", "86400"))
AUTH_SESSION_EXPIRY = int(os.getenv("CODELY_AUTH_SESSION_EXPIRY", "604800"))

SMTP_HOST = os.getenv("CODELY_SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("CODELY_SMTP_PORT", "587"))
SMTP_USER = os.getenv("CODELY_SMTP_USER", "")
SMTP_PASSWORD = os.getenv("CODELY_SMTP_PASSWORD", "")
SMTP_USE_TLS = os.getenv("CODELY_SMTP_USE_TLS", "true").lower() == "true"
FROM_EMAIL = os.getenv("CODELY_FROM_EMAIL", "")

BASE_URL = os.getenv("CODELY_BASE_URL", "http://localhost:8889")

WORKSPACE_ROOT = os.getenv("CODELY_WORKSPACE_ROOT", os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "..")))
MAX_FILE_SIZE = int(os.getenv("CODELY_MAX_FILE_SIZE", "1048576"))
COMMAND_TIMEOUT = int(os.getenv("CODELY_COMMAND_TIMEOUT", "30"))
MAX_WORKERS = int(os.getenv("CODELY_MAX_WORKERS", "4"))
CHAT_TIMEOUT = int(os.getenv("CODELY_CHAT_TIMEOUT", "300"))
EMBED_TIMEOUT = int(os.getenv("CODELY_EMBED_TIMEOUT", "60"))
MAX_TASKS_PER_USER = int(os.getenv("CODELY_MAX_TASKS_PER_USER", "2"))
RATE_LIMIT_CHAT = int(os.getenv("CODELY_RATE_LIMIT_CHAT", "60"))
RATE_LIMIT_INGEST = int(os.getenv("CODELY_RATE_LIMIT_INGEST", "10"))
BATCH_EMBED_SIZE = int(os.getenv("CODELY_BATCH_EMBED_SIZE", "10"))
