# audit.md: Error Logs, Edge Cases, and Historical Fixes

## 1. Known Quirks
- Ollama 0.30.6+ changed embedding endpoint to `/api/embed` (from `/api/embeddings`); code has fallback logic
- Large file uploads may take time; no progress bar yet but backend logs progress
- In private browsing mode, localStorage may throw quota errors; web UI has try/catch
- Sidebar may be empty on first load if no threads exist; UI shows appropriate message

## 2. Historical Fix Attempts
| Issue | Date | Fix Attempts | Final Fix |
|-------|------|--------------|-----------|
| Silent Exceptions Crashing App | 2026-04-12 | Tried wrapping in generic try/except; failed to catch root cause | Removed silent exceptions, added full error logging with context |
| Sidebar Empty After Restart | 2026-07-18 | Tried clearing localStorage; didn't fix | Changed order to renderThreadList() first, wrap saveThreadMeta() in try/catch |
| Socket Binding Errors | 2026-07-17 | Tried killing hung processes, incrementing port | Centralized network config in core/config.py, default port 8889 |
| Blocking File I/O Freezing App | 2026-07-17 | Tried threading; had race conditions | Implemented async ingestion with TaskManager |

## 3. Error Log Monitoring Checklist
- Always check server logs for errors after any change
- Look for:
  - Exceptions with "user_id" or "context_id" in log message
  - Ollama connection errors
  - File I/O errors
  - Auth token errors
