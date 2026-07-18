# STRICT RULES CHECKLIST (v0.6.0)

> **Living Document** | Last Updated: 2026-05-03
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

### Error Handling
- [ ] No `except Exception: pass` anywhere
- [ ] All except blocks log with `logger.error()`
- [ ] Error messages include context (context_id, user_id, etc.)

### Imports
- [ ] All needed imports at top of file
- [ ] `hashlib` imported when generating doc_id
- [ ] `numpy as np` imported when using FAISS operations
- [ ] No wildcard imports (`from X import *`)

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

**Document Version**: 0.6.0  
**Last Updated**: 2026-05-03  
**Enforcement**: ALL code changes MUST pass this checklist  
**Violation Consequence**: Code rejected, bug WILL reoccur
