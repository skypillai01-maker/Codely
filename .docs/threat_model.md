# threat_model.md: Security Threats and Protection Measures

## 1. Threat Actors
- **Local User**: Primary user of the system; trusted but needs isolation
- **Malicious Local Actor**: Someone with physical access to the machine (low risk if machine is secure)
- **Remote Attacker**: Network-based attacker (low risk if server is not exposed publicly)

## 2. Threat Vectors
| Vector | Risk | Description | Protection |
|--------|------|-------------|------------|
| Auth Brute Force | Medium | Attacker spams /request-login or /verify endpoints | Per-email/per-token rate limiting (VULN-003 mitigated) |
| Path Traversal | High | Attacker uses FileWrite to write outside workspace root | FileWrite checks for path traversal, restricts to workspace root (VULN-001) |
| Command Injection | High | Attacker injects malicious arguments to SandboxExec | TODO: Implement argument filtering for SandboxExec (VULN-002) |
| Cross-User Data Leak | Critical | User A can access User B's memory/storage | Strict user isolation (all data is scoped to user_id, implemented in vector_store.py) |
| Server Exposure | Medium | Server is exposed to public internet | Use firewall, VPN, or reverse proxy; don't expose port 8889 publicly |

## 3. Critical Data Points to Protect
- User email addresses
- User memory/chat history
- Any files uploaded by user
- Magic link tokens (short-lived, stored securely in auth database)

## 4. Security Hardening Measures
- All user data stored in user-specific directories under storage/
- No secrets committed to git
- No telemetry sent to external servers
- Timeouts and retries for all external requests
- No silent exceptions; full error logging with context
