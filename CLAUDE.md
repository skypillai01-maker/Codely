# CLAUDE.md: Coding Style, Tech Stack, and Rules for Codely AI

## 1. Core Principles and Blocklists
- **NO SILENT EXCEPTIONS**: Never use `except Exception: pass`; always log with `logger.error()` including context (user_id, context_id, etc.)
- **NO BRUTE-FORCE VECTOR SEARCH**: Always use FAISS HNSW index with cosine similarity; no exact search unless explicitly required for small datasets
- **NO HARDCODED MODEL NAMES**: All LLM/embedding model config must come from `core/config.py` only; no hardcoding in adapters/rag/etc.
- **USER ISOLATION FIRST**: All data (memory, auth, etc.) must be user-isolated; use `get_memory_for_user(user_id)`
- **NO UNVERIFIED NETWORK REQUESTS**: For any external API calls (Ollama, email, web search), always use timeouts, retries, and error handling

## 2. Tech Stack (NO DEVIATION)
- **Backend Language**: Python 3.12+
- **Web Framework**: FastAPI (async endpoints only where appropriate)
- **Vector DB**: FAISS (HNSW index only)
- **Embeddings**: Ollama default embedding model (configurable via `core/config.py`)
- **LLM Provider**: Ollama (local only)
- **Auth**: Email magic link only
- **Frontend**: Plain HTML/CSS/JS (no frameworks like React/Vue)
- **Package Manager**: pip (requirements.txt)
- **Logging**: Python `logging` module (structured logs, no print statements)

## 3. Testing Commands
- To run the app: `python -m core.api.main` (starts on port 8889)
- No formal test suite yet; manual verification using the web UI and CLI
- Verify changes by:
  1. Starting the server
  2. Using web UI (http://localhost:8889) to test chat, file upload, document management, etc.
  3. Checking the server logs for errors

## 4. File Structure Rules
- Core logic in `core/`
- Modules in `modules/`
- Clients in `clients/`
- All governance files in root or `.docs/` (per user specification)
- Runtime data in `storage/` (gitignored)

## 5. Code Style Conventions
- Use snake_case for variables, functions, file names
- Use type hints for all function parameters and return values
- Write docstrings for all public classes/methods
- Organize imports at top of file: stdlib first, then third-party, then local
- Max line length: 120 characters

## 6. Mandatory Pre-Commit Checks
- Always run `git status` before committing
- Never commit `storage/`, `.env`, or any user-specific data
- Always verify endpoints still work before pushing
