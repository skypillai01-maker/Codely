import os
import sys
import time
import json
import uuid
import threading
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Form, Depends
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

current_dir = os.path.dirname(os.path.abspath(__file__))
core_dir = os.path.dirname(current_dir)
project_dir = os.path.dirname(core_dir)
for p in [core_dir, project_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from core.config import (
    API_HOST, API_PORT, OLLAMA_BASE_URL, CHAT_MODEL, EMBEDDING_MODEL,
    MAX_WORKERS, RATE_LIMIT_CHAT, RATE_LIMIT_INGEST,
    CHAT_TIMEOUT, AUTH_SESSION_EXPIRY, BASE_URL,
    BATCH_EMBED_SIZE, MODEL_CONFIG_PATH, MEMORY_STORAGE_PATH,
    MAX_TASKS_PER_USER
)
from core.auth.database import init_db, get_db, create_session, validate_session, revoke_session, cleanup_expired_sessions
from core.auth.token_service import TokenService
from core.auth.email_service import EmailService
from core.auth.middleware import get_current_user, get_current_user_optional
from core.auth.models import MagicLinkRequest, VerifyTokenRequest
from core.llm.adapters.ollama import OllamaAdapter
from core.memory.vector_store import FAISSVectorStore
from core.rag.engine import RAGEngine
from core.task_engine.manager import TaskManager, TaskStatus
from core.modules.registry import registry

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DEBUG = os.getenv("CODELY_DEBUG", "").lower() in ("1", "true", "yes")

_ollama: Optional[OllamaAdapter] = None
_token_service: Optional[TokenService] = None
_email_service: Optional[EmailService] = None
_task_manager: Optional[TaskManager] = None
_memory_stores: Dict[str, FAISSVectorStore] = {}
_memory_stores_lock = threading.Lock()

rate_limit_lock = threading.Lock()
rate_limit_store: Dict[str, list] = {}
MAX_FILE_SIZE = 50 * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ollama, _token_service, _email_service, _task_manager
    init_db()
    os.makedirs(MEMORY_STORAGE_PATH, exist_ok=True)

    _ollama = OllamaAdapter(base_url=OLLAMA_BASE_URL, model=CHAT_MODEL)
    _token_service = TokenService()
    _email_service = EmailService()
    _task_manager = TaskManager(max_workers=MAX_WORKERS, storage_dir="storage/tasks")

    if _ollama.validate_connectivity():
        logger.info("Ollama connectivity OK")
    else:
        logger.warning("Ollama not reachable — chat will fail until it is")

    registry.discover_modules("modules")
    logger.info(f"Discovered modules: {[m['name'] for m in registry.list_modules()]}")

    yield


app = FastAPI(title="Codely AI", version="0.6.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers ──────────────────────────────────────────

@app.exception_handler(RuntimeError)
async def runtime_error_handler(request, exc):
    logger.error(f"Runtime error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(status_code=503, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if DEBUG:
        raise
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


# ── Dependencies ────────────────────────────────────────────────

def get_ollama():
    if _ollama is None:
        raise RuntimeError("Server not initialized")
    return _ollama


def get_token_service():
    if _token_service is None:
        raise RuntimeError("Server not initialized")
    return _token_service


def get_email_service():
    if _email_service is None:
        raise RuntimeError("Server not initialized")
    return _email_service


def get_task_manager():
    if _task_manager is None:
        raise RuntimeError("Server not initialized")
    return _task_manager


def check_rate_limit(user_id: str, endpoint: str, max_requests: int) -> bool:
    with rate_limit_lock:
        key = f"{user_id}:{endpoint}"
        now = time.time()
        if key not in rate_limit_store:
            rate_limit_store[key] = []
        rate_limit_store[key] = [t for t in rate_limit_store[key] if now - t < 60]
        if len(rate_limit_store[key]) >= max_requests:
            return False
        rate_limit_store[key].append(now)
        return True


def get_memory_store(user_id: str) -> FAISSVectorStore:
    with _memory_stores_lock:
        if user_id not in _memory_stores:
            _memory_stores[user_id] = FAISSVectorStore(
                embed_adapter=get_ollama(),
                base_path=MEMORY_STORAGE_PATH,
                user_id=user_id
            )
        return _memory_stores[user_id]


def get_rag_engine(user_id: str) -> RAGEngine:
    store = get_memory_store(user_id)
    return RAGEngine(llm=get_ollama(), memory=store)


def persist_model_config(config: dict):
    os.makedirs(os.path.dirname(MODEL_CONFIG_PATH), exist_ok=True)
    with open(MODEL_CONFIG_PATH, "w") as f:
        json.dump(config, f)


def load_model_config() -> dict:
    if os.path.exists(MODEL_CONFIG_PATH):
        with open(MODEL_CONFIG_PATH) as f:
            return json.load(f)
    return {"chat_model": CHAT_MODEL, "embedding_model": EMBEDDING_MODEL}


# ── Static files ──────────────────────────────────────────────

CLIENTS_WEB = os.path.join(project_dir, "clients", "web")


def _read_html(filename: str) -> str:
    path = os.path.join(CLIENTS_WEB, filename)
    if not os.path.exists(path):
        raise HTTPException(404, "Not found")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/")
async def serve_index():
    return HTMLResponse(_read_html("index.html"))


@app.get("/index.html")
async def serve_index_alt():
    return HTMLResponse(_read_html("index.html"))


# ── Auth endpoints ─────────────────────────────────────────────

@app.get("/api/v1/auth/request-login")
async def serve_login_page():
    return HTMLResponse(_read_html("login.html"))


@app.post("/api/v1/auth/request-login")
async def request_login(body: MagicLinkRequest):
    token = get_token_service().generate_magic_token(body.email)
    sent = get_email_service().send_magic_link(body.email, token)
    if not sent:
        raise HTTPException(500, "Failed to send magic link")
    dev_link = f"{BASE_URL}/api/v1/auth/verify?token={token}" if not os.getenv("CODELY_SMTP_USER") else None
    return {
        "message": "Magic link sent! Check your email (or console in dev mode).",
        "dev_link": dev_link
    }


@app.get("/api/v1/auth/verify")
async def verify_magic_link(token: str):
    user = get_token_service().verify_magic_token(token)
    if not user:
        return HTMLResponse("""
            <html><body style="background:#1a1a1a;color:#ececec;font-family:sans-serif;
            display:flex;align-items:center;justify-content:center;height:100vh;">
            <div style="text-align:center;">
            <h2 style="color:#e74c3c;">Invalid or expired link</h2>
            <a href="/api/v1/auth/request-login" style="color:#10a37f;">Request a new one</a>
            </div></body></html>
        """, status_code=400)
    expiry = (datetime.now(timezone.utc) + timedelta(seconds=AUTH_SESSION_EXPIRY)).isoformat()
    session_id = create_session(user["user_id"], expiry)
    return RedirectResponse(url=f"/?session_id={session_id}")


@app.post("/api/v1/auth/verify")
async def verify_magic_link_post(body: VerifyTokenRequest):
    user = get_token_service().verify_magic_token(body.token)
    if not user:
        raise HTTPException(400, "Invalid or expired token")
    expiry = (datetime.now(timezone.utc) + timedelta(seconds=AUTH_SESSION_EXPIRY)).isoformat()
    session_id = create_session(user["user_id"], expiry)
    return {"session_id": session_id, "user_id": user["user_id"], "email": user["email"]}


@app.get("/api/v1/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@app.post("/api/v1/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    revoke_session(current_user["session_id"])
    return {"message": "Logged out successfully"}


# ── Chat endpoints ─────────────────────────────────────────────

@app.post("/api/v1/chat")
async def chat(
    body: dict,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    context_id = body.get("context_id")
    prompt = body.get("prompt", "")
    mode = body.get("mode", "normal")

    if not context_id or not prompt:
        raise HTTPException(400, "context_id and prompt are required")
    if not check_rate_limit(user_id, "chat", RATE_LIMIT_CHAT):
        raise HTTPException(429, "Rate limit exceeded")

    rag = get_rag_engine(user_id)
    result = rag.generate_with_context(
        context_id=context_id,
        prompt=prompt,
        session_id=context_id,
        mode=mode
    )
    return {
        "response": result["response"],
        "tool_used": result.get("tool_used"),
        "tool_suggestion": result.get("tool_suggestion")
    }


@app.post("/api/v1/chat-with-files")
async def chat_with_files(
    request: Request,
    current_user: dict = Depends(get_current_user_optional),
):
    user_id = current_user["user_id"] if current_user else "anonymous"
    form = await request.form()
    context_id = form.get("context_id", str(uuid.uuid4()))
    prompt = form.get("prompt", "")
    save_to_memory = form.get("save_to_memory", "false").lower() == "true"
    mode = form.get("mode", "normal")
    urls_str = form.get("urls", "")
    execute_tool = form.get("execute_tool")

    if not check_rate_limit(user_id, "chat", RATE_LIMIT_CHAT):
        raise HTTPException(429, "Rate limit exceeded")

    store = get_memory_store(user_id)
    rag = get_rag_engine(user_id)
    attachments = {"files": [], "urls": [], "saved": False}
    saved_to_memory = False

    for field_name, field_value in form.items():
        if field_name == "files" and hasattr(field_value, "read"):
            content = await field_value.read()
            text = content.decode("utf-8", errors="ignore")
            combined = f"--- Content from {field_value.filename} ---\n{text}"
            store.add(context_id, combined)
            attachments["files"].append(field_value.filename)

    import requests as http_requests
    for url in [u.strip() for u in urls_str.split(",") if u.strip()]:
        try:
            resp = http_requests.get(url, timeout=15)
            text = resp.text
            store.add(context_id, f"--- Content from {url} ---\n{text}")
            attachments["urls"].append(url)
        except Exception as e:
            logger.warning(f"Failed to fetch URL {url}: {e}")

    if save_to_memory and (attachments["files"] or attachments["urls"]):
        saved_to_memory = True
        attachments["saved"] = True

    if prompt:
        result = rag.generate_with_context(
            context_id=context_id,
            prompt=prompt,
            session_id=context_id,
            mode=mode,
            execute_tool=execute_tool
        )
        return {
            "response": result["response"],
            "tool_used": result.get("tool_used"),
            "tool_suggestion": result.get("tool_suggestion"),
            "mode": mode,
            "attachments": attachments,
            "saved_to_memory": saved_to_memory
        }

    return {
        "response": "Files and URLs processed.",
        "tool_used": None,
        "tool_suggestion": None,
        "mode": mode,
        "attachments": attachments,
        "saved_to_memory": saved_to_memory
    }


# ── Memory endpoints ───────────────────────────────────────────

@app.post("/api/v1/memory/add")
async def add_memory(
    body: dict,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    context_id = body.get("context_id")
    text = body.get("text", "")
    metadata = body.get("metadata", {})

    if not context_id or not text:
        raise HTTPException(400, "context_id and text are required")

    store = get_memory_store(user_id)
    store.add(context_id, text, metadata)
    return {"status": "success", "message": "Memory added"}


@app.delete("/api/v1/memory/clear/{context_id}")
async def clear_memory(
    context_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    store = get_memory_store(user_id)
    store.clear(context_id)
    return {"status": "success", "message": f"Memory cleared for {context_id}"}


@app.post("/api/v1/memory/merge")
async def merge_memory(
    body: dict,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    target = body.get("target_context_id")
    sources = body.get("source_context_ids", [])

    if not target or not sources:
        raise HTTPException(400, "target_context_id and source_context_ids are required")

    store = get_memory_store(user_id)
    entries = store.merge(target, sources)
    return {"status": "success", "entries_merged": entries}


# ── Ingest endpoints ───────────────────────────────────────────

@app.post("/api/v1/ingest")
async def ingest_text(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    form = await request.form()
    context_id = form.get("context_id", user_id)
    text = form.get("text", "")

    if not text:
        raise HTTPException(400, "text is required")
    if not check_rate_limit(user_id, "ingest", RATE_LIMIT_INGEST):
        raise HTTPException(429, "Rate limit exceeded")
    if not get_task_manager().can_submit_task(user_id, MAX_TASKS_PER_USER):
        raise HTTPException(429, "Too many active tasks")

    store = get_memory_store(user_id)

    def ingest_task(txt, uid):
        store.add(context_id, txt, progress_callback=lambda p, m: None)
        return {"status": "success", "chunks": 1}

    task_id = get_task_manager().submit(ingest_task, text, user_id)
    return {"task_id": task_id, "status": "pending"}


@app.post("/api/v1/ingest/file")
async def ingest_file(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    form = await request.form()
    context_id = form.get("context_id", user_id)

    file_field = None
    for key, val in form.items():
        if key == "file" and hasattr(val, "read"):
            file_field = val
            break

    if not file_field:
        raise HTTPException(400, "file is required")
    if not check_rate_limit(user_id, "ingest", RATE_LIMIT_INGEST):
        raise HTTPException(429, "Rate limit exceeded")
    if not get_task_manager().can_submit_task(user_id, MAX_TASKS_PER_USER):
        raise HTTPException(429, "Too many active tasks")

    content = await file_field.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, f"File too large. Max size: {MAX_FILE_SIZE // 1024 // 1024}MB")

    filename = getattr(file_field, "filename", "unknown")

    def file_ingest_task(content_bytes, fname):
        store = get_memory_store(user_id)
        text = content_bytes.decode("utf-8", errors="ignore")
        store.add(context_id, text, progress_callback=lambda p, m: None)
        return {"status": "success", "filename": fname}

    task_id = get_task_manager().submit(file_ingest_task, content, filename)
    return {"task_id": task_id, "status": "pending"}


# ── Task endpoints ─────────────────────────────────────────────

@app.get("/api/v1/tasks/{task_id}")
async def get_task(task_id: str):
    task = get_task_manager().get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@app.get("/api/v1/tasks/{task_id}/stream")
async def stream_task(task_id: str):
    task = get_task_manager().get_task(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    def generate():
        last_progress = -1
        while True:
            task = get_task_manager().get_task(task_id)
            if not task:
                break
            if task["progress"] != last_progress:
                last_progress = task["progress"]
                yield f"data: {json.dumps(task)}\n\n"
            if task["status"] in ["completed", "failed", "cancelled"]:
                yield f"data: {json.dumps(task)}\n\n"
                break
            time.sleep(0.5)

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/v1/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    if get_task_manager().cancel_task(task_id):
        return {"status": "cancelled"}
    raise HTTPException(404, "Task not found")


@app.get("/api/v1/tasks")
async def list_tasks(user_id: Optional[str] = None):
    tasks = get_task_manager().list_tasks()
    if user_id:
        tasks = [t for t in tasks if user_id in str(t)]
    return {"tasks": tasks}


# ── Thread endpoints ───────────────────────────────────────────

@app.get("/api/v1/threads")
async def list_threads(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    store = get_memory_store(user_id)
    contexts = store.list_contexts()
    return {"threads": [{"id": c} for c in contexts], "count": len(contexts)}


@app.get("/api/v1/threads/{context_id}/stats")
async def get_thread_stats(
    context_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    store = get_memory_store(user_id)
    try:
        stats = store.get_stats(context_id)
        return stats
    except Exception:
        raise HTTPException(404, "Thread not found")


@app.delete("/api/v1/threads/{context_id}")
async def delete_thread(
    context_id: str,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]
    store = get_memory_store(user_id)
    store.clear(context_id)
    return {"status": "success", "message": f"Thread {context_id} deleted"}


# ── Module endpoints ───────────────────────────────────────────

@app.get("/api/v1/modules")
async def list_modules():
    return {"modules": registry.list_modules()}


@app.post("/api/v1/modules/execute/{module_name}")
async def execute_module(
    module_name: str,
    body: dict,
    current_user: dict = Depends(get_current_user)
):
    module = registry.get_module(module_name)
    if not module:
        raise HTTPException(404, f"Module '{module_name}' not found")
    try:
        result = module.execute(body.get("params", body))
        return result
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Model endpoints ───────────────────────────────────────────

@app.get("/api/v1/model")
async def get_current_model():
    config = load_model_config()
    return config


@app.post("/api/v1/model/switch")
async def switch_model(body: dict):
    model_type = body.get("model_type")
    model_name = body.get("model_name")
    if not model_type or not model_name:
        raise HTTPException(400, "model_type and model_name are required")

    config = load_model_config()
    config[model_type] = model_name
    persist_model_config(config)

    global _ollama
    if model_type == "chat_model":
        _ollama = OllamaAdapter(base_url=OLLAMA_BASE_URL, model=model_name)
    return {"message": f"Model {model_type} switched to {model_name}", "config": config}


# ── Tool endpoints (Phase 3) ──────────────────────────────────

@app.get("/api/v1/tools")
async def list_tools():
    return {
        "tools": [
            {"name": "FileWrite", "description": "Write or update files within workspace", "requires_permission": True},
            {"name": "SandboxExec", "description": "Execute commands in sandboxed environment", "requires_permission": True},
            {"name": "TestGen", "description": "Generate unit tests for code", "requires_permission": False},
        ]
    }


@app.post("/api/v1/tools/write-file")
async def write_file_tool(
    body: dict,
    current_user: dict = Depends(get_current_user)
):
    from modules.file_write import FileWriteModule
    module = FileWriteModule()
    params = {
        "file_path": body.get("file_path", ""),
        "content": body.get("content", ""),
        "mode": body.get("mode", "write"),
        "workspace_root": os.path.dirname(project_dir)
    }
    return module.execute(params)


@app.post("/api/v1/tools/exec-command")
async def exec_command_tool(
    body: dict,
    current_user: dict = Depends(get_current_user)
):
    from modules.sandbox_exec import SandboxExecModule
    module = SandboxExecModule()
    params = {
        "command": body.get("command", ""),
        "timeout": body.get("timeout", 30),
        "workdir": body.get("workdir", os.getcwd())
    }
    return module.execute(params)


@app.post("/api/v1/tools/generate-tests")
async def generate_tests_tool(
    body: dict,
    current_user: dict = Depends(get_current_user)
):
    from modules.test_gen import TestGenModule
    module = TestGenModule()
    params = {
        "code": body.get("code", ""),
        "file_path": body.get("file_path", ""),
        "framework": body.get("framework", "pytest"),
        "test_style": body.get("test_style", "comprehensive")
    }
    return module.execute(params)


# ── Root health ────────────────────────────────────────────────

@app.get("/health")
async def health():
    ok = get_ollama().validate_connectivity() if _ollama else False
    return {"status": "ok" if ok else "degraded", "service": "Codely AI", "ollama": ok}


if __name__ == "__main__":
    uvicorn.run("core.api.main:app", host=API_HOST, port=API_PORT, reload=False)
