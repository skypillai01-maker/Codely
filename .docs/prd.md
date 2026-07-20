# prd.md: Codely AI Platform Product Requirements Document

## 1. High-Level Vision
Codely is a local, private, internet-aware RAG AI coding assistant designed for individual developers. It prioritizes user privacy (all data stored locally), developer productivity (write/exec/test generation tools), and multi-modal context (chat with files, URLs, etc.).

## 2. Target User
- **Primary**: Individual software developers who want a local AI assistant without relying on cloud services
- **Secondary**: Hobbyists, students, developers working on sensitive codebases

## 3. Core Value Proposition
- **Privacy First**: 100% local data (no cloud storage, no telemetry)
- **Multi-Modal RAG**: Chat with files (text, PDF, images, Office docs), URLs, code
- **Developer Tools**: Built-in modules for FileWrite, SandboxExec, and TestGen
- **User Isolation**: Multiple users supported, each with their own isolated storage and memory

## 4. Scope Boundaries (MVP)
### IN SCOPE
- Local LLMs via Ollama
- RAG with HNSW vector search
- Email magic link auth
- Chat with files (text, code, basic multi-modal)
- FileWrite (safe file editing)
- SandboxExec (safe command execution)
- TestGen (unit test generation)
- Document management (list, delete documents)
- Basic thread management

### OUT OF SCOPE
- Cloud-based LLMs (OpenAI, Anthropic, etc.) by default (though Ollama adapter could be extended)
- Mobile app
- Multi-tenant SaaS deployment
- Built-in code editor (focus on IDE integration via web UI/CLI/SDK)
- Advanced team collaboration features
