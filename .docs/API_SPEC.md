# API Specification (v0.6.1)

> **Living Document** | Last Updated: 2026-05-03
> **Version**: 0.6.1 | **Enforcement**: STRICT

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
  "context_id": "string",
  "response": "string"
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
| **Context Isolation** | Every request (except health, model, provider) MUST include a `context_id` |
| **Statelessness** | No session-based data. Every request is self-contained |
| **Versioning** | All endpoints are prefixed with `/api/v1/` |
| **Local-Only** | NO calls to external APIs. All processing is local |

---

## 3. Health & System

### 3.1 Health Check

```
GET /health
```

**Response (200):**
```json
{
  "status": "healthy",
  "platform": "Codely AI",
  "version": "0.6.1"
}
```

---

## 4. Chat & Memory (Existing)

### 4.1 Chat (RAG Enabled)

```
POST /api/v1/chat
```

**Payload:**
```json
{
  "context_id": "string",
  "prompt": "string",
  "user_id": "string (optional)",
  "stream": "boolean (default: false)"
}
```

**Response (200):**
```json
{
  "context_id": "string",
  "response": "string"
}
```

### 4.2 Chat with Files & URLs (NEW)

```
POST /api/v1/chat-with-files
Content-Type: multipart/form-data
```

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context_id` | string | Yes | Conversation context |
| `prompt` | string | Yes | User message |
| `save_to_memory` | boolean | No | Save attachments to memory (default: false) |
| `urls` | string | No | Comma-separated URLs |
| `files` | file[] | No | Multiple file attachments |

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
  "context_id": "string",
  "response": "string",
  "attachments": {
    "files": ["file1.pdf", "image.png"],
    "urls": ["https://example.com"]
  },
  "saved_to_memory": true
}
```

**Example (curl):**
```bash
curl -X POST http://localhost:8889/api/v1/chat-with-files \
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

### 4.3 Add Memory

```
POST /api/v1/memory/add
```

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
  "message": "Memory added successfully"
}
```

### 4.3 Clear Memory

```
DELETE /api/v1/memory/clear/{context_id}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Memory for {context_id} cleared"
}
```

### 4.4 Search Memory

```
POST /api/v1/memory/search
```

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
  "status": "success",
  "results": [
    {
      "text": "string",
      "metadata": "object",
      "score": "float"
    }
  ]
}
```

### 4.5 Merge Memory (NEW)

```
POST /api/v1/memory/merge
```

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
  "message": "Successfully merged 10 entries",
  "entries_merged": 10,
  "target_context_id": "string",
  "source_context_ids": ["string", "string"]
}
```

---

## 4b. Thread Management (NEW)

### 4b.1 List Threads

```
GET /api/v1/threads
```

**Response (200):**
```json
{
  "threads": [
    {
      "id": "thread_123",
      "entries": 5,
      "size_bytes": 1024,
      "exists": true
    }
  ],
  "count": 1
}
```

### 4b.2 Get Thread Stats

```
GET /api/v1/threads/{context_id}/stats
```

**Response (200):**
```json
{
  "context_id": "thread_123",
  "entries": 5,
  "size_bytes": 1024,
  "exists": true
}
```

### 4b.3 Delete Thread

```
DELETE /api/v1/threads/{context_id}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Thread thread_123 deleted"
}
```

---

## 5. Task Engine (Enhanced)

### 5.1 Submit Task

```
POST /api/v1/tasks/submit
```

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

### 5.2 Get Task Status

```
GET /api/v1/tasks/{task_id}
```

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

### 5.3 List Tasks

```
GET /api/v1/tasks
```

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

### 5.4 Stream Task Progress (NEW)

```
GET /api/v1/tasks/{task_id}/stream
```

**Response**: Server-Sent Events (SSE)
```
data: {"id":"...", "status":"running", "progress":50, "message":"Processing..."}

data: {"id":"...", "status":"completed", "progress":100, "result":"..."}
```

### 5.5 Cancel Task (NEW)

```
POST /api/v1/tasks/{task_id}/cancel
```

**Response (200):**
```json
{
  "status": "cancelled"
}
```

**Response (404):**
```json
{
  "status": "error",
  "detail": "Task not found"
}
```

---

## 6. Modules (Existing)

### 6.1 List Modules

```
GET /api/v1/modules
```

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

### 6.2 Execute Module

```
POST /api/v1/modules/execute/{module_name}
```

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

## 7. Multi-Modal Ingestion (Existing)

### 7.1 Upload File

```
POST /api/v1/ingest/file
Content-Type: multipart/form-data
```

**Form Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `context_id` | string | Yes | Target context |
| `user_id` | string | Yes | User ID for rate limiting |
| `file` | file | Yes | PDF, Image, Text, DOCX, XLSX, PPTX |

**Rate Limiting**: 10 requests per user per 60 seconds
**File Size Limit**: 50MB maximum

**Response (200):**
```json
{
  "status": "submitted",
  "task_id": "string",
  "message": "File {filename} is being processed in the background."
}
```

### 7.2 Ingest URL

```
POST /api/v1/ingest/url
```

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

## 8. Model Management (NEW - Phase 2)

### 8.1 List Available Models

```
GET /api/v1/model/list
```

**Response (200):**
```json
{
  "status": "success",
  "runtime": "ollama | openai_compat",
  "runtime_url": "string",
  "models": [
    {
      "name": "string",
      "size": "string (optional)",
      "modified_at": "datetime (optional)"
    }
  ]
}
```

### 8.2 Get Current Model

```
GET /api/v1/model/current
```

**Response (200):**
```json
{
  "status": "success",
  "model": "string",
  "runtime": "string",
  "capabilities": {
    "vision": "boolean",
    "streaming": "boolean",
    "embeddings": "boolean"
  }
}
```

### 8.3 Switch Model

```
POST /api/v1/model/switch
```

**Payload:**
```json
{
  "model": "string (required)",
  "runtime": "string (optional, default: auto-detect)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Switched to model {model}",
  "previous_model": "string",
  "new_model": "string"
}
```

**Response (400 - Model Not Found):**
```json
{
  "status": "error",
  "detail": "Model {model} not found. Available models: [...]"
}
```

### 8.4 Validate Connectivity

```
POST /api/v1/model/validate
```

**Payload (optional):**
```json
{
  "runtime": "string (optional)",
  "url": "string (optional)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "connected": "boolean",
  "runtime": "string",
  "url": "string",
  "available_models": ["string"]
}
```

---

## 9. LLM Runtime Providers (NEW - Phase 2)

### 9.1 List Available Runtimes

```
GET /api/v1/providers
```

**Response (200):**
```json
{
  "status": "success",
  "runtimes": [
    {
      "name": "ollama",
      "url": "http://localhost:11434",
      "status": "connected | disconnected",
      "models_count": "integer"
    },
    {
      "name": "openai_compat",
      "url": "http://localhost:1234/v1",
      "status": "connected | disconnected",
      "models_count": "integer"
    }
  ]
}
```

### 9.2 Detect Runtime

```
POST /api/v1/providers/detect
```

**Payload (optional):**
```json
{
  "url": "string (optional, default: localhost scan)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "detected": "boolean",
  "runtime": "string (ollama | openai_compat | none)",
  "url": "string",
  "message": "string"
}
```

---

## 10. Project Management (NEW - Phase 2)

### 10.1 Initialize Project

```
POST /api/v1/project/init
```

**Payload:**
```json
{
  "path": "string (required, absolute or relative path)",
  "auto_detect": "boolean (default: true)",
  "language": "string (optional, override auto-detect)",
  "framework": "string (optional)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "project_id": "string",
  "path": "string",
  "language": "string",
  "framework": "string (nullable)",
  "files_count": "integer"
}
```

### 10.2 Get Project Status

```
GET /api/v1/project/status
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `project_id` | string | Specific project (optional, uses active if not provided) |

**Response (200):**
```json
{
  "status": "success",
  "project_id": "string",
  "root_path": "string",
  "language": "string",
  "framework": "string",
  "files_count": "integer",
  "dependencies": ["string"],
  "last_updated": "ISO datetime",
  "is_active": "boolean"
}
```

### 10.3 List Projects

```
GET /api/v1/project/list
```

**Response (200):**
```json
{
  "status": "success",
  "projects": [
    {
      "project_id": "string",
      "path": "string",
      "language": "string",
      "last_updated": "ISO datetime"
    }
  ],
  "count": "integer"
}
```

### 10.4 Scan Project

```
POST /api/v1/project/scan
```

**Payload:**
```json
{
  "project_id": "string",
  "deep_scan": "boolean (default: false)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "project_id": "string",
  "scan_duration_ms": "integer",
  "files_found": "integer",
  "structure": {
    "directories": ["string"],
    "file_types": {
      "extension": "count"
    }
  }
}
```

### 10.5 Get Project Tree

```
GET /api/v1/project/tree
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `project_id` | string | Project ID |
| `path` | string | Relative path within project (optional) |
| `depth` | integer | Max depth (default: 3, max: 10) |

**Response (200):**
```json
{
  "status": "success",
  "project_id": "string",
  "path": "string",
  "tree": {
    "name": "root",
    "type": "directory",
    "children": [
      {
        "name": "src",
        "type": "directory",
        "children": [...]
      },
      {
        "name": "main.py",
        "type": "file",
        "size": "integer"
      }
    ]
  }
}
```

### 10.6 Close Project

```
DELETE /api/v1/project/close
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `project_id` | string | Project to close |

**Response (200):**
```json
{
  "status": "success",
  "message": "Project {project_id} closed"
}
```

---

## 11. Execution Engine (NEW - Phase 2)

> **READ-ONLY OPERATIONS ONLY** | No file writes permitted

### 11.1 Analyze File

```
POST /api/v1/execute/analyze
```

**Payload:**
```json
{
  "path": "string (required, absolute or project-relative path)",
  "project_id": "string (optional)",
  "include_imports": "boolean (default: true)",
  "include_exports": "boolean (default: true)",
  "include_functions": "boolean (default: true)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "path": "string",
  "language": "string",
  "analysis": {
    "lines": "integer",
    "imports": ["string"],
    "exports": ["string"],
    "functions": [
      {
        "name": "string",
        "line": "integer",
        "params": ["string"]
      }
    ],
    "classes": [
      {
        "name": "string",
        "line": "integer",
        "methods": ["string"]
      }
    ]
  }
}
```

### 11.2 Analyze Project

```
POST /api/v1/execute/analyze-project
```

**Payload:**
```json
{
  "project_id": "string",
  "options": {
    "include_tests": "boolean (default: false)",
    "include_deps": "boolean (default: true)"
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "project_id": "string",
  "summary": {
    "total_files": "integer",
    "total_lines": "integer",
    "languages": {
      "extension": "count"
    },
    "complexity_score": "integer (0-100)"
  }
}
```

### 11.3 Explain Code

```
POST /api/v1/execute/explain
```

**Payload:**
```json
{
  "path": "string (required)",
  "focus": "string (optional, e.g., 'function_name' or 'class_name')",
  "project_id": "string (optional)",
  "depth": "basic | detailed (default: basic)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "path": "string",
  "explanation": "string (markdown formatted)",
  "focus_item": "string (if focus was specified)"
}
```

### 11.4 Suggest Improvements

```
POST /api/v1/execute/suggest
```

**Payload:**
```json
{
  "path": "string (required)",
  "project_id": "string (optional)",
  "category": "all | performance | security | style | bugs (default: all)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "path": "string",
  "suggestions": [
    {
      "line": "integer (nullable)",
      "type": "performance | security | style | bug",
      "severity": "low | medium | high",
      "message": "string",
      "suggestion": "string",
      "code_snippet": "string (optional)"
    }
  ]
}
```

### 11.5 Search Code

```
POST /api/v1/execute/search
```

**Payload:**
```json
{
  "pattern": "string (required)",
  "project_id": "string (optional)",
  "path": "string (optional, search within specific path)",
  "glob": "string (optional, e.g., '**/*.py')",
  "case_sensitive": "boolean (default: false)",
  "regex": "boolean (default: false)"
}
```

**Response (200):**
```json
{
  "status": "success",
  "pattern": "string",
  "matches": [
    {
      "file": "string",
      "line": "integer",
      "content": "string",
      "context": "string (surrounding lines)"
    }
  ],
  "count": "integer"
}
```

### 11.6 Read File

```
GET /api/v1/execute/read
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `path` | string | Absolute or project-relative path |
| `project_id` | string | For relative paths |
| `start_line` | integer | Start line (default: 1) |
| `end_line` | integer | End line (default: 100) |

**Response (200):**
```json
{
  "status": "success",
  "path": "string",
  "lines": "integer (total)",
  "content": "string (requested range)",
  "truncated": "boolean"
}
```

---

## 11. Phase 3: Tools API

### 11.1 List Tools

**Endpoint:** `GET /api/v1/tools`

**Auth:** None (public)

**Response (200):**
```json
{
  "tools": [
    {
      "name": "FileWrite",
      "description": "Write or update files safely within the workspace root",
      "requires_permission": true,
      "permission_level": "write"
    },
    {
      "name": "SandboxExec",
      "description": "Execute commands in a sandboxed environment",
      "requires_permission": true,
      "permission_level": "execute"
    },
    {
      "name": "TestGen",
      "description": "Generate unit tests for code files",
      "requires_permission": false,
      "permission_level": "read"
    },
    {
      "name": "WebSearch",
      "description": "Search the internet for real-time information",
      "requires_permission": true,
      "permission_level": "external"
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
| 400 | Bad Request | Invalid input, missing required fields |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable | Valid JSON but invalid semantics |
| 500 | Server Error | Unexpected internal failure |

---

## 13. Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.6.1 | 2026-05-03 | Production fixes: SSE progress, cancel tasks, rate limiting, timeouts, retry logic |
| 0.6.0 | 2026-05-03 | HNSW vector search, document chunking, document management API |
| 0.5.0 | 2026-05-02 | Phase 3: FileWrite, SandboxExec, TestGen tools API |
| 0.4.0 | 2026-05-02 | Thinking modes, markdown responses, permission-based web search, auth |
| 0.3.1 | 2026-04-12 | Multi-user auth, email magic links, user-scoped storage |
| 0.3.0 | 2026-04-12 | Thread isolation, ChatGPT-style UI, logging |
| 0.2.2 | 2026-04-11 | Critical bug fix: silent exceptions |
| 0.2.1 | 2026-04-11 | Chat with Files & URLs |
| 0.2.0 | 2026-04-11 | Model management, embedding fallback |
| 0.1.0 | Previous | Phase 2 architecture, initial release |

---

**Document Version**: 0.6.0  
**Enforcement**: STRICT - All new endpoints must follow this spec
