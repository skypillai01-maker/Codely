# procedures.md: Standard Operating Blueprints

## 1. Bug Fix Workflow
1. **Identify and Document**: Add to `vulnerabilities.md` with ID, severity, description, mitigation
2. **Plan**: Use `TodoWrite` to create step-by-step plan
3. **Fix**: Implement the fix, following `CLAUDE.md` rules
4. **Verify**: Test manually (per `testing.md`), check server logs for errors
5. **Update Docs**: Update relevant docs (IMPLEMENTATION_SUMMARY.md, etc.)
6. **Commit**: Atomic commit with descriptive message referencing the fix
7. **Close**: Mark vulnerability as "Mitigated" in `vulnerabilities.md`

## 2. Feature Addition Workflow
1. **Check PRD and Architecture**: Confirm feature is in scope (read `prd.md`, `architecture.md`)
2. **Plan**: Write `plan.md` or use `TodoWrite` for steps
3. **Update next-task.md**: Set current task
4. **Implement**: Follow `CLAUDE.md` style; add any necessary endpoints/modules
5. **Add Documention**: Update `API_SPEC.md`, `IMPLEMENTATION_SUMMARY.md`, etc.
6. **Test**: Follow `testing.md` patterns
7. **Commit**: Atomic commit with descriptive message
8. **Update memory.md**: Document what was done and why

## 3. API Endpoint Creation
1. **Add Pydantic model**: If needed, in `core/api/main.py` or appropriate place
2. **Implement logic**: In `core/api/main.py` or call into core/rag/modules
3. **Add error handling**: Try/except with logging
4. **Add middleware checks**: Auth, permissions, etc. (if needed)
5. **Document**: Add to `API_SPEC.md` and `IMPLEMENTATION_SUMMARY.md`
6. **Test manually**: Test via web UI or curl

## 4. Git Workflow
- Always start with `git status`
- Commit frequently, with atomic changes
- Write descriptive commit messages (e.g., "feat: add document management endpoints", "fix: add auth rate limiting")
- Never commit `storage/`, `.env`, or user-specific data
- Pull before pushing to avoid conflicts
