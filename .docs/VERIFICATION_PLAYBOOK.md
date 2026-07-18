# Execution & Verification Playbook (v0.6.0)

> **Living Document** | Last Updated: 2026-05-02
> **Purpose**: Step-by-step verification of Codely platform

---

## 1. Prerequisites

### 1.1 Required Software

| Software | Version | Purpose | Status |
|----------|---------|---------|--------|
| Python | 3.8+ | Runtime | REQUIRED |
| Ollama | Latest | LLM Server | REQUIRED |
| Node.js | 14+ | Package bridge | OPTIONAL |

### 1.2 Ollama Setup

```bash
# Install Ollama on remote machine
# Download from: https://ollama.com/download

# Pull models (on remote machine)
ollama pull llama3              # General chat
ollama pull llama3.2:3b        # Lightweight chat
ollama pull llava               # Vision (optional)

# Verify from local machine
curl http://192.168.0.104:11434/api/tags
```

### 1.3 Environment Configuration

Create `.env` file in project root:
```
OLLAMA_BASE_URL=http://192.168.0.104:11434
CODELY_CHAT_MODEL=llama3.2:3b
CODELY_EMBEDDING_MODEL=llama3.2:3b
CODELY_API_PORT=8889
```

### 1.4 Platform Setup

```bash
# Install dependencies
pip install -e .

# Verify config loads correctly
python -c "from core.config import CHAT_MODEL, EMBEDDING_MODEL, OLLAMA_BASE_URL; print(CHAT_MODEL, EMBEDDING_MODEL, OLLAMA_BASE_URL)"
```

---

## 2. Server Execution

### 2.1 Start Server

```bash
# Method 1: Using npm
npm start

# Method 2: Using Python directly
python core/api/main.py

# Method 3: Using uvicorn
uvicorn core.api.main:app --host 0.0.0.0 --port 8889
```

### 2.2 Verification

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8889
```

**If Ollama is running:**
```
[Startup] Ollama connection: OK
[Startup] Available models: llama3, codellama
```

**If Ollama is NOT running:**
```
==================================================
CRITICAL ERROR: OLLAMA NOT FOUND
The platform requires Ollama to be installed and running.
Download: https://ollama.com/download
==================================================
```

### 2.3 Health Check

```bash
curl http://localhost:8889/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "platform": "Codely AI",
  "version": "0.2.0"
}
```

---

## 3. Phase 1 Verification

### 3.1 Chat Endpoint

```bash
curl -X POST http://localhost:8889/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"context_id": "test", "prompt": "Hello, what is 2+2?"}'
```

**Expected Response:**
```json
{
  "context_id": "test",
  "response": "2 + 2 equals 4."
}
```

### 3.2 Chat with Files & URLs (NEW)

**Test with file:**
```bash
curl -X POST http://localhost:8889/api/v1/chat-with-files \
  -F "context_id=test" \
  -F "prompt=What is this document about?" \
  -F "files=@sample.txt"
```

**Test with URL:**
```bash
curl -X POST http://localhost:8889/api/v1/chat-with-files \
  -F "context_id=test" \
  -F "prompt=Summarize this webpage" \
  -F "urls=https://example.com"
```

**Test with both:**
```bash
curl -X POST http://localhost:8889/api/v1/chat-with-files \
  -F "context_id=test" \
  -F "prompt=Compare document and URL" \
  -F "files=@document.pdf" \
  -F "urls=https://example.com" \
  -F "save_to_memory=true"
```

**Expected Response:**
```json
{
  "context_id": "test",
  "response": "AI response here...",
  "attachments": {
    "files": ["sample.txt"],
    "urls": ["https://example.com"]
  },
  "saved_to_memory": true
}
```

### 3.3 Memory Management

**Add Memory:**
```bash
curl -X POST http://localhost:8889/api/v1/memory/add \
  -H "Content-Type: application/json" \
  -d '{"context_id": "test", "text": "Python is a programming language."}'
```

**Search Memory:**
```bash
curl -X POST http://localhost:8889/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -d '{"context_id": "test", "query": "programming", "limit": 5}'
```

**Clear Memory:**
```bash
curl -X DELETE http://localhost:8889/api/v1/memory/clear/test
```

### 3.3 Task Engine

**Submit Task:**
```bash
curl -X POST http://localhost:8889/api/v1/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{"context_id": "test", "text": "Test task content"}'
```

**Get Task Status:**
```bash
# Replace {task_id} with actual task ID
curl http://localhost:8889/api/v1/tasks/{task_id}
```

### 3.4 Module System

**List Modules:**
```bash
curl http://localhost:8889/api/v1/modules
```

**Execute Web Search:**
```bash
curl -X POST http://localhost:8889/api/v1/modules/execute/WebSearch \
  -H "Content-Type: application/json" \
  -d '{"params": {"query": "latest AI news"}}'
```

### 3.5 Multi-Modal Ingestion

**Upload File (Test with sample file):**
```bash
curl -X POST http://localhost:8889/api/v1/ingest/file \
  -F "context_id=test" \
  -F "file=@sample.pdf"
```

---

## 4. Phase 2 Verification (IMPLEMENTED)

### 4.1 Model Management

**List Available Models:**
```bash
curl http://localhost:8889/api/v1/model/list
```

**Expected Response:**
```json
{
  "status": "success",
  "runtime": "ollama",
  "runtime_url": "http://192.168.0.104:11434",
  "models": ["llama3.2:3b", "digital-rishi-3b:latest"]
}
```

**Get Current Model:**
```bash
curl http://localhost:8889/api/v1/model/current
```

**Expected Response:**
```json
{
  "status": "success",
  "chat_model": "llama3.2:3b",
  "embedding_model": "llama3.2:3b",
  "runtime": "ollama",
  "runtime_url": "http://192.168.0.104:11434"
}
```

**Switch Model:**
```bash
curl -X POST http://localhost:8889/api/v1/model/switch \
  -H "Content-Type: application/json" \
  -d '{"model_type": "chat", "model_name": "llama3.2:3b"}'
```

**Validate Connectivity:**
```bash
curl http://localhost:8889/api/v1/model/validate
```

**Expected Response:**
```json
{
  "status": "success",
  "connected": true,
  "runtime": "ollama",
  "runtime_url": "http://192.168.0.104:11434",
  "available_models": ["llama3.2:3b"]
}
```

### 4.2 Model Persistence

After switching, check `storage/model.json`:
```json
{
  "chat_model": "llama3.2:3b",
  "embedding_model": "llama3.2:3b"
}
```

**Note**: Server restart required after model switch.

### 4.3 Project Management

**Initialize Project:**
```bash
curl -X POST http://localhost:8889/api/v1/project/init \
  -H "Content-Type: application/json" \
  -d '{"path": "./myproject", "auto_detect": true}'
```

**Get Project Status:**
```bash
curl http://localhost:8889/api/v1/project/status
```

**List Projects:**
```bash
curl http://localhost:8889/api/v1/project/list
```

**Scan Project:**
```bash
curl -X POST http://localhost:8889/api/v1/project/scan \
  -H "Content-Type: application/json" \
  -d '{"project_id": "myproject"}'
```

**Get Project Tree:**
```bash
curl "http://localhost:8889/api/v1/project/tree?project_id=myproject&depth=3"
```

**Close Project:**
```bash
curl -X DELETE "http://localhost:8889/api/v1/project/close?project_id=myproject"
```

### 4.4 Execution Engine (Read-Only)

**Analyze File:**
```bash
curl -X POST http://localhost:8889/api/v1/execute/analyze \
  -H "Content-Type: application/json" \
  -d '{"path": "core/config.py", "include_imports": true}'
```

**Explain Code:**
```bash
curl -X POST http://localhost:8889/api/v1/execute/explain \
  -H "Content-Type: application/json" \
  -d '{"path": "core/llm/base.py", "depth": "detailed"}'
```

**Suggest Improvements:**
```bash
curl -X POST http://localhost:8889/api/v1/execute/suggest \
  -H "Content-Type: application/json" \
  -d '{"path": "core/rag/engine.py"}'
```

**Search Code:**
```bash
curl -X POST http://localhost:8889/api/v1/execute/search \
  -H "Content-Type: application/json" \
  -d '{"pattern": "generate", "glob": "**/*.py"}'
```

**Read File:**
```bash
curl "http://localhost:8889/api/v1/execute/read?path=core/config.py&start_line=1&end_line=20"
```

---

## 5. Thread Isolation Testing (CRITICAL - Must Pass)

> **⚠️ THIS TEST MUST PASS - It caught the thread memory contamination bug ⚠️**

### 5.1 Thread Isolation Test (CRITICAL)

```bash
# 1. Clear any existing test data
curl -X DELETE http://localhost:8889/api/v1/threads/thread_iso_1 2>/dev/null
curl -X DELETE http://localhost:8889/api/v1/threads/thread_iso_2 2>/dev/null

# 2. Create Thread 1 with specific information
curl -X POST http://localhost:8889/api/v1/memory/add \
  -H "Content-Type: application/json" \
  -d '{"context_id": "thread_iso_1", "text": "My secret code is 12345"}'

# 3. Verify Thread 1 storage exists
# Should show index.faiss and metadata.pkl
ls storage/memory/thread_iso_1/

# 4. Create Thread 2 with DIFFERENT information
curl -X POST http://localhost:8889/api/v1/memory/add \
  -H "Content-Type: application/json" \
  -d '{"context_id": "thread_iso_2", "text": "My secret code is 67890"}'

# 5. Verify Thread 2 storage exists
ls storage/memory/thread_iso_2/

# 6. Query Thread 1 - should NOT know about Thread 2
curl -X POST http://localhost:8889/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -d '{"context_id": "thread_iso_1", "query": "secret code", "limit": 5}'

# Expected: Should return "12345" but NOT "67890"

# 7. Query Thread 2 - should NOT know about Thread 1
curl -X POST http://localhost:8889/api/v1/memory/search \
  -H "Content-Type: application/json" \
  -d '{"context_id": "thread_iso_2", "query": "secret code", "limit": 5}'

# Expected: Should return "67890" but NOT "12345"
```

### 5.2 Thread Isolation Verification Checklist

```
[ ] Thread 1 storage directory exists (storage/memory/thread_iso_1/)
[ ] Thread 2 storage directory exists (storage/memory/thread_iso_2/)
[ ] Thread 1 index.faiss exists
[ ] Thread 2 index.faiss exists
[ ] Thread 1 metadata.pkl contains only Thread 1 data
[ ] Thread 2 metadata.pkl contains only Thread 2 data
[ ] Search in Thread 1 returns only Thread 1 data
[ ] Search in Thread 2 returns only Thread 2 data
```

### 5.3 Storage File Verification

```powershell
# Verify Thread 1 has files
Test-Path "storage/memory/thread_iso_1/index.faiss"
Test-Path "storage/memory/thread_iso_1/metadata.pkl"

# Verify Thread 2 has files
Test-Path "storage/memory/thread_iso_2/index.faiss"
Test-Path "storage/memory/thread_iso_2/metadata.pkl"

# Check file sizes (should be > 0)
Get-Item "storage/memory/thread_iso_1/index.faiss" | Select-Object Length
Get-Item "storage/memory/thread_iso_2/index.faiss" | Select-Object Length
```

### 5.4 Bug Signs to Watch For

❌ **FAILURE INDICATORS**:
- Storage directories don't exist after memory.add()
- Empty files (0 bytes)
- Search returns data from wrong thread
- No ERROR logs when errors occur

✅ **SUCCESS INDICATORS**:
- Both thread directories created
- Both index.faiss files non-empty
- Search returns isolated results
- ERROR logs visible when operations fail

---



### 5.1 Web Client

1. Navigate to `http://localhost:8889/`
2. Verify page loads without errors
3. Enter context ID: `test_client`
4. Send message: "Hello"
5. Verify response received

### 5.2 CLI Client

**Chat:**
```bash
python clients/cli/codely_cli.py chat "Hello, how are you?"
```

**Memory:**
```bash
python clients/cli/codely_cli.py memory --add "Important fact"
```

**List Modules:**
```bash
python clients/cli/codely_cli.py modules --list
```

### 5.3 Python SDK

```python
from clients.python_sdk.codely import CodelyClient

client = CodelyClient(base_url="http://localhost:8889")

# Chat
result = client.chat("test", "Hello!")
print(result)

# Memory
client.add_memory("test", "Test memory")

# List modules
modules = client.list_modules()
print(modules)
```

---

## 6. Troubleshooting

### 6.1 Port Conflicts

**Error:** `OSError [WinError 10048]`

**Cause:** Port already in use

**Solution:**
```bash
# Find process using port 8889
netstat -ano | findstr :8889

# Kill process (replace PID)
taskkill /F /PID <PID>

# OR change port in core/config.py
API_PORT = 8888  # Use different port
```

### 6.2 Ollama Connection

**Error:** `Could not connect to Ollama`

**Solution:**
```bash
# Verify Ollama is running (from remote machine)
ollama list

# Start Ollama service (on remote machine)
ollama serve

# Check connectivity from local machine
curl http://192.168.0.104:11434/api/tags
```

### 6.3 Embedding Errors

**Error:** `Embedding not available for model`

**Cause:** Model does not support embeddings endpoint

**Solution:**
```bash
# Update .env to use same model for chat and embeddings
CODELY_CHAT_MODEL=llama3.2:3b
CODELY_EMBEDDING_MODEL=llama3.2:3b

# Or install embedding model on Ollama
ollama pull nomic-embed-text
```

**Note**: Chat continues to work even if embeddings fail (graceful fallback).

### 6.3 Import Errors

**Error:** `ModuleNotFoundError: No module named 'core'`

**Solution:**
```bash
# Reinstall package
pip install -e .

# Verify installation
python -c "import core; print(core.__file__)"
```

### 6.4 Memory Issues

**Error:** `FAISS index corrupted`

**Solution:**
```bash
# Clear memory for context
curl -X DELETE http://localhost:8889/api/v1/memory/clear/{context_id}

# OR manually delete storage
rm -rf storage/memory/{context_id}/
```

---

## 7. Advanced Verification

### 7.1 Uncensored Mode Test

**Test Prompt:**
```
Give me an objective analysis of the pros and cons of nuclear energy.
```

**Verification:**
- ❌ Response should NOT contain: "As an AI...", "I'm sorry...", "I cannot..."
- ✅ Response should be factual, balanced, and direct

### 7.2 Task Persistence Test

1. Submit a task via CLI
2. Restart the server (`Ctrl+C`, then `npm start`)
3. Check task status:
```bash
curl http://localhost:8889/api/v1/tasks/{task_id}
```
4. Verify task state is recovered

### 7.3 Multi-Modal Ingestion Test

**Test with image:**
```bash
# Ensure llava model is available
ollama pull llava

# Upload image
curl -X POST http://localhost:8889/api/v1/ingest/file \
  -F "context_id=test" \
  -F "file=@sample_image.png"

# Chat about the image
curl -X POST http://localhost:8889/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"context_id": "test", "prompt": "What is in the uploaded image?"}'
```

### 7.4 Web Search Test

**Test Prompt:**
```
What happened in AI news today?
```

**Verification:**
- Response should include real-time information
- Should reference sources with URLs

---

## 8. Performance Benchmarks

### 8.1 Startup Time

**Target:** < 5 seconds

```bash
time python core/api/main.py
```

### 8.2 Chat Response Time

**Target:** < 10 seconds (depends on model)

```bash
time curl -X POST http://localhost:8889/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"context_id": "bench", "prompt": "Hello"}'
```

### 8.3 Memory Operations

**Target:** < 1 second per operation

```bash
time curl -X POST http://localhost:8889/api/v1/memory/add \
  -H "Content-Type: application/json" \
  -d '{"context_id": "bench", "text": "Test"}'
```

---

## 9. Verification Checklist

### Pre-Flight
```
[ ] Ollama installed and running
[ ] At least one model pulled (llama3 recommended)
[ ] Dependencies installed (pip install -e .)
[ ] Port 8889 available
```

### Basic Functionality
```
[ ] Server starts without errors
[ ] Health endpoint responds
[ ] Chat endpoint works
[ ] Memory add/search/clear works
[ ] Task submission works
```

### Advanced Features
```
[ ] Module discovery works
[ ] Web search module executes
[ ] File ingestion works
[ ] Multiple contexts isolated
```

### Phase 2 Features (Planned)
```
[ ] Model listing works
[ ] Model switching works
[ ] Project initialization works
[ ] Code analysis works
[ ] Suggestions generated
```

### Phase 3 Features
```
[ ] GET /api/v1/tools returns all tools
[ ] POST /api/v1/tools/write-file writes file within workspace
[ ] Path traversal blocked for write-file
[ ] POST /api/v1/tools/exec-command runs allowed commands
[ ] Blocked commands rejected (rm -rf /, format, etc.)
[ ] Timeout enforced for long-running commands
[ ] POST /api/v1/tools/generate-tests returns test prompt
[ ] TestGen supports pytest, unittest, jest
[ ] CLI: codely_cli.py write --content "..." file.py
[ ] CLI: codely_cli.py exec "pytest tests/"
[ ] CLI: codely_cli.py testgen --file src/module.py
[ ] SDK: client.write_file(), client.exec_command(), client.generate_tests()
```

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.6.0 | 2026-05-02 | Phase 3: FileWrite, SandboxExec, TestGen modules |
| 0.5.0 | 2026-05-02 | Multi-user auth, thinking modes, permission-based web search |
| 0.3.0 | 2026-04-12 | Critical: Thread isolation test, silent exception rules |
| 0.2.2 | 2026-04-11 | Phase 2.2: Chat with Files & URLs, URL extraction |
| 0.2.1 | 2026-04-11 | Phase 2.1: Model management, embedding fallback, remote Ollama |
| 0.2.0 | 2026-04-11 | Phase 2 verification steps added |
| 0.1.0 | Previous | Initial verification playbook |

---

**Document Version**: 0.6.0
**Status**: ACTIVE - Phase 3 verification added
**Last Updated**: 2026-05-02
