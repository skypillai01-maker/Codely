# Codely AI Platform - Architecture Blueprint (v0.6.1)

> **Living Document** | Last Updated: 2026-05-03
> **Status**: Production Ready | Thread Isolation | Phase 3 Write/Exec/TestGen | HNSW + Chunking | Production Hardened
> **Enforcement**: STRICT - VIOLATIONS ARE HARD STOP

---

## 1. Executive Summary

### 1.1 Mission Statement

**Codely = Your personal AI software engineer + system architect + execution engine**

Codely is a self-evolving development system that:
- Understands what you want to build
- Plans architecture
- Writes production-ready code
- Debugs itself
- Improves over time
- Stays modular for future upgrades

### 1.2 Core Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│                    CODELY CORE PRINCIPLES                        │
├─────────────────────────────────────────────────────────────────┤
│  1. LOCAL-ONLY MANDATE: No third-party API calls ever          │
│  2. THREAD ISOLATION: Each conversation completely separate    │
│  3. MODEL-AGNOSTIC: Any local LLM/VLM, swappable instantly     │
│  4. UNCENSORED INTELLIGENCE: Raw, objective information        │
│  5. LOG ALL ERRORS: Silent exceptions are FORBIDDEN            │
│  6. HNSW VECTOR SEARCH: O(log N) search with FAISS          │
│  7. DOCUMENT CHUNKING: Text split before embedding             │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Design Goals

| Goal | Description |
|------|-------------|
| **Eliminate Skill Gap** | Think like a senior developer on your behalf |
| **Eliminate Time Waste** | Generate correct code, fix errors automatically |
| **Eliminate Tool Dependency** | All-in-one self-contained dev environment |

### 1.4 Evolution Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ Complete | AI chatbot, RAG, multi-modal ingestion |
| **Phase 2.1** | ✅ Complete | Model management, embedding fallback |
| **Phase 2.2** | ✅ Complete | Chat with files & URLs |
| **Phase 2.3** | ✅ Complete | Thread isolation, ChatGPT-style UI |
| **Phase 2.4** | ✅ Complete | Multi-user auth, email magic links |
| **Phase 2.5** | ✅ Complete | HNSW vector search, document chunking, doc management |
| **Phase 2.6** | ✅ Complete | Production hardening (timeouts, rate limiting, SSE) |
| Phase 3 | ✅ Complete | Full execution engine, file writes, test generation |
| Phase 4 | Planned | Project scaffolding, code analysis, suggestions |
| Phase 5 | Planned | Git integration, PR generation, code review |

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CODELY PLATFORM                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         CLIENT LAYER                                  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────────┐ │    │
│  │  │ Web Client  │  │  CLI Tool   │  │     Python SDK              │ │    │
│  │  │ (HTML/JS)   │  │ (Argparse)  │  │     (Requests Wrapper)      │ │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      API GATEWAY (FastAPI)                           │    │
│  │  Endpoints: /chat, /chat-with-files, /threads, /model, /memory, │    │
│  │             /ingest/file, /documents, /tasks, /auth              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        CORE SERVICES                                  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │    RAG      │  │   Task     │  │  Module     │  │   LLM       │  │    │
│  │  │   Engine    │  │   Engine   │  │  Registry   │  │   Bridge    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     STORAGE LAYER                                    │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │    │
│  │  │   Memory    │  │   Tasks    │  │    Temp     │                   │    │
│  │  │  (FAISS+    │  │   (JSON)   │  │   (Files)   │                   │    │
│  │  │   HNSW)     │  │            │  │            │                   │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow Diagram

```
                               USER REQUEST
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │    API Gateway (Validation)    │
                     └──────────────────────────────┘
                                    │
               ┌────────────────────┼────────────────────┐
               │                    │                    │
               ▼                    ▼                    ▼
     ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
     │  Chat Handler   │  │  Model Manager  │  │ Memory Manager  │
     │ (session_id)    │  │ (LLM Routing)   │  │ (FAISS)         │
     └─────────────────┘  └─────────────────┘  └─────────────────┘
               │                    │                    │
               └────────────────────┼────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │       RAG Engine              │
                     │  1. Query Transform           │
                     │  2. Memory Search (context_id)│
                     │  3. Tool Detection            │
                     │  4. Response Generation       │
                     └──────────────────────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │     Ollama /api/chat          │
                     │  (session_isolation)          │
                     └──────────────────────────────┘
```

---

## 3. Core Components

### 3.1 Universal LLM Bridge

**Purpose**: Abstract all local LLM runtimes behind a unified interface.

```
core/llm/
├── base.py              # Abstract interface (all adapters inherit)
└── adapters/
    └── ollama.py        # Ollama /api/chat with session isolation
```

#### 3.1.1 Supported Runtimes

| Runtime | API Style | Models Supported |
|---------|----------|-----------------|
| **Ollama** | /api/chat + /api/embeddings | llama3, dolphin, mistral, codellama, llava, moondream, nomic-embed-text |

#### 3.1.2 Adapter Interface (base.py)

```python
class BaseLLM(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: List[Dict] = None, session_id: str = None) -> str:
        """Generate text response."""
        pass

    @abstractmethod
    def stream(self, prompt: str, context: List[Dict] = None, session_id: str = None) -> Generator[str, None, None]:
        """Stream response."""
        pass

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embeddings."""
        pass

    @abstractmethod
    def validate_connectivity(self) -> bool:
        """Verify runtime is reachable."""
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models on this runtime."""
        pass

    @abstractmethod
    def describe_image(self, image_path: str, prompt: str = "Describe this image.") -> str:
        """Use vision model to describe an image."""
        pass
```

### 3.2 RAG Memory Layer

**Purpose**: Persistent contextual memory with thread isolation and HNSW vector search.

```
storage/memory/
├── {user_id}/
│   ├── thread_xxx_hvr7ad8lm/
│   │   ├── index.faiss      # HNSW vector index (O(log N) search)
│   │   └── metadata.pkl     # Text chunks + metadata (per thread)
│   └── thread_yyy_l0e3pgu8t/
│       ├── index.faiss      # HNSW with M=32, efConstruction=200
│       └── metadata.pkl     # Each entry: {text, metadata: {source, doc_id, timestamp}}
└── ...
```

#### 3.2.1 HNSW Configuration (Video-Grade Performance)

| Parameter | Value | Description |
|-----------|-------|-------------|
| `HNSW_M` | 32 | Number of bi-directional links per node |
| `HNSW_EF_CONSTRUCTION` | 200 | Build-time search width |
| `HNSW_EF_SEARCH` | 50 | Query-time search width |

*Same algorithm as Pinecone, Weaviate, Chroma - implemented via FAISS `IndexHNSWFlat`*

#### 3.2.2 Chunking Strategy

| Parameter | Value | Description |
|-----------|-------|-------------|
| `CHUNK_SIZE` | 1000 | Characters per chunk |
| `CHUNK_OVERLAP` | 200 | Overlap between chunks |

**Why Chunk**: Documents split into overlapping pieces before embedding → better RAG retrieval.

#### 3.2.3 Memory Isolation Rules

- **User Memory**: `storage/memory/{user_id}/` - Isolated per user
- **Thread Memory**: `storage/memory/{user_id}/{context_id}/` - Isolated per thread
- **Session Isolation**: Each thread uses unique `session_id` in Ollama
- **No Cross-Contamination**: User A can NEVER see User B's data
- **Document Tracking**: Each chunk has `doc_id` for document-level operations

#### 3.2.2 Memory Flow

```
User A - Thread 1 ──> context_id=thread_1 ──> session_id=thread_1
                                              FAISS: storage/memory/thread_1/

User A - Thread 2 ──> context_id=thread_2 ──> session_id=thread_2
                                              FAISS: storage/memory/thread_2/

User B - Thread 1 ──> context_id=thread_1 ──> session_id=thread_1
                                              FAISS: storage/memory/thread_1/
```

### 3.3 Task Engine

**Purpose**: Background processing for heavy operations.

```
core/task_engine/
└── manager.py       # Singleton TaskManager with ThreadPoolExecutor
```

#### 3.3.1 Task Persistence Rules

- Every task serialized to `storage/tasks/task_{task_id}.json`
- State updates on every transition (PENDING → RUNNING → COMPLETED/FAILED)
- Recovery on startup via task directory scan

### 3.4 Module System

**Purpose**: Extensible plugin architecture for capabilities.

```
modules/
├── search_web/      # DuckDuckGo integration
├── file_write/      # Safe file operations
├── sandbox_exec/    # Command execution
└── test_gen/        # Test generation
```

---

## 4. Document Management API (NEW)

### 4.1 Ingestion Endpoint

**POST** `/api/v1/ingest/file`

```python
# Request (multipart/form-data)
context_id: str      # Thread context
file: UploadFile      # File to ingest

# Response
{
    "status": "submitted",
    "task_id": "task_abc123",
    "message": "File document.pdf is being processed in the background."
}
```

**Background Processing**:
1. Save file to `storage/temp/`
2. Extract text based on file type (PDF, DOCX, XLSX, PPTX, TXT, Images)
3. Generate `doc_id` (MD5 hash of filename + content length)
4. Split text into chunks (`CHUNK_SIZE=1000`, `CHUNK_OVERLAP=200`)
5. Embed each chunk using Ollama `nomic-embed-text`
6. Add chunks to HNSW index with metadata `{source, doc_id, timestamp}`
7. Delete temp file

### 4.2 List Documents Endpoint

**GET** `/api/v1/documents`

```python
# Response
{
    "documents": [
        {
            "doc_id": "a3f8b2c1",
            "source": "document.pdf",
            "timestamp": "2026-05-03T10:30:00",
            "chunk_count": 15,
            "contexts": ["thread_xxx", "thread_yyy"]
        }
    ],
    "count": 1
}
```

**Logic**: Scans all user contexts, extracts `doc_id` from metadata, groups by document.

### 4.3 Delete Document Endpoint

**DELETE** `/api/v1/documents/{doc_id}`

```python
# Response
{
    "status": "success",
    "message": "Deleted 15 chunks for document a3f8b2c1",
    "deleted_chunks": 15
}
```

**Logic**: 
1. Scan all user contexts
2. Identify chunks with matching `doc_id`
3. Rebuild HNSW index without those chunks
4. Update metadata.pkl

---

---

## 4. Configuration Architecture

### 4.1 Central Configuration (core/config.py)

```python
from dotenv import load_dotenv
load_dotenv()

PLATFORM_NAME = "Codely AI"
VERSION = "0.6.1"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
CHAT_MODEL = os.getenv("CODELY_CHAT_MODEL", "llama3")
EMBEDDING_MODEL = os.getenv("CODELY_EMBEDDING_MODEL", "nomic-embed-text")

API_HOST = os.getenv("CODELY_API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("CODELY_API_PORT", "8889"))
```

### 4.2 Vector Store Configuration (core/memory/vector_store.py)

```python
# HNSW parameters (same as video - production grade)
HNSW_M = 32  # Number of bi-directional links per node
HNSW_EF_CONSTRUCTION = 200  # Build-time search width
HNSW_EF_SEARCH = 50  # Query-time search width

# Chunking parameters
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
```

### 4.3 .env File Configuration

```bash
OLLAMA_BASE_URL=http://localhost:11434
CODELY_CHAT_MODEL=llama3.2:3b
CODELY_EMBEDDING_MODEL=llama3.2:3b
CODELY_API_HOST=0.0.0.0
CODELY_API_PORT=8889
```

### 4.4 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `CODELY_CHAT_MODEL` | `llama3` | Model for generating responses |
| `CODELY_EMBEDDING_MODEL` | `nomic-embed-text` | Model for creating embeddings |
| `CODELY_API_HOST` | `0.0.0.0` | API bind address |
| `CODELY_API_PORT` | `8889` | API port |

---

## 5. Storage Structure

```
storage/
├── memory/
│   └── {user_id}/                  # User-scoped memory
│       ├── {context_id}/           # Thread-specific
│       │   ├── index.faiss         # HNSW vector index
│       │   └── metadata.pkl        # Text chunks + metadata
│       └── {context_id}/
│           ├── index.faiss
│           └── metadata.pkl
├── tasks/
│   └── task_{task_id}.json        # Task persistence
├── model.json                       # Persisted model config
└── temp/                           # Uploaded files (cleaned after processing)
```

### 5.1 Metadata Structure per Chunk

```python
{
    "text": "chunk text content...",
    "metadata": {
        "source": "document.pdf",      # Original filename
        "doc_id": "a3f8b2c1",        # Unique document ID (first 8 chars of MD5)
        "timestamp": "2026-05-03T10:30:00",  # Ingestion time
        "chunk_index": 0                  # Position in document
    }
}
```

---

## 6. Security Model

### 6.1 Isolation Boundaries

| Layer | Boundary | Enforcement |
|-------|----------|-------------|
| **Memory** | `context_id` | Directory partitioning |
| **Ollama Sessions** | `session_id` | API parameter |
| **Modules** | Sandboxed | No core/ filesystem access |

### 6.2 Forbidden Operations

```
1. Silent exception handling (except: pass)
2. Cross-thread data access
3. External API calls
4. Memory pollution (errors added to FAISS)
```

---

## 7. Phase 3: Write/Exec/TestGen Architecture

### 7.1 FileWrite Module

```
modules/file_write/
└── __init__.py        # FileWriteModule + registration
```

**Safety Guarantees**:
- Path traversal detection: `_resolve_safe_path()` resolves and validates against workspace root
- Workspace confinement: All writes must resolve within `WORKSPACE_ROOT`
- Auto-mkdir: Parent directories created automatically
- Modes: `write` (overwrite) or `append`

**API**: `POST /api/v1/tools/write-file`
```json
{
  "file_path": "src/example.py",
  "content": "print('hello')",
  "mode": "write"
}
```

### 7.2 SandboxExec Module

```
modules/sandbox_exec/
└── __init__.py        # SandboxExecModule + registration
```

**Security Model**:
- Blocked patterns: `rm -rf /`, `format`, `shutdown`, `del /f`, destructive commands
- Blocked actions: File deletion, move, rename (require explicit confirmation)
- Timeout: Configurable (default 30s, max 120s)
- Output truncation: stdout/stderr capped at 50KB each
- Windows: `CREATE_NO_WINDOW` flag hides console

**Allowed Commands**: ls, dir, cat, python, node, pip, npm, git, pytest, gcc, etc.

**API**: `POST /api/v1/tools/exec-command`
```json
{
  "command": "pytest tests/ -v",
  "timeout": 60,
  "workdir": "/path/to/project"
}
```

### 7.3 TestGen Module

```
modules/test_gen/
└── __init__.py        # TestGenModule + registration
```

**Supported Frameworks**:
| Framework | Test Pattern | Location | Run Command |
|-----------|--------------|----------|-------------|
| pytest | `test_*.py` | `tests/` | `pytest {file} -v` |
| unittest | `test_*.py` | `tests/` | `python -m unittest {file} -v` |
| jest | `*.test.js` | `__tests__/` | `jest {file}` |

**Language Detection**: Auto-detects from file extension or code content patterns.

**Test Styles**: `comprehensive`, `basic`, `edge_cases`, `integration`

**API**: `POST /api/v1/tools/generate-tests`
```json
{
  "code": "def add(a, b): return a + b",
  "file_path": "src/math.py",
  "framework": "pytest",
  "test_style": "comprehensive"
}
```

### 7.4 Tool Permission Levels

| Tool | Permission Level | Requires Approval |
|------|-----------------|-------------------|
| FileWrite | `write` | Yes |
| SandboxExec | `execute` | Yes |
| TestGen | `read` | No |
| WebSearch | `external` | Yes |

**API**: `GET /api/v1/tools` - Returns all available tools with permission levels.

---

## 8. Build System

### 8.1 Package Structure

```
Codely/
├── core/           # Top-level package (installed via pip)
├── modules/        # Extensible plugins
├── clients/        # Multi-client interfaces
└── storage/       # Runtime data
```

### 8.2 Installation

```bash
pip install -e .
```

---

## 9. Component Dependencies

```
main.py
├── OllamaAdapter
│   └── BaseLLM
├── FAISSVectorStore
│   └── BaseMemory
├── RAGEngine
│   ├── BaseLLM
│   └── BaseMemory
├── TaskManager (Singleton)
└── ModuleRegistry (Singleton)
```

---

## 9. Error Handling Strategy

> **⚠️ CRITICAL - All code MUST follow these rules ⚠️**

### 9.0 NO SILENT EXCEPTIONS (MANDATORY)

```python
# ❌ FORBIDDEN - This caused the thread isolation bug!
try:
    result = operation()
except Exception:
    pass  # NEVER DO THIS

# ✅ REQUIRED
try:
    result = operation()
except Exception as e:
    logger.error(f"Operation failed: {type(e).__name__}: {e}")
    raise  # or return safe default
```

### 9.1 ALL ERROR PATHS MUST LOG

Every catch block MUST include:
- `logger.error()` for failures
- `logger.warning()` for recoverable issues
- Include context (context_id, file path, etc.)

### 9.2 HTTP Exception Mapping

| Error Type | Status Code | Response |
|------------|-------------|----------|
| Validation Error | 400 | `{"detail": "Invalid input"}` |
| Not Found | 404 | `{"detail": "Resource not found"}` |
| Server Error | 500 | `{"detail": str(error)}` |

### 9.3 LLM Connection Errors

- Ollama not found → Startup warning, non-fatal
- Embedding fails → Graceful fallback, chat still works

---

## Appendix A: File Structure

```
Codely/
├── .docs/                  # Documentation (9 files)
├── core/                   # Main package
│   ├── api/main.py         # FastAPI application
│   ├── config.py           # Configuration
│   ├── llm/
│   │   ├── base.py         # Abstract LLM interface
│   │   └── adapters/ollama.py  # Ollama adapter
│   ├── memory/
│   │   ├── base.py         # Abstract memory interface
│   │   └── vector_store.py # FAISS vector store
│   ├── rag/engine.py       # RAG engine
│   ├── task_engine/manager.py  # Task manager
│   └── modules/            # Plugin registry
├── modules/search_web/     # DuckDuckGo module
├── clients/
│   ├── web/index.html      # ChatGPT-style Web UI
│   ├── cli/codely_cli.py   # CLI tool
│   └── python_sdk/codely.py # Python SDK
├── storage/                # Runtime data (gitignored)
├── .env                    # Configuration (gitignored)
├── requirements.txt
└── pyproject.toml
```

---

**Document Version**: 0.5.0
**Last Updated**: 2026-04-12
**Status**: ACTIVE - Production Ready
**Enforcement**: ALL changes must reference this document
**Critical Rules**: No silent exceptions | Thread isolation mandatory | Log all errors
