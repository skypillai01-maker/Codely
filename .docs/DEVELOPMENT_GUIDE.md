# Codely AI Platform - Development Guide

> **Version**: 0.6.0 | **Last Updated**: 2026-05-02
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
ollama pull llama3.2:3b

# Install dependencies
pip install -e .

# Configure
echo OLLAMA_BASE_URL=http://localhost:11434 > .env
echo CODELY_CHAT_MODEL=llama3.2:3b >> .env

# Start server
python core/api/main.py
```

### Verify

```bash
# Health check
curl http://localhost:8889/health

# Chat test
curl -X POST http://localhost:8889/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"context_id": "test", "prompt": "Hello"}'
```

---

## 2. Project Overview

**Codely** = Local-first AI platform with RAG memory, multi-modal ingestion, and ChatGPT-style thread isolation.

### Key Features

| Feature | Description |
|---------|-------------|
| **Thread Isolation** | Each conversation completely separate |
| **RAG Memory** | FAISS vector store per thread |
| **Multi-Modal** | PDF, DOCX, XLSX, PPTX, Images, URLs |
| **Local LLM** | Ollama only (no external APIs) |

---

## 3. 🚨 CRITICAL RULES

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

Every conversation is completely separate. No cross-talk.

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
MODEL = "llama3"
URL = "http://localhost:11434"

# ✅ REQUIRED
from core.config import CHAT_MODEL, OLLAMA_BASE_URL
```

---

## 4. Architecture

### Directory Structure

```
Codely/
├── core/                   # Main package
│   ├── api/main.py         # FastAPI app (557 lines)
│   ├── config.py          # Configuration (20 lines)
│   ├── llm/
│   │   ├── base.py        # Abstract LLM interface
│   │   └── adapters/ollama.py  # Ollama adapter
│   ├── memory/
│   │   ├── base.py        # Abstract memory interface
│   │   └── vector_store.py # FAISS implementation
│   ├── rag/engine.py      # RAG processing
│   ├── task_engine/manager.py  # Task manager
│   └── modules/           # Plugin registry
├── modules/search_web/    # DuckDuckGo module
├── clients/
│   ├── web/index.html     # ChatGPT-style Web UI
│   ├── cli/codely_cli.py  # CLI tool
│   └── python_sdk/codely.py # Python SDK
├── storage/               # Runtime data (gitignored)
├── .docs/               # 9 documentation files
└── .env                # Configuration (gitignored)
```

### Data Flow

```
User Request
     │
     ▼
API Validation (context_id required)
     │
     ▼
RAG Engine ──→ Memory Search (context_id)
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
Thread A ──> context_id=A ──> session_id=A ──> Ollama
Thread B ──> context_id=B ──> session_id=B ──> Ollama

Each thread is completely isolated.
```

---

## 5. Code Standards

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

## 6. API Reference

### Chat Endpoints

#### Basic Chat
```
POST /api/v1/chat
{
  "context_id": "thread_123",
  "prompt": "Hello"
}
```

#### Chat with Files
```
POST /api/v1/chat-with-files
context_id: thread_123
prompt: Explain this
files: [uploaded files]
urls: https://example.com
save_to_memory: true
```

### Thread Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/threads` | List all threads |
| GET | `/api/v1/threads/{id}/stats` | Thread statistics |
| DELETE | `/api/v1/threads/{id}` | Delete thread |

### Memory

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/memory/add` | Add to memory |
| POST | `/api/v1/memory/search` | Search memory |
| POST | `/api/v1/memory/merge` | Merge threads |
| DELETE | `/api/v1/memory/clear/{id}` | Clear memory |

### Model Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/model/list` | List available models |
| GET | `/api/v1/model/current` | Get current models |
| POST | `/api/v1/model/switch` | Switch model |
| GET | `/api/v1/model/validate` | Check connection |

### Phase 3 Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tools` | List all tools with permissions |
| POST | `/api/v1/tools/write-file` | Write to file (workspace-confined) |
| POST | `/api/v1/tools/exec-command` | Execute sandboxed command |
| POST | `/api/v1/tools/generate-tests` | Generate unit tests |

---

## 7. Testing Guide

### Thread Isolation Test (MANDATORY)

```bash
# 1. Create Thread A
curl -X POST http://localhost:8889/api/v1/memory/add \
  -H "Content-Type: application/json" \
  -d '{"context_id": "thread_a", "text": "My favorite color is blue"}'

# 2. Create Thread B
curl -X POST http://localhost:8889/api/v1/memory/add \
  -H "Content-Type: application/json" \
  -d '{"context_id": "thread_b", "text": "My favorite color is red"}'

# 3. Verify storage directories exist
ls storage/memory/thread_a/  # Should show index.faiss + metadata.pkl
ls storage/memory/thread_b/  # Should show index.faiss + metadata.pkl

# 4. Search Thread A - should ONLY return "blue"
curl -X POST http://localhost:8889/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -d '{"context_id": "thread_a", "query": "favorite color"}'

# 5. Search Thread B - should ONLY return "red"
curl -X POST http://localhost:8889/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -d '{"context_id": "thread_b", "query": "favorite color"}'
```

### Error Logging Test

```bash
# Start server and watch logs
python core/api/main.py 2>&1 | Select-String "ERROR"

# Trigger error
curl -X POST http://localhost:8889/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"context_id": "", "prompt": "test"}'

# Check: Error should appear in logs
# ❌ Wrong: No log output (silent failure)
```

---

## 8. Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Thread contamination | Silent exceptions | Enable logging, check storage files |
| Empty storage | Embedding failure | Check Ollama, verify model supports embeddings |
| No response | Ollama offline | Start Ollama, check `.env` URL |
| Import errors | Package not installed | `pip install -e .` |

### Debug Commands

```bash
# Check storage directories
Get-ChildItem -Recurse storage/memory/

# Check model config
Get-Content storage/model.json

# Test Ollama connection
curl http://localhost:11434/api/tags

# Verify FAISS files exist
Test-Path storage/memory/{context_id}/index.faiss
```

---

## 9. Lessons Learned

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

## 10. Quick Reference

### Must-Read Files

| File | Purpose |
|------|---------|
| `DEVELOPMENT_GUIDE.md` | This file |
| `GUIDELINES.md` | Technical rules |
| `RULES_CHECKLIST.md` | Pre-commit checklist |
| `core/config.py` | All configuration |
| `core/memory/vector_store.py` | Memory implementation |
| `core/api/main.py` | API endpoints |

### Emergency Contacts

For issues, check:
1. Server logs for ERROR entries
2. `storage/memory/{context_id}/` for FAISS files
3. `storage/model.json` for model config
4. `.env` for runtime settings

---

**Document Version**: 0.5.0
**Last Updated**: 2026-04-12
**Enforcement**: STRICT - VIOLATIONS ARE HARD STOP
