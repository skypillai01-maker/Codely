# STRICT RULES CHECKLIST (v0.7.0)

> **Living Document** | Last Updated: 2026-07-18
> **Enforcement**: MANDATORY - Every rule here comes from a real bug/mistake
> **Philosophy**: "Treat every mistake as a rule, correct once, never repeat!"

---

## ⚠️ CRITICAL RULES - VIOLATION = HARD STOP

### Rule #1: USER-SPECIFIC MEMORY (From Bug Fix)
**MISTAKE**: Used global `memory` instead of user-specific `FAISSVectorStore(user_id=...)`
**RULE**: Always use `get_memory_for_user(user_id)` for user operations
```python
# ❌ WRONG - Global memory, no user isolation
memory.add(context_id, text, metadata)

# ✅ CORRECT - User-specific memory
user_memory = get_memory_for_user(user["user_id"])
user_memory.add(context_id, text, metadata)
```

### Rule #2: BACKGROUND TASK USER_ID (From Bug Fix)
**MISTAKE**: Background task `process_file_ingestion` didn't receive `user_id`
**RULE**: All background tasks requiring user memory MUST receive `user_id` as first parameter
```python
# ❌ WRONG - No user_id in background task
task_id = task_manager.submit(process_file_ingestion, context_id, file_path, filename)

# ✅ CORRECT - Pass user_id first
task_id = task_manager.submit(process_file_ingestion, user["user_id"], context_id, file_path, filename)

# Then in the function:
def process_file_ingestion(user_id: str, context_id: str, file_path: str, filename: str):
    user_memory = FAISSVectorStore(embed_adapter=embed_adapter, user_id=user_id)
```

### Rule #3: HNSW INDEX ONLY (From Implementation)
**MISTAKE**: Used `IndexFlatL2` (brute-force O(N)) instead of `IndexHNSWFlat` (O(log N))
**RULE**: Always use HNSW for production vector search, never brute-force
```python
# ❌ WRONG - Brute force, slow for large datasets
index = faiss.IndexFlatL2(dimension)

# ✅ CORRECT - HNSW, fast O(log N) search
index = faiss.IndexHNSWFlat(dimension, HNSW_M)
index.hnsw.efConstruction = HNSW_EF_CONSTRUCTION
index.hnsw.efSearch = HNSW_EF_SEARCH
```

### Rule #4: CHUNKING MANDATORY (From Implementation)
**MISTAKE**: Added entire documents as single vectors (terrible RAG performance)
**RULE**: Always chunk text before embedding, never embed full documents
```python
# ❌ WRONG - Single vector for entire document
embedding = embed_adapter.embed(full_document_text)
index.add(np.array([embedding]))

# ✅ CORRECT - Chunk first, then embed each chunk
chunks = self._split_text(full_document_text)  # Split into CHUNK_SIZE pieces
for chunk in chunks:
    embedding = embed_adapter.embed(chunk)
    index.add(np.array([embedding]))
```

### Rule #5: DOCUMENT METADATA STRUCTURE (From Implementation)
**MISTAKE**: No document tracking, couldn't delete by document
**RULE**: All ingested documents MUST have metadata with `doc_id`, `source`, `timestamp`
```python
# ❌ WRONG - No document tracking
metadata = {"source": filename}

# ✅ CORRECT - Full document metadata
import hashlib
doc_id = hashlib.md5(f"{filename}{len(content)}".encode()).hexdigest()[:8]
metadata = {
    "source": filename,
    "doc_id": doc_id,
    "timestamp": datetime.now().isoformat()
}
```

### Rule #6: NO SILENT EXCEPTIONS (From Previous Bug)
**MISTAKE**: `except Exception: pass` hid critical errors
**RULE**: Every except block MUST log the error with context
```python
# ❌ WRONG - Silent exception
try:
    result = operation()
except Exception:
    pass

# ✅ CORRECT - Log with context
try:
    result = operation()
except Exception as e:
    logger.error(f"Operation failed for context_id={context_id}: {type(e).__name__}: {e}")
    raise  # or return safe default
```

### Rule #7: HNSW CONSTANTS CONFIGURATION (From Implementation)
**MISTAKE**: Hardcoded HNSW parameters scattered in code
**RULE**: Define HNSW parameters as module-level constants in `vector_store.py`
```python
# ✅ CORRECT - In vector_store.py, after imports:
HNSW_M = 32  # Number of bi-directional links per node
HNSW_EF_CONSTRUCTION = 200  # Build-time search width
HNSW_EF_SEARCH = 50  # Query-time search width

CHUNK_SIZE = 1000  # Text chunk size for embedding
CHUNK_OVERLAP = 200  # Overlap between chunks
```

### Rule #8: IMPORT ORGANIZATION (From Syntax Fix)
**MISTAKE**: Missing `import hashlib`, `import numpy` in files that use them
**RULE**: All imports used in a file MUST be at the top of the file
```python
# ✅ CORRECT - All imports at top
import os
import faiss
import numpy as np
import pickle
import logging
import hashlib  # Needed for doc_id generation
from typing import List, Dict, Any, Optional
```

### Rule #9: DELETE OPERATION REBUILD INDEX (From Implementation)
**MISTAKE**: Tried to delete from HNSW index (not supported directly)
**RULE**: To delete from HNSW, rebuild index with only kept vectors
```python
# ✅ CORRECT - Rebuild index without deleted chunks
kept_metadata = [m for m in metadata if m["metadata"].get("doc_id") != doc_id]
new_index = faiss.IndexHNSWFlat(dimension, HNSW_M)
for entry in kept_metadata:
    idx = metadata.index(entry)
    vec = old_index.reconstruct(idx)
    new_index.add(np.array([vec]))
```

### Rule #10: STRING FORMATTING (From Syntax Error)
**MISTAKE**: `f"text {var}"` with smart quotes `""` instead of straight quotes `""`
**RULE**: Always use straight quotes for Python strings, never smart/curly quotes
```python
# ❌ WRONG - Smart quotes (causes SyntaxError)
logger.info(f"Processing {context_id}")  # This is actually OK, but don't use " "

# ❌ WRONG - Curly braces in f-string without proper escaping
# ✅ CORRECT - Straight quotes, proper f-string syntax
logger.info(f"Processing context_id={context_id}")
```

### Rule #11: DOM VARIABLE DECLARATION (From Bug Fix 2026-07-18)
**MISTAKE**: Used `threadList` DOM reference in JavaScript before declaring it with `let`/`const`
**RULE**: Never rely on implicit globals for DOM elements — use `document.getElementById()` or explicit `let`/`const`
```javascript
// ❌ WRONG - Implicit global (ReferenceError when element missing)
function refreshThreadList() {
    threadList.innerHTML = "";  // ReferenceError: threadList is not defined
}

// ✅ CORRECT - Explicit DOM lookup
const threadList = document.getElementById("threadList");
function refreshThreadList() {
    if (threadList) threadList.innerHTML = "";
}
```

### Rule #12: CONVERSATION MUST BE SAVED TO MEMORY (From Bug Fix 2026-07-18)
**MISTAKE**: Chat endpoints never called `rag.learn()` after generating a response
**RULE**: Every chat endpoint MUST save the Q&A pair to FAISS memory after generation
```python
# ✅ CORRECT - Save conversation to memory
result = rag.generate_with_context(context_id=context_id, prompt=prompt, ...)
conversation = f"User: {prompt}\n\nAssistant: {result['response']}"
rag.learn(context_id, conversation, {"type": "conversation", "mode": mode})
```

### Rule #13: EMBEDDING MUST HAVE FALLBACK (From Bug Fix 2026-07-18)
**MISTAKE**: `OllamaAdapter.embed()` only called `/api/embeddings` — failed on Ollama 0.30.6+
**RULE**: Always provide a fallback embedding method that works without external dependencies
```python
# ✅ CORRECT - Try Ollama first, fall back to numpy hash embedding
def embed(self, text):
    try:
        return self._ollama_embed(text)
    except Exception:
        return self._fallback_embed(text)  # zero-dependency numpy fallback
```

### Rule #14: ONLY SHOW THREADS WITH CONTENT (From Bug Fix 2026-07-18)
**MISTAKE**: `/api/v1/threads` returned every context directory including empty ones
**RULE**: Filter threads by `entries > 0` before returning them in the thread list
```python
# ✅ CORRECT - Skip empty threads
threads = []
for c in store.list_contexts():
    stats = store.get_stats(c)
    if stats.get("entries", 0) > 0:
        threads.append({"id": c})
return {"threads": threads}
```

### Rule #15: RENDER BEFORE LOCALSTORAGE WRITE (From Bug Fix 2026-07-18)
**MISTAKE**: `createThread()` called `saveThreadMeta()` (localStorage.setItem) before `renderThreadList()`. If localStorage throws (quota reached, private browsing, disabled storage), the function aborts before the sidebar renders.
**RULE**: Always render the DOM first, then perform side-effects with try/catch
```javascript
// ❌ WRONG - localStorage write can abort rendering
threads.unshift(thread);
saveThreadMeta();       // May throw!
renderThreadList();     // Never reached
selectThread(thread.id); // Never reached

// ✅ CORRECT - Render first, side-effect safely
threads.unshift(thread);
renderThreadList();
selectThread(thread.id);
try { saveThreadMeta(); } catch(e) { console.warn(e); }
```

### Rule #16: SERVER-SIDE THREAD NAME (From Bug Fix 2026-07-18)
**MISTAKE**: Thread names stored only in localStorage. After cache clear or device switch, threads showed truncated garbage IDs.
**RULE**: Always derive a human-readable thread name from the first FAISS entry's text on the server side
```python
# get_stats() MUST return a name derived from FAISS metadata
def get_stats(self, context_id):
    if entries > 0:
        first_text = metadata[0]["text"]  # "User: Say hello\n\nAssistant: Hello!"
        name = first_text.replace("User: ", "").split("\n")[0][:60]
    return {"name": name, "entries": entries}
```

### Rule #17: LOAD PAST MESSAGES FROM SERVER (From Bug Fix 2026-07-18)
**MISTAKE**: Server-loaded threads had `messages: []`. Past conversation text was invisible.
**RULE**: Provide a server endpoint that reads FAISS metadata and returns parsed messages. Frontend fetches messages when selecting a thread.
```python
# Server endpoint
@app.get("/api/v1/threads/{context_id}/messages")
async def get_thread_messages(context_id, current_user):
    store = get_memory_store(current_user["user_id"])
    messages = store.get_messages(context_id)  # reads metadata.pkl
    return {"messages": messages}

# Frontend - async selectThread
async function selectThread(threadId) {
    currentThread = threads.find(t => t.id === threadId);
    if (currentThread.messages.length === 0 && currentThread.entries > 0) {
        const resp = await fetch(`/api/v1/threads/${id}/messages`);
        currentThread.messages = (await resp.json()).messages || [];
    }
    renderMessages();
}
```

---

## 📋 PRE-COMMIT CHECKLIST (Must Pass All)

### Memory Operations
- [ ] Using `get_memory_for_user(user_id)` not global `memory`
- [ ] Background tasks receive `user_id` as first parameter
- [ ] User memory created with `FAISSVectorStore(user_id=user_id)`

### Vector Store
- [ ] Using `IndexHNSWFlat` not `IndexFlatL2`
- [ ] HNSW parameters set (`efConstruction`, `efSearch`)
- [ ] Text chunked before embedding (`_split_text()` called)
- [ ] Chunk size/overlap matches constants (`CHUNK_SIZE`, `CHUNK_OVERLAP`)

### Document Management
- [ ] Ingested documents have `doc_id` in metadata
- [ ] Metadata includes `source`, `doc_id`, `timestamp`
- [ ] `list_documents` endpoint returns proper structure
- [ ] Delete endpoint rebuilds index correctly

### Conversation Memory
- [ ] Chat endpoint saves Q&A to FAISS via `rag.learn()` after generation
- [ ] Chat-with-files endpoint saves Q&A to FAISS via `rag.learn()` after generation
- [ ] Conversation saved as `"User: {prompt}\n\nAssistant: {response}"` with metadata

### Embedding Fallback
- [ ] `embed()` method has fallback when Ollama API fails
- [ ] Fallback does not depend on external packages (numpy only)
- [ ] Embedding dimension is consistent (768)

### Error Handling
- [ ] No `except Exception: pass` anywhere
- [ ] All except blocks log with `logger.error()`
- [ ] Error messages include context (context_id, user_id, etc.)

### Imports
- [ ] All needed imports at top of file
- [ ] `hashlib` imported when generating doc_id
- [ ] `numpy as np` imported when using FAISS operations
- [ ] No wildcard imports (`from X import *`)

### Thread Listing
- [ ] `/api/v1/threads` filters out contexts with 0 entries
- [ ] Stats checked before adding to response (`get_stats(context_id).entries > 0`)

### Frontend (Web UI)
- [ ] DOM elements accessed via `document.getElementById()`, not implicit globals
- [ ] All variables declared with `let`/`const` before use
- [ ] Null/undefined checks before accessing DOM element properties
- [ ] `createThread()` calls `renderThreadList()` + `selectThread()` before `saveThreadMeta()`
- [ ] `saveThreadMeta()` wrapped in try/catch in every calling function
- [ ] Thread names sourced from server (`t.name`), not localStorage
- [ ] `selectThread()` is `async` — fetches past messages instead of showing empty chat
- [ ] `clearMemory()` and `renameThread()` functions exist (not just onclick attributes)

### Syntax
- [ ] Straight quotes for all strings
- [ ] Proper f-string syntax (`f"text {var}"`)
- [ ] Type hints on all function parameters and returns

---

## 🚨 KNOWN BUG PATTERNS TO AVOID

### Pattern #1: Cross-User Data Leak
**Symptom**: User A sees User B's documents
**Cause**: Using global memory instead of user-specific
**Fix**: Always use `get_memory_for_user(user_id)`

### Pattern #2: Background Task User Context Loss
**Symptom**: Background task uses wrong user's memory
**Cause**: `user_id` not passed to background task
**Fix**: Pass `user_id` as first param to `task_manager.submit()`

### Pattern #3: Slow Vector Search
**Symptom**: Search takes forever with many documents
**Cause**: Using `IndexFlatL2` instead of `IndexHNSWFlat`
**Fix**: Use HNSW with proper `M`, `efConstruction`, `efSearch`

### Pattern #4: Poor RAG Performance
**Symptom**: LLM gets irrelevant context
**Cause**: Full documents embedded as single vectors
**Fix**: Chunk documents with `CHUNK_SIZE` and `CHUNK_OVERLAP`

### Pattern #5: Orphaned Documents
**Symptom**: Can't delete or track documents
**Cause**: No `doc_id` in metadata
**Fix**: Always generate and store `doc_id` with metadata

### Pattern #6: Undefined DOM Variable Reference
**Symptom**: `ReferenceError: threadList is not defined` in Web UI
**Cause**: Frontend code references DOM elements as undeclared globals
**Fix**: Always use `document.getElementById("id")` and declare with `const`/`let`

### Pattern #7: Lost Conversation Memory
**Symptom**: Chat history vanishes after server restart
**Cause**: Chat endpoints never saved Q&A pairs to FAISS memory via `rag.learn()`
**Fix**: Always call `rag.learn()` after `rag.generate_with_context()` in every chat endpoint

### Pattern #8: Silent Embedding Failure
**Symptom**: FAISS memory saves fail silently — index stays at 0 entries
**Cause**: Ollama `/api/embeddings` fails but exception is swallowed; no fallback
**Fix**: Use hash-based numpy embedding fallback when Ollama embedding API is unavailable

### Pattern #9: Empty Threads in Sidebar
**Symptom**: Threads with "Empty chat" label appear in the sidebar
**Cause**: `/api/v1/threads` returns context directories even when they have 0 FAISS entries
**Fix**: Filter threads by `entries > 0` in the list endpoint

### Pattern #10: Empty Sidebar After Restart
**Symptom**: Sidebar completely empty after re-login — no threads displayed, "New Chat" appears
**Cause**: `createThread()` calls `saveThreadMeta()` (localStorage.setItem) BEFORE `renderThreadList()`. If localStorage throws (quota/private mode), the entire function aborts before rendering.
**Fix**: Render thread list and select the thread FIRST, then try/catch localStorage write.

### Pattern #11: Unrecognizable Thread Names
**Symptom**: Threads show as truncated IDs like "thread_a1b2c3d4e5f6…" instead of meaningful names
**Cause**: Thread name stored only in localStorage. After cache clear, no server-side name exists.
**Fix**: Derive thread name from first FAISS entry's text. `get_stats()` includes a `name` field.

### Pattern #12: Empty Chat Area for Past Threads
**Symptom**: Clicking a past thread shows blank chat window — no messages displayed
**Cause**: `loadThreads()` sets `messages: []` for server-loaded threads. No endpoint returns message text.
**Fix**: Add `GET /api/v1/threads/{id}/messages` endpoint that reads FAISS metadata.pkl and parses user/ai pairs. Frontend fetches messages on thread selection.

---

## 📖 STRICT CODING STANDARDS

### Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| HNSW Constants | `UPPER_SNAKE_CASE` | `HNSW_M`, `CHUNK_SIZE` |
| Function Parameters | `snake_case` | `context_id`, `user_id` |
| Background Tasks | `snake_case` | `process_file_ingestion` |

### File Structure
```
core/memory/vector_store.py
├── HNSW_* constants (top of file)
├── CHUNK_* constants (top of file)
├── FAISSVectorStore class
│   ├── __init__() - Initialize with user_id
│   ├── _split_text() - Chunking logic
│   ├── add() - Chunk before embed
│   ├── search() - Use HNSW index
│   └── merge() - Rebuild HNSW index
```

### API Endpoints for Documents
| Method | Endpoint | Purpose | Rule |
|--------|----------|---------|------|
| `POST` | `/api/v1/ingest/file` | Ingest file | Background task gets `user_id` |
| `GET` | `/api/v1/documents` | List documents | Use `user_memory`, not `memory` |
| `DELETE` | `/api/v1/documents/{doc_id}` | Delete document | Rebuild HNSW index |

---

**Document Version**: 0.7.0  
**Last Updated**: 2026-07-18  
**Enforcement**: ALL code changes MUST pass this checklist  
**Violation Consequence**: Code rejected, bug WILL reoccur
