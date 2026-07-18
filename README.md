# Codely AI Platform

**Version**: 0.6.1 | **Your personal AI software engineer + system architect + execution engine**

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

### 2. Configure

Create `.env` file:
```bash
OLLAMA_BASE_URL=http://localhost:11434
CODELY_CHAT_MODEL=llama3.2:3b
CODELY_EMBEDDING_MODEL=llama3.2:3b

# Optional: SMTP for email magic links (console fallback available)
CODELY_SMTP_HOST=smtp.gmail.com
CODELY_SMTP_PORT=587
CODELY_SMTP_USER=your-email@gmail.com
CODELY_SMTP_PASSWORD=your-app-password
CODELY_FROM_EMAIL=your-email@gmail.com
```

### 3. Start Server

```bash
python core/api/main.py
```

### 4. Access

- **Web UI**: http://localhost:8889/
- **CLI**: `python clients/cli/codely_cli.py chat "Hello"`

---

## Features

### Multi-User Authentication

- **Email magic link login** - no passwords to manage
- **User-scoped data isolation** - each user has separate memory storage
- **SQLite session management** - robust session handling with expiry
- **SMTP integration** - real email delivery or console fallback for dev

### ChatGPT-Style Thread Isolation

- **Each conversation is completely separate** - no cross-talk between threads
- **ChatGPT-style UI** - dark theme, rename chats, clear memory
- **Merge on demand** - only combine memories when you choose
- **Session-based isolation** - Ollama `/api/chat` with unique session_id per thread

### Smart Response Modes

- **Quick Mode** - Direct, concise answers
- **Thinking Mode** - Step-by-step reasoning with explanation
- **Deep Thinking Mode** - Comprehensive multi-step analysis with multiple perspectives

### Rich Message Rendering

- **Syntax-highlighted code blocks** with copy button (Python, JS, TS, Java, C/C++, Go, Rust, Bash, SQL)
- **Inline code**, **bold**, *italic*, and list formatting
- **Visual distinction** between code and normal text
- **Mode badges** show which response mode was used

### Smart Web Research

- **Permission-based** - AI suggests web search when relevant, you decide
- **No unnecessary searches** - Only triggers when current/real-time info would help
- **One-click execution** - "Search Web" button appears below the response
- **Research badges** on enhanced answers

### Write Capabilities (Phase 3)

- **Safe file writes** - Confined to workspace root with path traversal protection
- **Append or overwrite** - Flexible write modes for different use cases
- **Automatic directory creation** - Parent directories created as needed

### Sandboxed Command Execution (Phase 3)

- **Restricted scope** - Blocked patterns prevent destructive commands
- **Timeout enforcement** - Configurable timeout (default 30s, max 120s)
- **Output capture** - stdout/stderr captured and truncated if too large
- **Windows-compatible** - Uses `CREATE_NO_WINDOW` to hide console

### Test Generation (Phase 3)

- **Multi-framework** - Supports pytest, unittest, and Jest
- **Language detection** - Auto-detects source language from file extension
- **Test styles** - Comprehensive, basic, edge_cases, or integration focus
- **LLM-powered prompts** - Generates optimized prompts for test generation

### Chat with AI

- RAG-enabled responses with HNSW vector search
- Complete thread isolation
- Memory persistence per conversation
- Save to memory option

### Attachments & Document Management (NEW)

- **Multi-format support**: PDF, DOCX, XLSX, PPTX, TXT, Images, Code files, URLs
- **HNSW Algorithm**: O(log N) vector search (same as Pinecone/Weaviate)
- **Smart Chunking**: Text split into 1000-char chunks with 200-char overlap
- **Document Tracking**: Each document gets unique `doc_id` for management
- **Document API**: List all ingested documents, delete by document ID
- **Background Processing**: File ingestion runs in background tasks

### Model Management

- Independent chat/embedding models
- Local Ollama integration
- Model persistence (`storage/model.json`)
- Remote Ollama support (via `.env`)
- Embedding fallback (chat works even if embeddings fail)

### Clients

- **Web UI** - ChatGPT-style dark theme interface
- **CLI** - Command-line interface with thread management
- **Python SDK** - Programmatic access

### Multi-Modal Ingestion

| Format | Processing |
|--------|-----------|
| PDF | Text extraction via pypdf |
| DOCX | python-docx |
| XLSX | openpyxl |
| PPTX | python-pptx |
| Images | Vision model (llava) |
| Code files | Plain text |
| URLs | BeautifulSoup |

---

## Architecture

```
Codely/
├── core/           # Main package
│   ├── api/        # FastAPI endpoints (HNSW + Chunking)
│   ├── llm/        # Ollama adapter
│   ├── memory/     # FAISS vector store (HNSW + Chunking)
│   ├── rag/        # RAG engine
│   └── task_engine/# Background tasks
├── modules/        # Plugins (DuckDuckGo search)
├── clients/        # Web, CLI, Python SDK
├── .docs/          # Comprehensive documentation
└── storage/        # Runtime data (gitignored)
```

---

## HNSW Vector Search (Video-Grade Performance)

Codely uses **HNSW (Hierarchical Navigable Small World)** algorithm via FAISS:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `HNSW_M` | 32 | Bi-directional links per node |
| `HNSW_EF_CONSTRUCTION` | 200 | Build-time search width |
| `HNSW_EF_SEARCH` | 50 | Query-time search width |

**Same algorithm used by**: Pinecone, Weaviate, Chroma, Milvus

---

## Document Chunking Strategy

| Parameter | Value | Description |
|-----------|-------|-------------|
| `CHUNK_SIZE` | 1000 | Characters per chunk |
| `CHUNK_OVERLAP` | 200 | Overlap between chunks |

**Why Chunk**: Documents split before embedding → better RAG retrieval quality.

---

## API Endpoints (New)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ingest/file` | Ingest file with chunking (background) |
| `GET` | `/api/v1/documents` | List all ingested documents |
| `DELETE` | `/api/v1/documents/{doc_id}` | Delete document by ID |

---

## Documentation

| Document | Purpose |
|----------|---------|
| `DEVELOPMENT_GUIDE.md` | **START HERE** - Entry point for AI/developers |
| `GUIDELINES.md` | Technical rules and ADRs |
| `RULES_CHECKLIST.md` | **STRICT RULES** - Every mistake becomes a rule |
| `ARCHITECTURE.md` | System architecture (HNSW, Chunking) |
| `API_SPEC.md` | API documentation |
| `CONVENTIONS.md` | Coding standards |
| `VERIFICATION_PLAYBOOK.md` | Testing guide |
| `IMPLEMENTATION_SUMMARY.md` | Complete feature list |
| `revaluate.md` | Project status |

---

## Strict Rules (from RULES_CHECKLIST.md)

1. **User Memory**: Always use `get_memory_for_user(user_id)`, never global `memory`
2. **Background Tasks**: Pass `user_id` as first parameter to `task_manager.submit()`
3. **HNSW Only**: Use `IndexHNSWFlat`, never `IndexFlatL2` (brute-force)
4. **Chunk Before Embed**: Always call `_split_text()` before embedding
5. **Document Metadata**: All documents need `doc_id`, `source`, `timestamp`
6. **No Silent Exceptions**: Every `except` block MUST log with `logger.error()`
7. **Imports at Top**: All imports used must be at file top (hashlib, numpy, etc.)

---

## Requirements

- Python 3.8+
- Ollama (local or remote)
- SMTP server (optional, for email magic links)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.6.1 | 2026-05-03 | Production fixes: timeouts, retry logic, rate limiting, SSE, progress tracking, .env.example |
| 0.6.0 | 2026-05-03 | HNSW vector search, document chunking, document management API |
| 0.5.0 | 2026-05-02 | Phase 3: Write, Exec, TestGen tools |
| 0.4.0 | 2026-05-02 | Thinking modes, markdown/code rendering, permission-based web search |
| 0.3.1 | 2026-04-12 | Multi-user auth, email magic links, user-scoped storage |
| 0.3.0 | 2026-04-12 | Thread isolation, ChatGPT-style UI, logging |
| 0.2.2 | 2026-04-11 | Critical bug fix: silent exceptions |
| 0.2.1 | 2026-04-11 | Chat with Files & URLs |
| 0.2.0 | 2026-04-11 | Model management, embedding fallback |
| 0.1.0 | Previous | Phase 2 architecture, initial release |

---

## License

Private - All rights reserved.
