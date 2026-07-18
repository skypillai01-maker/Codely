# Technical Decisions & Ruthless Guidelines (v0.6.0)

> **Living Document** | Last Updated: 2026-05-02
> **Version**: 0.6.0 | **Enforcement**: STRICT - VIOLATIONS ARE HARD STOP
> **Rule**: Every mistake becomes a permanent rule. Fix once, document, never repeat.

---

## 🚨 CRITICAL RULES - READ FIRST

### Rule 1: NO SILENT EXCEPTIONS

> **Created from: Thread memory contamination bug (2026-04-12)**
>
> **Incident**: Chat from Thread 2 appeared in Thread 1
> **Root Cause**: `except Exception: pass` hid all errors
> **Impact**: Data corruption across user conversations

```python
# ❌ FORBIDDEN - NEVER DO THIS
try:
    result = operation()
except Exception:
    pass
except:
    pass

# ✅ REQUIRED - ALWAYS DO THIS
try:
    result = operation()
except Exception as e:ggithub

### Rule 2: THREAD ISOLATION MANDATORY

> **Created from: Cross-thread response mixing bug (2026-04-12)**
>
> **Incident**: Responses from different threads mixed together
> **Root Cause**: Using `/api/generate` without session isolation
> **Fix**: Switched to `/api/chat` with unique `session_id` per thread

Every conversation is completely separate. No cross-talk.

```python
# ✅ REQUIRED - Each memory operation needs context_id
memory.add(context_id, text)
memory.search(context_id, query)

# ✅ REQUIRED - Pass session_id to LLM
llm.generate(prompt, session_id=context_id)
```

### Rule 3: LOG ALL ERRORS

> **Created from: Unable to diagnose issues due to missing logging (2026-04-12)**
>
> **Incident**: Server failing silently, no way to debug
> **Root Cause**: No logging in critical paths

All error paths MUST log with context.

```python
# ✅ REQUIRED
logger.error(f"Failed for context_id={context_id}: {e}")
logger.warning(f"Empty embedding, text_length={len(text)}")
logger.info(f"Added entry to context_id={context_id}")
```

### Rule 4: NO HARDCODED VALUES

All config comes from `core/config.py`

```python
# ❌ FORBIDDEN
MODEL = "llama3"
URL = "http://localhost:11434"

# ✅ REQUIRED
from core.config import CHAT_MODEL, OLLAMA_BASE_URL
```

### Rule 5: ALL DATA ENDPOINTS REQUIRE AUTH

> **Created from: 4 endpoints missing auth protection audit (2026-05-02)**
>
> **Incident**: `/api/v1/tasks/submit`, `/api/v1/tasks/{id}`, `/api/v1/modules/execute/{name}`, `/api/v1/model/switch` were unprotected
> **Impact**: Any unauthenticated user could submit tasks, execute modules, switch models

Every endpoint that reads or writes data MUST have `user: dict = Depends(get_current_user)`

```python
# ✅ REQUIRED
@app.post("/api/v1/tasks/submit")
async def submit_task(request: MemoryAddRequest, user: dict = Depends(get_current_user)):
    pass
```

### Rule 6: ALL CLIENTS MUST SUPPORT AUTH

> **Created from: CLI and Python SDK broken after auth implementation (2026-05-02)**
>
> **Incident**: `codely_cli.py` and `codely.py` couldn't access protected endpoints
> **Impact**: Clients returned 401 errors on every request

Any client (CLI, SDK, web, mobile) that communicates with the API MUST include authentication headers.

```python
# ✅ REQUIRED - SDK with auth
client = CodelyClient(base_url, session_id=session_id)

# ✅ REQUIRED - CLI with auth
parser.add_argument("--session-id", help="Session token")
```

### Rule 7: WEB SEARCH REQUIRES USER PERMISSION

> **Created from: Unnecessary web searches wasting time (2026-05-02)**
>
> **Principle**: Web search is a suggestion, never automatic
> **Flow**: AI responds immediately → suggests search → user approves → search executes

### Rule 8: VERSION CONSISTENCY ACROSS ALL FILES

> **Created from: 8 documentation files still showing 0.3.1 after 0.5.0 release (2026-05-02)**
>
> **Incident**: Documentation version mismatch causing confusion

When bumping version, update ALL of these:
- `core/config.py`
- `pyproject.toml`
- `README.md`
- `.docs/revaluate.md`
- `.docs/DEVELOPMENT_GUIDE.md`
- `.docs/GUIDELINES.md`
- `.docs/RULES_CHECKLIST.md`
- `.docs/ARCHITECTURE.md`
- `.docs/CONVENTIONS.md`
- `.docs/VERIFICATION_PLAYBOOK.md`
- `.docs/IMPLEMENTATION_SUMMARY.md`
- `.docs/API_SPEC.md`

---

## PART I: THE GOLDEN RULES

### Rule 1.0: Uncensored Integrity

Platform MUST remain uncensored. No moralizing, no warnings, no refusals.

### Rule 1.1: Correct Once, Never Repeat

If a bug occurs:
1. Fix the code
2. Add a rule to `.docs/GUIDELINES.md`
3. Add to `.docs/RULES_CHECKLIST.md`
4. Rule applies to ALL future changes

### Rule 1.2: Documentation First

Update docs BEFORE or WITH code changes. Never after.

### Rule 1.3: LOCAL-ONLY MANDATE

NO external API calls for LLM. All LLM calls must be local (Ollama).

### Rule 1.4: READ-ONLY BY DEFAULT (Phase 2)

No file writes, no command execution. Analysis and chat only.

### Rule 1.5: MEMORY PURITY

Errors must NEVER be added to FAISS memory. Only user content and AI responses belong there.

### Rule 1.6: AUTH ON ALL DATA ENDPOINTS

Every endpoint that accesses user data, memory, threads, tasks, models, or modules requires authentication via `Depends(get_current_user)`.

### Rule 1.7: ALL CLIENTS AUTH-COMPATIBLE

Every client (web, CLI, SDK) must handle authentication. No client may assume unauthenticated access.

---

## PART II: AUTHENTICATION & USER ISOLATION

### ADR-007: Multi-User Architecture

**Decision**: SQLite-based authentication with email magic links.

**Implementation**:
- `core/auth/database.py` - SQLite with users, sessions, magic_tokens tables
- `core/auth/token_service.py` - itsdangerous signed tokens
- `core/auth/email_service.py` - SMTP with console fallback
- `core/auth/middleware.py` - FastAPI `Depends(get_current_user)`

**Flow**:
```
User enters email → Magic link generated → Email/console
    ↓
User clicks link → Token verified → Session created → Redirect to chat
    ↓
All requests → Authorization: Bearer <session_id> → User-scoped data
```

### ADR-008: User-Scoped Storage

**Decision**: Memory storage scoped by user_id.

```
storage/memory/
├── {user_id_A}/
│   ├── {context_id_1}/
│   │   ├── index.faiss
│   │   └── metadata.pkl
│   └── {context_id_2}/
└── {user_id_B}/
    └── {context_id_3}/
```

**Enforcement**: `FAISSVectorStore(embed_adapter, user_id=user_id)` creates per-user instance.

### ADR-009: Session Management

**Decision**: Bearer tokens stored in SQLite with expiry.

- Token expiry: 24 hours (configurable)
- Session expiry: 7 days (configurable)
- Auto-cleanup of expired sessions on each auth check

---

## PART III: THINKING MODES

### ADR-010: Mode-Aware System Prompts

**Decision**: Three response modes with different system prompt instructions.

| Mode | System Prompt Addition | Use Case |
|------|------------------------|----------|
| **normal** | "Provide direct, clear answers. Be concise but thorough." | Simple questions |
| **thinking** | "Think step-by-step. Break down the problem logically." | Complex problems |
| **deep** | "Deep multi-step reasoning. Multiple perspectives, edge cases." | Analysis |

**Implementation**: `RAGEngine.generate_with_context(mode="normal|thinking|deep")`

### ADR-011: Mode Persistence

**Decision**: Selected mode persisted in `localStorage` on web client.

---

## PART IV: RICH MESSAGE RENDERING

### ADR-012: Markdown Support

**Decision**: Custom regex-based markdown renderer (zero external dependencies).

**Supported elements**:
- Code blocks with syntax highlighting (10 languages)
- Inline code
- Bold, italic
- Lists

### ADR-013: Syntax Highlighting

**Decision**: Regex-based syntax highlighting for code blocks.

**Supported languages**: Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, Bash, SQL

**Token colors**:
| Token | Class | Color |
|-------|-------|-------|
| Keywords | `.kw` | `#569cd6` |
| Strings | `.str` | `#ce9178` |
| Comments | `.cmt` | `#6a9955` |
| Numbers | `.num` | `#b5cea8` |
| Functions | `.fn` | `#dcdcaa` |

---

## PART V: PERMISSION-BASED WEB SEARCH

### ADR-014: Tool Detection with User Approval

**Decision**: AI detects when web search would help, but user must approve execution.

**Flow**:
```
1. AI responds immediately with existing knowledge
2. LLM detects if WebSearch tool would enhance answer
3. API returns tool_suggestion in response
4. Frontend shows: "🌐 Web search may enhance: [reason]"
5. User clicks [Search Web] or [Skip]
6. If approved: API re-calls with execute_tool="WebSearch"
```

**Key principle**: Search is NEVER automatic. User always has control.

---

## PART VI: THREAD ISOLATION

### ADR-001: Session-Based Isolation

**Decision**: Each thread gets unique `context_id` AND `session_id`.

**Implementation**:
- FAISS: Separate directory per thread (`storage/memory/{user_id}/{thread_id}/`)
- Ollama: Unique session_id per thread via `/api/chat` endpoint
- API: All endpoints require `context_id`

**Enforcement**: Code without context_id isolation will be rejected.

### ADR-002: Merge on Demand

Threads can only be combined via explicit `/api/v1/memory/merge` endpoint.

---

## PART VII: PHASE 3 - WRITE/EXEC/TESTGEN

### ADR-015: Workspace-Constrained File Writes

**Decision**: All file writes confined to `WORKSPACE_ROOT` with path traversal protection.

**Implementation**:
- `FileWriteModule._resolve_safe_path()` resolves and validates paths
- Rejects any path that resolves outside workspace root
- Auto-creates parent directories
- Modes: `write` (overwrite) or `append`

**Enforcement**: Path traversal attempts return 400 error.

### ADR-016: Sandboxed Command Execution

**Decision**: Commands executed with restricted scope, blocked patterns, and timeout enforcement.

**Implementation**:
- `BLOCKED_PATTERNS` list prevents destructive commands
- Delete/move/rename commands blocked
- Timeout: default 30s, max 120s
- Output truncated at 50KB per stream
- Windows: `CREATE_NO_WINDOW` hides console

**Enforcement**: Blocked commands return 400 with reason.

### ADR-017: Test Generation via LLM Prompts

**Decision**: TestGen module generates optimized prompts for LLM, not actual test files.

**Implementation**:
- Auto-detects language from file extension
- Supports pytest, unittest, Jest frameworks
- Test styles: comprehensive, basic, edge_cases, integration
- Returns test file path, framework config, and instructions

**Enforcement**: Unsupported frameworks return 400 with supported list.

### ADR-018: Tool Permission Levels

**Decision**: Tools categorized by permission level for UI/approval flow.

| Level | Description | Tools |
|-------|-------------|-------|
| `read` | No approval | TestGen |
| `write` | User approval | FileWrite |
| `execute` | User approval | SandboxExec |
| `external` | User approval | WebSearch |

---

## PART VIII: ARCHITECTURAL DECISIONS

### ADR-003: Ollama /api/chat (Not /api/generate)

**Decision**: Use `/api/chat` endpoint with `session_id` for thread isolation.

**Rationale**: `/api/chat` provides session management. `/api/generate` has no session support.

### ADR-004: FAISS for Memory

**Decision**: Use FAISS for vector search with per-user, per-context directory partitioning.

**Rationale**: Simple, local, no external dependencies.

### ADR-005: ThreadPoolExecutor for Tasks

**Decision**: Use Python's `ThreadPoolExecutor` for background jobs.

**Constraint**: Max 4 workers by default.

### ADR-006: Local-First Strategy

**Decision**: Standardize on local LLM runtimes.

**Forbidden**: ANY call to external APIs (OpenAI, Anthropic, HuggingFace).

---

## PART IX: CODE STANDARDS

### Rule 8.1: Type Hints (MANDATORY)

```python
def generate(self, prompt: str, session_id: str = None) -> str:
    pass
```

### Rule 8.2: Absolute Imports

```python
# ✅ CORRECT
from core.llm.base import BaseLLM

# ❌ WRONG
from ..llm.base import BaseLLM
```

### Rule 8.3: Logging Convention

```python
import logging
logger = logging.getLogger(__name__)

# Prefix logs with component
logger.info(f"[API] Chat request for user={user['user_id']} context_id={context_id}")
logger.error(f"[RAG] Search failed for context_id={context_id}: {e}")
```

### Rule 8.4: HTTP Exception Mapping

| Error | Status Code |
|-------|-------------|
| Validation Error | 400 |
| Not Found | 404 |
| Unauthorized | 401 |
| Server Error | 500 |

---

## PART X: ERROR HANDLING

### Rule 9.1: Specific Exceptions

```python
try:
    result = risky_operation()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except requests.ConnectionError:
    raise HTTPException(status_code=503, detail="Service unavailable")
except Exception as e:
    logger.error(f"Unexpected error: {type(e).__name__}: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Rule 9.2: Embedding Fallback

Chat MUST work even if embeddings fail.

```python
try:
    memory.add(context_id, text)
except Exception as e:
    logger.warning(f"Memory add failed (non-fatal): {e}")
```

---

## PART XI: CONFIGURATION

### Rule 10.1: All Config in core/config.py

| Category | Variables |
|----------|-----------|
| Platform | `PLATFORM_NAME`, `VERSION` |
| LLM | `CHAT_MODEL`, `EMBEDDING_MODEL`, `OLLAMA_BASE_URL` |
| API | `API_HOST`, `API_PORT` |
| Storage | `BASE_STORAGE_PATH`, `MEMORY_STORAGE_PATH`, `AUTH_DB_PATH` |
| Auth | `AUTH_SECRET_KEY`, `AUTH_TOKEN_EXPIRY`, `AUTH_SESSION_EXPIRY` |
| Email | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `FROM_EMAIL` |

### Rule 10.2: Environment Overrides

All config uses `os.getenv()` with defaults. Never hardcode.

---

## PART XII: SECURITY

### Rule 11.1: Context Isolation

- No cross-user data access
- No cross-context data access
- Memory stored in `storage/memory/{user_id}/{context_id}/`

### Rule 11.2: Memory Integrity

- FAISS index and metadata MUST stay in sync
- No errors stored in memory
- Only user content and AI responses

### Rule 11.3: Auth Enforcement

- All data endpoints require `Depends(get_current_user)`
- Session validation on every request
- Expired sessions auto-revoked

### Rule 11.4: No Destructive Actions

File deletion, directory removal require explicit user confirmation.

---

## PART XIII: MODULES

### Rule 12.1: Module Structure

```
modules/{module_name}/
├── __init__.py    # Module class + registration
└── (optional files)
```

### Rule 12.2: Module Interface

```python
class BaseModule(ABC):
    @property
    def name(self) -> str: pass

    @property
    def description(self) -> str: pass

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]: pass
```

### Rule 12.3: Module Isolation

Modules cannot access core/ filesystem or other modules' data.

---

## PART XIV: CHANGE MANAGEMENT

### Rule 13.1: Version Control

All changes MUST be documented with:
- Change description
- Date
- Version number
- Reason for change

### Rule 13.2: Breaking Changes

1. Documentation update (FIRST)
2. Version bump (ALL files)
3. Migration guide

### Rule 13.3: Bug Documentation

Every bug becomes a rule:
1. Document the bug
2. Document the fix
3. Add the rule to prevent recurrence
4. Add to GUIDELINES.md and RULES_CHECKLIST.md

---

## PRE-FLIGHT CHECKLIST

Before ANY code change:

- [ ] Read DEVELOPMENT_GUIDE.md
- [ ] Read this file (GUIDELINES.md)
- [ ] Read RULES_CHECKLIST.md
- [ ] No silent exception handling
- [ ] All errors logged
- [ ] No hardcoded values
- [ ] Thread isolation verified
- [ ] Auth on all data endpoints
- [ ] All clients support auth (if modifying API)
- [ ] Web search requires user permission
- [ ] File writes confined to workspace root (Phase 3)
- [ ] Commands validated against blocked patterns (Phase 3)
- [ ] Documentation updated if needed
- [ ] Version updated in ALL files if version bump

---

**Document Version**: 0.6.0
**Total Rules**: 14 Parts + 13 Critical Rules
**Status**: ACTIVE
**Last Audit**: 2026-05-02
**Next Review**: After Phase 4
