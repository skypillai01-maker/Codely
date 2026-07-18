# Codely AI Platform - Development Guide

> **Version**: 0.7.0 | **Last Updated**: 2026-07-18
> **Status**: Production Ready | **Enforcement**: STRICT - VIOLATIONS ARE HARD STOP

---

## 🚨 READ THIS FIRST

This is the **entry point for AI/developers**. Before making ANY changes:

1. Read this file
2. Read `.docs/GUIDELINES.md`
3. Read `.docs/RULES_CHECKLIST.md`

**Every mistake becomes a permanent rule. Fix once, document, never repeat.**

---

## 1. Quick Start

### Prerequisites

```bash
# Install Ollama
# Download: https://ollama.com/download

# Pull models
ollama pull qwen2.5-coder

# Configure
cp .env.example .env
```

### Quick Start (recommended)

```bash
python3 run.py
```

This single command creates a virtual environment, installs dependencies from `requirements.txt`, kills any existing process on port 8889, and starts the server.

### Manual Start

```bash
# Create venv & install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Start server
python core/api/main.py
```

### Verify

```bash
# Health check
curl http://localhost:8889/health

# Auth: get a session
# Visit http://localhost:8889/ in a browser, login, then use session_id:

# Chat test
curl -X POST http://localhost:8889/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <session_id>" \
  -d '{"context_id": "test", "prompt": "Hello"}'
```

---

## 2. Project Overview

**Codely** = Local-first AI platform with RAG memory, multi-modal ingestion, and ChatGPT-style thread isolation.

### Key Features

| Feature | Description |
|---------|-------------|
| **Thread Isolation** | Each conversation completely separate |
| **RAG Memory** | FAISS vector store per thread, scoped to user |
| **Multi-Modal** | PDF, DOCX, XLSX, PPTX, Images, URLs |
| **Local LLM** | Ollama only (no external APIs) |
| **Magic Link Auth** | Passwordless login via email or console link |

---

## 3. Auth Flow

Codely uses passwordless **magic link** authentication:

```
User visits / → redirected to login page (login.html)
         │
         ▼
User enters email → magic link sent
         │            (dev link printed to console if SMTP not configured)
         ▼
User clicks link → redirected to /?session_id=xxx
         │
         ▼
API call → Authorization: Bearer <session_id>
```

| Step | Endpoint | Description |
|------|----------|-------------|
| 1 | `GET /api/v1/auth/request-login` | Serves login page |
| 2 | `POST /api/v1/auth/request-login` | Sends magic link email (or prints to console) |
| 3 | `GET /api/v1/auth/verify?token=xxx` | Verifies token, creates session, redirects |
| 4 | `POST /api/v1/auth/verify` | Same as above but returns JSON |
| 5 | `GET /api/v1/auth/me` | Returns current user info |
| 6 | `POST /api/v1/auth/logout` | Revokes session |

All subsequent API calls use:

```
Authorization: Bearer <session_id>
```

The `session_id` is obtained after magic link verification. Protected endpoints use `current_user = Depends(get_current_user)` middleware which validates the Bearer token and returns `{user_id, email, display_name, session_id}`.

---

## 4. 🚨 CRITICAL RULES

### Rule 1: NO SILENT EXCEPTIONS

> **Created from: Thread contamination bug (2026-04-12)**
>
> `except Exception: pass` hid errors that caused thread data mixing.

```python
# ❌ FORBIDDEN
try:
    result = operation()
except Exception:
    pass

# ✅ REQUIRED
try:
    result = operation()
except Exception as e:
    logger.error(f"Operation failed: {type(e).__name__}: {e}")
```

### Rule 2: THREAD ISOLATION MANDATORY

Every conversation is completely separate. No cross-talk. Threads are scoped per user under `storage/memory/{user_id}/{thread_id}/`.

```python
# ✅ REQUIRED
memory.add(context_id, text)
llm.generate(prompt, session_id=context_id)
```

### Rule 3: LOG ALL ERRORS

All error paths MUST log with context.

```python
logger.error(f"Failed for context_id={context_id}: {e}")
logger.warning(f"Empty embedding, text_length={len(text)}")
logger.info(f"Added entry to context_id={context_id}")
```

### Rule 4: NO HARDCODED VALUES

All config from `core/config.py`.

```python
# ❌ FORBIDDEN
MODEL = "hardcoded-model"
URL = "http://localhost:11434"

# ✅ REQUIRED
from core.config import CHAT_MODEL, OLLAMA_BASE_URL
```

---

## 5. Architecture

### Directory Structure

```
Codely/
├── core/                   # Main package
│   ├── api/main.py         # FastAPI app (~708 lines)
│   ├── config.py           # Configuration (46 lines)
│   ├── auth/               # Authentication (magic links, sessions)
│   │   ├── database.py
│   │   ├── token_service.py
│   │   ├── email_service.py
│   │   ├── middleware.py
│   │   └── models.py
│   ├── llm/
│   │   ├── base.py         # Abstract LLM interface
│   │   └── adapters/ollama.py  # Ollama adapter
│   ├── memory/
│   │   ├── base.py         # Abstract memory interface
│   │   └── vector_store.py # FAISS implementation (per-user scope)
│   ├── rag/engine.py       # RAG processing
│   ├── task_engine/manager.py  # Task manager
│   └── modules/            # Plugin registry
├── modules/                # Discoverable plugins
│   ├── search_web/         # DuckDuckGo module
│   ├── file_write/         # File write tool
│   ├── sandbox_exec/       # Command execution tool
│   └── test_gen/           # Test generation tool
├── clients/
│   ├── web/index.html      # ChatGPT-style Web UI
│   ├── cli/codely_cli.py   # CLI tool
│   └── python_sdk/codely.py # Python SDK
├── storage/                # Runtime data (gitignored)
│   ├── memory/{user_id}/{thread_id}/  # FAISS per-thread
│   ├── tasks/
│   ├── temp/
│   ├── auth.db
│   └── model.json
├── .docs/                  # 9 documentation files
├── run.py                  # One-command launcher
├── requirements.txt        # Python dependencies
└── .env                    # Configuration (gitignored)
```

### Data Flow

```
User Request (Auth: Bearer <session_id>)
     │
     ▼
API Validation (user_id from session, context_id required)
     │
     ▼
RAG Engine ──→ Memory Search (user_id / context_id)
     │
     ▼
Tool Detection ──→ Module Registry
     │
     ▼
LLM Generate (session_id=context_id)
     │
     ▼
Response
```

### Thread Isolation

```
User A ──> storage/memory/user_a/thread_1/
User A ──> storage/memory/user_a/thread_2/
User B ──> storage/memory/user_b/thread_1/

Each thread is completely isolated within user scope.
```

---

## 6. Code Standards

### Type Hints (REQUIRED)

```python
def generate(self, prompt: str, session_id: str = None) -> str:
    pass
```

### Logging (REQUIRED)

```python
import logging
logger = logging.getLogger(__name__)

# Prefix with component
logger.info(f"[API] Chat request for context_id={context_id}")
logger.error(f"[RAG] Search failed: {e}")
```

### Exception Handling (REQUIRED)

```python
# ✅ CORRECT
try:
    result = operation()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except Exception as e:
    logger.error(f"Unexpected error: {type(e).__name__}: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Imports (REQUIRED)

```python
# Absolute imports for core/
from core.llm.base import BaseLLM
from core.config import API_PORT
```

---

## 7. API Reference

### Auth

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/auth/request-login` | Login page | No |
| POST | `/api/v1/auth/request-login` | Send magic link | No |
| GET | `/api/v1/auth/verify?token=xxx` | Verify token, redirect to `/` | No |
| POST | `/api/v1/auth/verify` | Verify token, return JSON | No |
| GET | `/api/v1/auth/me` | Current user info | Yes |
| POST | `/api/v1/auth/logout` | Revoke session | Yes |

### Chat

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/chat` | Basic chat with RAG context | Yes |
| POST | `/api/v1/chat-with-files` | Chat with file attachments | Optional |

#### Basic Chat
```
POST /api/v1/chat
Authorization: Bearer <session_id>
{
  "context_id": "thread_123",
  "prompt": "Hello"
}
```

#### Chat with Files
```
POST /api/v1/chat-with-files
Authorization: Bearer <session_id>
context_id: thread_123
prompt: Explain this
files: [uploaded files]
urls: https://example.com
save_to_memory: true
```

### Thread Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/threads` | List threads for current user | Yes |
| GET | `/api/v1/threads/{id}/stats` | Thread statistics | Yes |
| GET | `/api/v1/threads/{id}/messages` | Thread message history | Yes |
| DELETE | `/api/v1/threads/{id}` | Delete thread | Yes |

### Memory

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/memory/add` | Add to memory (scoped to user) | Yes |
| POST | `/api/v1/memory/merge` | Merge threads | Yes |
| DELETE | `/api/v1/memory/clear/{id}` | Clear thread memory | Yes |

### Ingest

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/ingest` | Ingest text for RAG | Yes |
| POST | `/api/v1/ingest/file` | Ingest files (PDF, DOCX, etc.) | Yes |

### Tasks

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/tasks` | List all tasks | No |
| GET | `/api/v1/tasks/{id}` | Get task status | No |
| GET | `/api/v1/tasks/{id}/stream` | Stream task logs (SSE) | No |
| POST | `/api/v1/tasks/{id}/cancel` | Cancel running task | No |

### Model Management

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/model` | Get current model config | No |
| POST | `/api/v1/model/switch` | Switch chat/embedding model | No |

### Tools (Phase 3)

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/tools` | List all tools with permissions | No |
| POST | `/api/v1/tools/write-file` | Write to file (workspace-confined) | Yes |
| POST | `/api/v1/tools/exec-command` | Execute sandboxed command | Yes |
| POST | `/api/v1/tools/generate-tests` | Generate unit tests | Yes |

### Modules

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/v1/modules` | List discovered modules | No |
| POST | `/api/v1/modules/execute/{name}` | Execute a module | Yes |

### System

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check (Ollama status) | No |

---

## 8. Testing Guide

### Auth Flow Test

```bash
# 1. Request magic link (dev mode prints link to console)
curl -X POST http://localhost:8889/api/v1/auth/request-login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
# → dev_link printed in console

# 2. Verify the token (gives session_id)
curl "http://localhost:8889/api/v1/auth/verify?token=<token_from_dev_link>"
# → Redirects to /?session_id=xxx

# 3. Check current user
curl http://localhost:8889/api/v1/auth/me \
  -H "Authorization: Bearer <session_id>"
```

### Thread Isolation Test (MANDATORY)

```bash
# Get a session_id first via auth flow
SESSION="your_session_id_here"

# 1. Add memory to Thread A
curl -X POST http://localhost:8889/api/v1/memory/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION" \
  -d '{"context_id": "thread_a", "text": "My favorite color is blue"}'

# 2. Add memory to Thread B
curl -X POST http://localhost:8889/api/v1/memory/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION" \
  -d '{"context_id": "thread_b", "text": "My favorite color is red"}'

# 3. Verify storage directories exist (scoped by user)
ls storage/memory/{user_id}/thread_a/  # Should show index.faiss + metadata.pkl
ls storage/memory/{user_id}/thread_b/  # Should show index.faiss + metadata.pkl

# 4. Chat in Thread A - should reference "blue"
curl -X POST http://localhost:8889/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION" \
  -d '{"context_id": "thread_a", "prompt": "What is my favorite color?"}'

# 5. Chat in Thread B - should reference "red"
curl -X POST http://localhost:8889/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION" \
  -d '{"context_id": "thread_b", "prompt": "What is my favorite color?"}'
```

### Fetch Thread Messages

```bash
SESSION="your_session_id_here"

# Get thread messages (after chatting)
curl http://localhost:8889/api/v1/threads/thread_a/messages \
  -H "Authorization: Bearer $SESSION"
```

### Error Logging Test

```bash
# Start server and watch logs
python core/api/main.py 2>&1 | grep ERROR

# Trigger error (empty context_id)
curl -X POST http://localhost:8889/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION" \
  -d '{"context_id": "", "prompt": "test"}'

# Check: Error should appear in logs
# ❌ Wrong: No log output (silent failure)
```

---

## 9. Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Thread contamination | Silent exceptions | Enable logging, check storage files |
| Empty storage | Embedding failure | Check Ollama, verify model supports embeddings |
| No response | Ollama offline | Start Ollama, check `.env` URL |
| 401 Unauthorized | Missing/invalid session | Get new session via auth flow |
| Import errors | Dependencies not installed | `pip install -r requirements.txt` or use `python3 run.py` |

### Debug Commands

```bash
# Check storage directories (scoped by user)
ls -R storage/memory/

# Check model config
cat storage/model.json

# Test Ollama connection
curl http://localhost:11434/api/tags

# Verify FAISS files exist
ls storage/memory/{user_id}/{context_id}/index.faiss
```

---

## 10. Lessons Learned

> **⚠️ THIS SECTION IS CRITICAL ⚠️**
> Every entry here represents a bug that was fixed.

### Bug #1: Silent Exception Handling

**Date**: 2026-04-12
**Impact**: Thread memory contamination
**Root Cause**: `except Exception: pass` hid all errors

**Rule**: Never use bare `except` or `except Exception: pass`

### Bug #2: Cross-Thread Response Mixing

**Date**: 2026-04-12
**Impact**: Responses from different threads mixed
**Root Cause**: `/api/generate` without session isolation

**Rule**: Use `/api/chat` with `session_id` for thread isolation

### Bug #3: Missing Logging

**Date**: 2026-04-12
**Impact**: Unable to diagnose issues
**Root Cause**: No logging in critical paths

**Rule**: All error paths MUST have logging

---

## 11. Quick Reference

### Must-Read Files

| File | Purpose |
|------|---------|
| `DEVELOPMENT_GUIDE.md` | This file |
| `GUIDELINES.md` | Technical rules |
| `RULES_CHECKLIST.md` | Pre-commit checklist |
| `core/config.py` | All configuration |
| `core/memory/vector_store.py` | Memory implementation |
| `core/api/main.py` | API endpoints |
| `core/auth/` | Auth system (magic links, sessions) |

### Default Models

| Setting | Default |
|---------|---------|
| Chat model | `qwen2.5-coder` |
| Embedding model | `qwen2.5-coder` |

Override via `.env`:
```
CODELY_CHAT_MODEL=qwen2.5-coder
CODELY_EMBEDDING_MODEL=qwen2.5-coder
```

### Emergency Contacts

For issues, check:
1. Server logs for ERROR entries
2. `storage/memory/{user_id}/{context_id}/` for FAISS files
3. `storage/model.json` for model config
4. `.env` for runtime settings
5. `storage/auth.db` for session data

---

**Document Version**: 0.7.0
**Last Updated**: 2026-07-18
**Enforcement**: STRICT - VIOLATIONS ARE HARD STOP
