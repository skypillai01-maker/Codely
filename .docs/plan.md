# plan.md: Sequential Development Phases

## Phase 0: Project Bootstrap (Completed)
- Initialize project structure (core/, modules/, clients/, .docs/)
- Set up basic FastAPI server
- Integrate Ollama for local LLM inference
- Implement minimal FAISS vector store

## Phase 1: Chat + Thread Isolation (Completed)
- Chat UI (ChatGPT-style)
- Thread creation/selection/deletion
- User isolation (per-user memory/storage)
- Magic link authentication
- Session management
- WebSocket/SSE for streaming responses

## Phase 2: RAG + Multi-Modal Ingestion (Completed)
- HNSW vector search
- Text chunking
- File ingestion (text, code, basic multi-modal)
- Web search integration (DuckDuckGo)
- URL ingestion
- Conversation memory persistence (rag.learn())
- Thread message history loading
- Server-generated thread names

## Phase 3: Developer Tools (Completed)
- FileWrite module (safe file editing)
- SandboxExec module (command execution)
- TestGen module (unit test generation)
- API endpoints for modules
- Web UI for module usage

## Phase 4: Document Management + Full Governance (In Progress / Current)
- Document list endpoint
- Document delete endpoint
- Full governance file suite (CLAUDE.md, AGENTS.md, system-instructions.md, prd.md, architecture.md, data_model.md, design.md, plan.md, next-task.md, procedures.md, testing.md, threat_model.md, audit.md, memory.md, chatmem.md, vulnerabilities.md)
- Auth rate limiting
- Filename as source in metadata

## Phase 5: Future Enhancements (Backlog)
- Improve test coverage for modules
- Proper async multi-modal file ingestion (PDF, Office, images)
- SandboxExec argument filtering
- Module integration tests
- Better error handling and retries
- CLI improvements
- Python SDK improvements
