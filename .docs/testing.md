# testing.md: Test Cases and Verification Workflows

## 1. Manual Verification Checklist
All changes must pass these checks before being considered complete:

### 1.1 Server Starts Up
- Run `python -m core.api.main`; verify server starts on http://localhost:8889
- Check logs for errors; confirm Ollama connection is successful (pre-flight handshake)

### 1.2 Auth Works
- Go to http://localhost:8889/login.html; enter email
- Check logs for magic link (since email service is in-memory only)
- Copy token from logs, go to http://localhost:8889/login.html?token=<token>; verify login redirects to index.html
- Check local storage for token and user ID

### 1.3 Chat Works
- Create a new thread
- Send a simple message (e.g., "hello")
- Verify response is generated, thinking is streamed (if in deep thinking mode)
- Verify conversation appears in sidebar and is persistent after refresh

### 1.4 Document Management Works
- Upload a file (text/code) via the UI
- List documents via GET /api/v1/documents (use browser dev tools to check response)
- Delete a document via DELETE /api/v1/documents/<doc_id>
- Verify document is no longer listed

### 1.5 Modules Work (If Applicable)
- FileWrite: Use FileWrite tool; verify file is edited safely
- SandboxExec: Run a command; verify it executes safely
- TestGen: Generate unit tests; verify they're valid

## 2. Edge Cases to Test
- Empty context
- Large file uploads (>=10MB)
- Multiple users switching back and forth
- Internet down (verify graceful fallback for web search)
- Ollama not running (verify pre-flight check fails with helpful error)

## 3. Log Verification
- Always check server logs after each test
- Look for errors, warnings, or unexpected behavior
- All exceptions should be logged with full context (user_id, context_id, etc.)
