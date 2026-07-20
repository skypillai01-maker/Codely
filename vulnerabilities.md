# vulnerabilities.md: Project-Wide Security Vulnerabilities

## Known Vulnerabilities
| ID | Severity | Description | Mitigation | Status |
|----|----------|-------------|------------|--------|
| VULN-001 | Low | FileWrite module allows writing to any path within workspace root; no validation for sensitive system files | Ensure workspace root is not set to system directories; limit workspace root to project directories only; audit all file write operations | Mitigated |
| VULN-002 | Medium | SandboxExec module allows executing any command in ALLOWED_COMMANDS without further validation; no command whitelist for arguments | Implement argument filtering for sensitive commands; limit command execution to specific use cases; log all commands | In Progress |
| VULN-003 | Low | Added per-email/per-token rate limiting to auth endpoints (request-login and verify) | Use rate limiting middleware; per-resource limits | Mitigated |

## Critical Security Rules (Enforced)
- All user data must be isolated per user (user-scoped storage, memory, etc.)
- Never expose LLM API keys or secrets in logs or frontend
- All network requests must have timeouts and error handling
- No silent exceptions; log all errors with context
- Never commit .env or storage/ files to git
