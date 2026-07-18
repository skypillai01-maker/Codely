# API Specification (v0.7.0)

> **Living Document** | Last Updated: 2026-07-18
> **Version**: 0.7.0 | **Enforcement**: STRICT

---

## 1. Global Response Schemas

All endpoints MUST return one of the following JSON structures.

### 1.1 Success Response

```json
{
  "status": "success",
  "message": "string",
  "data": "object | list (optional)"
}
```

### 1.2 Chat Response

```json
{
  "response": "string",
  "tool_used": "string | null",
  "tool_suggestion": "object | null"
}
```

### 1.3 Error Response

```json
{
  "status": "error",
  "detail": "string"
}
```

### 1.4 List Response

```json
{
  "items": "list",
  "count": "integer"
}
```

---

## 2. Strict API Constraints

| Constraint | Rule |
|------------|------|
| **Authentication** | All endpoints except health, auth, model, modules, tools list require `Authorization: Bearer <session_id>` |
| **Versioning** | All endpoints are prefixed with `/api/v1/` |
| **Local-Only** | NO calls to external APIs. All processing is local |

---

## 3. Health & System

### 3.1 Health Check

```
GET /health
```

**Auth:** None (public)

**Response (200):**
```json
{
  "status": "ok",
  "service": "Codely AI",
  "ollama": true
}
```

**Degraded (Ollama down):**
```json
{
  "status": "degraded",
  "service": "Codely AI",
  "ollama": false
}
```

---

## 4. Authentication

### 4.1 Request Login (Page)

```
GET /api/v1/auth/request-login
```

**Auth:** None (public)

**Response (200):** HTML login page

### 4.2 Request Login (API)

```
POST /api/v1/auth/request-login
```

**Auth:** None (public)

**Payload:**
```json
{
  "email": "string",
  "display_name": "string (optional)"
}
```

**Response (200):**
```json
{
  "message": "Magic link sent! Check your email (or console in dev mode).",
  "dev_link": "string | null"
}
```

### 4.3 Verify Magic Link (GET - Browser Redirect)

```
GET /api/v1/auth/verify?token=<token>
```

**Auth:** None (public)

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `token` | string | Magic token from email |

**Response (302):** Redirect to `/?session_id=<session_id>`

**Error (400):** HTML error page with "Invalid or expired link"

### 4.4 Verify Magic Link (POST - API)

```
POST /api/v1/auth/verify
```

**Auth:** None (public)

**Payload:**
```json
{
  "token": "string"
}
```

**Response (200):**
```json
{
  "session_id": "string",
  "user_id": "string",
  "email": "string"
}
```

### 4.5 Get Current User

```
GET /api/v1/auth/me
```

**Auth:** Required (`Depends(get_current_user)`)

**Response (200):**
```json
{
  "user_id": "string",
  "email": "string",
  "display_name": "string",
  "session_id": "string"
}
```

### 4.6 Logout

```
POST /api/v1/auth/logout
```

**Auth:** Required (`Depends(get_current_user)`)

**Response (200):**
```json
{
  "message": "Logged out successfully"
}
```

---

## 5. Chat & Memory

### 5.1 Chat (RAG Enabled)

```
POST /api/v1/chat
```

**Auth:** Required (`Depends(get_current_user)`)

**Payload:**
```json
{
  "context_id": "string",
  "prompt": "string",
  "mode": "normal | thinking | deep (default: normal)"
}
```

**Response (200):**
```json
{
  "response": "string",
  "tool_used": "string | null",
  "tool_suggestion": {
    "name": "string",
    "reason": "string"
  } | null
}
```

### 5.2 Chat with Files & URLs

```
POST /api/v1/chat-with-files
Content-Type: multipart/form-data
```

**Auth:** Optional (`Depends(get_current_user_optional)`) — anonymous allowed

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context_id` | string | No | Conversation context (auto-generated if omitted) |
| `prompt` | string | No | User message |
| `mode` | string | No | `normal`, `thinking`, or `deep` (default: normal) |
| `save_to_memory` | boolean | No | Save attachments to memory (default: false) |
| `urls` | string | No | Comma-separated URLs |
| `files` | file[] | No | Multiple file attachments |
| `execute_tool` | string | No | Force-execute a specific tool module by name |

**Supported File Types:**
| Type | Extension | Processing |
|------|------------|-------------|
| Text | `.txt`, `.py`, `.js`, `.ts`, `.md` | Plain text read |
| PDF | `.pdf` | Text extraction via pypdf |
| Word | `.docx` | Text extraction via python-docx |
| Excel | `.xlsx`, `.xls` | Data extraction via openpyxl |
| PowerPoint | `.pptx` | Text extraction via python-pptx |
| Image | `.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif` | Vision model (llava) |
| Code | All code extensions | Plain text read |

**Response (200):**
```json
{
  "response": "string",
  "tool_used": "string | null",
  "tool_suggestion": "object | null",
  "mode": "string",
  "attachments": {
    "files": ["file1.pdf", "image.png"],
    "urls": ["https://example.com"],
    "saved": true
  },
  "saved_to_memory": true
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8889/api/v1/chat-with-files \
  -H "Authorization: Bearer <session_id>" \
  -F "context_id=test" \
  -F "prompt=Explain this document" \
  -F "files=@document.pdf" \
  -F "urls=https://example.com" \
  -F "save_to_memory=true"
```

**Example (CLI):**
```bash
python clients/cli/codely_cli.py chat "Explain this" --file document.pdf --url https://example.com --save-memory
```

### 5.3 Add Memory

```
POST /api/v1/memory/add
```

**Auth:** Required (`Depends(get_current_user)`)

**Payload:**
```json
{
  "context_id": "string",
  "text": "string",
  "metadata": "object (optional)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Memory added"
}
```

### 5.4 Search Memory

```
POST /api/v1/memory/search
```

**Auth:** Required (`Depends(get_current_user)`)

**Payload:**
```json
{
  "context_id": "string",
  "query": "string",
  "limit": "integer (default: 5)"
}
```

**Response (200):**
```json
{
  "results": [
    {
      "text": "string",
      "metadata": "object",
      "chunk_index": "integer"
    }
  ]
}
```

### 5.5 Clear Memory

```
DELETE /api/v1/memory/clear/{context_id}
```

**Auth:** Required (`Depends(get_current_user)`)

**Response (200):**
```json
{
  "status": "success",
  "message": "Memory cleared for {context_id}"
}
```

### 5.6 Merge Memory

```
POST /api/v1/memory/merge
```

**Auth:** Required (`Depends(get_current_user)`)

Merge memory from multiple threads into one.

**Payload:**
```json
{
  "target_context_id": "string",
  "source_context_ids": ["string", "string"]
}
```

**Response (200):**
```json
{
  "status": "success",
  "entries_merged": 10
}
```

---

## 6. Thread Management

### 6.1 List Threads

```
GET /api/v1/threads
```

**Auth:** Required (`Depends(get_current_user)`)

**Response (200):**
```json
{
  "threads": [
    {
      "id": "thread_123",
      "entries": 5,
      "name": "First message preview..."
    }
  ],
  "count": 1
}
```

### 6.2 Get Thread Stats

```
GET /api/v1/threads/{context_id}/stats
```

**Auth:** Required (`Depends(get_current_user)`)

**Response (200):**
```json
{
  "context_id": "thread_123",
  "entries": 5,
  "size_bytes": 1024,
  "name": "First message preview...",
  "exists": true
}
```

### 6.3 Get Thread Messages

```
GET /api/v1/threads/{context_id}/messages
```

**Auth:** Required (`Depends(get_current_user)`)

**Response (200):**
```json
{
  "context_id": "thread_123",
  "messages": [
    {
      "role": "user",
      "text": "What is Python?"
    },
    {
      "role": "ai",
      "text": "Python is a high-level programming language..."
    }
  ],
  "count": 2
}
```

### 6.4 Delete Thread

```
DELETE /api/v1/threads/{context_id}
```

**Auth:** Required (`Depends(get_current_user)`)

**Response (200):**
```json
{
  "status": "success",
  "message": "Thread thread_123 deleted"
}
```

---

## 7. Ingest

### 7.1 Ingest Text

```
POST /api/v1/ingest
Content-Type: multipart/form-data
```

**Auth:** Required (`Depends(get_current_user)`)

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context_id` | string | No | Target context (defaults to user_id) |
| `text` | string | Yes | Text content to ingest |

**Rate Limiting**: 10 requests per user per 60 seconds
**Max Active Tasks**: 2 per user

**Response (200):**
```json
{
  "task_id": "string",
  "status": "pending"
}
```

### 7.2 Ingest File

```
POST /api/v1/ingest/file
Content-Type: multipart/form-data
```

**Auth:** Required (`Depends(get_current_user)`)

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context_id` | string | No | Target context (defaults to user_id) |
| `file` | file | Yes | PDF, Image, Text, DOCX, XLSX, PPTX |

**Rate Limiting**: 10 requests per user per 60 seconds
**File Size Limit**: 50MB maximum
**Max Active Tasks**: 2 per user

**Response (200):**
```json
{
  "task_id": "string",
  "status": "pending"
}
```

### 7.3 Ingest URL

```
POST /api/v1/ingest/url
```

**Auth:** Required (`Depends(get_current_user)`)

**Payload:**
```json
{
  "context_id": "string",
  "url": "string",
  "extract_type": "text | screenshot (default: text)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Content extracted from URL",
  "extracted_text": "string"
}
```

---

## 8. Model Management

### 8.1 Get Model Config

```
GET /api/v1/model
```

**Auth:** None (public)

**Response (200):**
```json
{
  "chat_model": "llama3",
  "embedding_model": "nomic-embed-text"
}
```

### 8.2 Switch Model

```
POST /api/v1/model/switch
```

**Auth:** None (public)

**Payload:**
```json
{
  "model_type": "chat_model | embedding_model",
  "model_name": "string"
}
```

**Response (200):**
```json
{
  "message": "Model chat_model switched to llama3",
  "config": {
    "chat_model": "llama3",
    "embedding_model": "nomic-embed-text"
  }
}
```

**Response (400 - Missing Fields):**
```json
{
  "detail": "model_type and model_name are required"
}
```

---

## 9. Task Engine

### 9.1 Submit Task

```
POST /api/v1/tasks/submit
```

**Auth:** Required (`Depends(get_current_user)`)

**Payload:**
```json
{
  "context_id": "string",
  "text": "string",
  "metadata": "object (optional)"
}
```

**Response (200):**
```json
{
  "task_id": "string",
  "status": "submitted"
}
```

### 9.2 Get Task Status

```
GET /api/v1/tasks/{task_id}
```

**Auth:** None (public)

**Response (200):**
```json
{
  "id": "string",
  "status": "pending | running | completed | failed | cancelled",
  "result": "any",
  "error": "string (if failed)",
  "progress": "integer (0-100)",
  "message": "string (progress message)",
  "created_at": "ISO datetime",
  "started_at": "ISO datetime (nullable)",
  "finished_at": "ISO datetime (nullable)"
}
```

### 9.3 List Tasks

```
GET /api/v1/tasks
```

**Auth:** None (public)

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `user_id` | string | Filter by user (optional) |

**Response (200):**
```json
{
  "tasks": [
    {
      "id": "string",
      "status": "string",
      "progress": "integer",
      "created_at": "ISO datetime"
    }
  ],
  "count": "integer"
}
```

### 9.4 Stream Task Progress

```
GET /api/v1/tasks/{task_id}/stream
```

**Auth:** None (public)

**Response**: Server-Sent Events (SSE)
```
data: {"id":"...", "status":"running", "progress":50, "message":"Processing..."}

data: {"id":"...", "status":"completed", "progress":100, "result":"..."}
```

### 9.5 Cancel Task

```
POST /api/v1/tasks/{task_id}/cancel
```

**Auth:** None (public)

**Response (200):**
```json
{
  "status": "cancelled"
}
```

**Response (404):**
```json
{
  "detail": "Task not found"
}
```

---

## 10. Modules

### 10.1 List Modules

```
GET /api/v1/modules
```

**Auth:** None (public)

**Response (200):**
```json
{
  "modules": [
    {
      "name": "string",
      "description": "string"
    }
  ]
}
```

### 10.2 Execute Module

```
POST /api/v1/modules/execute/{module_name}
```

**Auth:** Required (`Depends(get_current_user)`)

**Payload:**
```json
{
  "params": "object"
}
```

**Response (200):**
```json
{
  "module": "string",
  "result": "object"
}
```

---

## 11. Tools API

### 11.1 List Tools

**Endpoint:** `GET /api/v1/tools`

**Auth:** None (public)

**Response (200):**
```json
{
  "tools": [
    {
      "name": "FileWrite",
      "description": "Write or update files within workspace",
      "requires_permission": true
    },
    {
      "name": "SandboxExec",
      "description": "Execute commands in sandboxed environment",
      "requires_permission": true
    },
    {
      "name": "TestGen",
      "description": "Generate unit tests for code",
      "requires_permission": false
    }
  ]
}
```

### 11.2 Write File

**Endpoint:** `POST /api/v1/tools/write-file`

**Auth:** Required (`Depends(get_current_user)`)

**Request Body:**
```json
{
  "file_path": "src/example.py",
  "content": "print('hello')",
  "mode": "write"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `file_path` | string | Yes | - | Path relative to workspace root |
| `content` | string | Yes | - | File content to write |
| `mode` | string | No | `"write"` | `"write"` or `"append"` |

**Response (200):**
```json
{
  "status": "success",
  "message": "Wrote src/example.py",
  "file_path": "src/example.py",
  "absolute_path": "/path/to/workspace/src/example.py",
  "bytes_written": 14,
  "lines": 1,
  "mode": "write"
}
```

**Security:**
- Path traversal detection: rejects paths resolving outside workspace root
- Parent directories auto-created

**Error Responses:**
| Status | Condition |
|--------|-----------|
| 400 | Path traversal detected, empty file_path, empty content |
| 500 | File write failed |

### 11.3 Execute Command

**Endpoint:** `POST /api/v1/tools/exec-command`

**Auth:** Required (`Depends(get_current_user)`)

**Request Body:**
```json
{
  "command": "pytest tests/ -v",
  "timeout": 60,
  "workdir": "/path/to/project"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `command` | string | Yes | - | Command to execute |
| `timeout` | integer | No | 30 | Timeout in seconds (max 120) |
| `workdir` | string | No | Workspace root | Working directory |

**Response (200):**
```json
{
  "status": "success",
  "command": "pytest tests/ -v",
  "exit_code": 0,
  "stdout": "collected 5 items\ntests/test_math.py::test_add PASSED\n...",
  "stderr": "",
  "elapsed_seconds": 2.34,
  "working_directory": "/path/to/project",
  "timeout_seconds": 60
}
```

**Blocked Commands:**
- `rm -rf /`, `rm -rf /*`, `format`, `mkfs`
- `shutdown`, `reboot`, `restart`
- `del /f /s /q`, `rd /s /q`
- File deletion, move, rename commands

**Error Responses:**
| Status | Condition |
|--------|-----------|
| 400 | Command blocked, timeout exceeded, invalid workdir |
| 500 | Execution failed |

### 11.4 Generate Tests

**Endpoint:** `POST /api/v1/tools/generate-tests`

**Auth:** Required (`Depends(get_current_user)`)

**Request Body:**
```json
{
  "code": "def add(a, b): return a + b",
  "file_path": "src/math.py",
  "framework": "pytest",
  "test_style": "comprehensive"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `code` | string | Yes | - | Source code to generate tests for |
| `file_path` | string | No | - | Source file path (for language detection) |
| `framework` | string | No | `"pytest"` | `"pytest"`, `"unittest"`, or `"jest"` |
| `test_style` | string | No | `"comprehensive"` | `"comprehensive"`, `"basic"`, `"edge_cases"`, `"integration"` |

**Response (200):**
```json
{
  "status": "success",
  "message": "Test generation prompt ready",
  "test_file_name": "test_math.py",
  "test_file_path": "src/tests/test_math.py",
  "framework": "pytest",
  "framework_config": {
    "pattern": "test_*.py",
    "location": "tests/",
    "imports": "import pytest",
    "run_command": "pytest {test_file} -v"
  },
  "language": "python",
  "test_prompt": "Generate comprehensive pytest tests for this python code...",
  "run_command": "pytest test_math.py -v",
  "instructions": "1. Save the generated test code to..."
}
```

**Error Responses:**
| Status | Condition |
|--------|-----------|
| 400 | No code provided, unsupported framework |
| 500 | Test generation failed |

---

## 12. Error Codes Reference

| HTTP Code | Meaning | When Used |
|-----------|---------|-----------|
| 200 | Success | Normal operation |
| 302 | Redirect | Magic link verification (GET) |
| 400 | Bad Request | Invalid input, missing required fields, expired token |
| 401 | Unauthorized | Missing or invalid session |
| 404 | Not Found | Resource doesn't exist |
| 413 | Payload Too Large | File exceeds size limit |
| 422 | Unprocessable | Valid JSON but invalid semantics |
| 429 | Rate Limited | Too many requests per time window |
| 500 | Server Error | Unexpected internal failure |
| 503 | Service Unavailable | Runtime error (e.g. Ollama not initialized) |

---

## 13. Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.7.0 | 2026-07-18 | Thread message history loading, server-side thread names, deterministic user_id (hash-based), embedding fallback (numpy hash), conversation memory persistence (rag.learn), spec cleanup |
| 0.6.2 | 2026-05-04 | Memory merge endpoint, messages endpoint, thread name derivation, auth refactor |
| 0.6.1 | 2026-05-03 | Production fixes: SSE progress, cancel tasks, rate limiting, timeouts, retry logic |
| 0.6.0 | 2026-05-03 | HNSW vector search, document chunking |
| 0.5.0 | 2026-05-02 | Phase 3: FileWrite, SandboxExec, TestGen tools API |
| 0.4.0 | 2026-05-02 | Thinking modes, markdown responses, permission-based web search, auth |
| 0.3.1 | 2026-04-12 | Multi-user auth, email magic links, user-scoped storage |
| 0.3.0 | 2026-04-12 | Thread isolation, ChatGPT-style UI, logging |
| 0.2.2 | 2026-04-11 | Critical bug fix: silent exceptions |
| 0.2.1 | 2026-04-11 | Chat with Files & URLs |
| 0.2.0 | 2026-04-11 | Model management, embedding fallback |
| 0.1.0 | Previous | Phase 2 architecture, initial release |

---

**Document Version**: 0.7.0
**Enforcement**: STRICT - All new endpoints must follow this spec
