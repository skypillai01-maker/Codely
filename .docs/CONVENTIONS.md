# Coding Conventions & Standards (v0.7.0)

> **Living Document** | Last Updated: 2026-07-18
> **Enforcement**: STRICT

---

## 1. Python Standards

### 1.1 Type Hints (MANDATORY)

```python
# ✅ CORRECT
def process_data(user_id: str, limit: int = 10) -> Dict[str, Any]:
    pass

# ❌ WRONG
def process_data(user_id, limit=10):
    pass
```

### 1.2 Docstrings (REQUIRED for Public Methods)

```python
def generate(self, prompt: str, session_id: str = None) -> str:
    """
    Generate a response using the configured LLM.

    Args:
        prompt: The user prompt to process.
        session_id: Optional session ID for conversation isolation.

    Returns:
        The generated response string.

    Raises:
        RuntimeError: If LLM connection fails.
    """
    pass
```

### 1.3 Line Length

Maximum: **100 characters**

### 1.4 Import Organization

```python
# Standard library (alphabetical)
import json
import os
from typing import Dict, List, Optional

# Third-party packages
import requests
from fastapi import FastAPI

# Local imports (absolute)
from core.llm.base import BaseLLM
from core.config import API_PORT
```

### 1.5 No Wildcard Imports

```python
# ❌ WRONG
from core.llm import *

# ✅ CORRECT
from core.llm.base import BaseLLM
```

### 1.6 Context Managers

```python
# ✅ CORRECT
with open(file_path, 'r') as f:
    content = f.read()

# ❌ WRONG
f = open(file_path, 'r')
content = f.read()
f.close()
```

---

## 2. Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | `snake_case.py` | `vector_store.py` |
| Classes | `PascalCase` | `FAISSVectorStore` |
| Functions | `snake_case` | `get_task_status` |
| Variables | `snake_case` | `context_id`, `memory_path` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_WORKERS`, `API_PORT` |
| Private | `_prefix` | `_cache`, `_internal` |

### 2.1 Class Naming

```python
class BaseLLM:                    # Abstract/base classes
class OllamaAdapter:              # Adapters (runtime name + type)
class FAISSVectorStore:           # Concrete implementations
class TaskManager:                # Manager/Service classes
```

### 2.2 Function Naming

```python
# Getters/setters
def get_model(self) -> str: ...
def set_model(self, model: str): ...

# Boolean checks
def is_connected(self) -> bool: ...

# Actions
def generate(self, prompt: str) -> str: ...
def validate_connectivity(self) -> bool: ...
```

---

## 3. File Organization

### 3.1 Module Structure

```
core/llm/
├── base.py              # Abstract base class
└── adapters/
    └── ollama.py        # One adapter per file
```

### 3.2 __init__.py Exports

```python
from core.llm.base import BaseLLM
from core.llm.adapters.ollama import OllamaAdapter

__all__ = ["BaseLLM", "OllamaAdapter"]
```

---

## 4. API Design Conventions

### 4.1 Endpoint Naming

| Operation | Pattern | Example |
|-----------|---------|---------|
| Create | `POST /resource` | `POST /api/v1/memory/add` |
| Read | `GET /resource` | `GET /api/v1/tasks/{task_id}` |
| Delete | `DELETE /resource` | `DELETE /api/v1/threads/{id}` |
| List | `GET /resources` | `GET /api/v1/threads` |

### 4.2 Error Responses

```python
# Validation error
raise HTTPException(status_code=400, detail="Invalid context_id")

# Not found
raise HTTPException(status_code=404, detail="Task not found")

# Server error
raise HTTPException(status_code=500, detail=str(error))
```

---

## 5. Logging Conventions

### 5.1 Logger Setup

```python
import logging
logger = logging.getLogger(__name__)
```

### 5.2 Log Levels

| Level | Use For |
|-------|---------|
| DEBUG | Detailed debugging info |
| INFO | General information |
| WARNING | Potential issues |
| ERROR | Failures that need attention |
| CRITICAL | System failures |

### 5.3 Logging Format

```python
# ✅ CORRECT - Include context
logger.info(f"Processing request for context_id={context_id}")
logger.warning(f"Empty embedding for text length={len(text)}")
logger.error(f"Failed to process {task_id}: {type(e).__name__}: {e}")

# ❌ WRONG - No print in production
print(f"Processing file: {file_path}")
```

### 5.4 Log Prefixes

```python
# Component-specific prefixes for filtering
logger.info(f"[API] Chat request received")
logger.info(f"[RAG] Searching memory for context_id={context_id}")
logger.error(f"[LLM] Connection failed to Ollama")
```

---

## 6. Exception Handling

### 6.1 Specific Exceptions

```python
# ✅ CORRECT
try:
    result = risky_operation()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except requests.ConnectionError:
    raise HTTPException(status_code=503, detail="Service unavailable")

# ❌ WRONG - Silent swallowing
try:
    result = risky_operation()
except Exception:
    pass  # FORBIDDEN
```

### 6.2 Custom Exceptions

```python
class CodelyError(Exception):
    """Base exception for Codely."""
    pass

class LLMConnectionError(CodelyError):
    """Raised when LLM connection fails."""
    pass
```

---

## 7. Git Conventions

### 7.1 Commit Messages

```
<type>(<scope>): <subject>

<body>
```

**Types**: feat | fix | docs | refactor | test | chore

**Examples**:
```
feat(llm): add session isolation to Ollama adapter
fix(memory): resolve thread contamination bug
docs(api): update endpoint documentation
```

### 7.2 Branch Naming

```
feature/feature-name
bugfix/issue-description
hotfix/critical-fix
docs/documentation
```

---

## 8. Documentation Standards

### 8.1 Docstring Format (Google Style)

```python
def function(param1: str, param2: int = 0) -> Dict[str, Any]:
    """
    Brief description.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2. Defaults to 0.

    Returns:
        Description of return value.

    Raises:
        ValueError: When param1 is invalid.
        RuntimeError: When operation fails.

    Example:
        >>> result = function("test")
    """
```

---

## 8. Phase 3 Module Conventions

### 8.1 FileWrite Module
- Always validate paths against workspace root
- Use `_resolve_safe_path()` for path safety
- Log all write operations with file size and line count
- Support both `write` and `append` modes

### 8.2 SandboxExec Module
- Validate commands against blocked patterns list
- Enforce timeout limits (max 120s)
- Capture and truncate output (50KB limit per stream)
- Use `CREATE_NO_WINDOW` on Windows
- Never allow delete/move/rename commands without explicit confirmation

### 8.3 TestGen Module
- Auto-detect language from file extension
- Support pytest, unittest, and Jest frameworks
- Generate LLM prompts, not actual test files
- Include run instructions and framework config

### 8.4 Tool Permission Model
- `read` - No approval needed (TestGen)
- `write` - User approval required (FileWrite)
- `execute` - User approval required (SandboxExec)
- `external` - User approval required (WebSearch)

---
## 9. Frontend Conventions

### 9.1 localStorage Safety
- Functions that write to `localStorage` MUST be wrapped in try/catch to handle QuotaExceededError or disabled storage

### 9.2 DOM-First Rendering
- DOM rendering operations (`appendChild`, `innerHTML`, `insertAdjacentHTML`) MUST happen BEFORE side-effects (`localStorage.setItem`, `fetch`)
- This ensures the user sees UI updates even if a side-effect fails

### 9.3 Thread Name Source
- Thread name is sourced from server response (`t.name`), not from localStorage
- `selectThread()` is `async` — it fetches past messages from the messages endpoint

### 9.4 Event Handler Definitions
- All `onclick` handlers referenced in HTML must have corresponding function definitions in JavaScript
- No dangling HTML event attributes pointing to undefined functions

### 9.5 DOM Element References
- DOM element IDs must be referenced via `document.getElementById()` with null checks
- Never assume an element exists — always guard against null

---

## 10. Code Review Checklist

Before committing any code:

- [ ] Type hints on all functions
- [ ] Docstrings on public methods
- [ ] No hardcoded values (use config.py)
- [ ] No wildcard imports
- [ ] Line length < 100
- [ ] No silent exceptions
- [ ] All errors logged
- [ ] Thread isolation verified
- [ ] Documentation updated

---

**Document Version**: 0.7.0
**Enforcement**: STRICT
