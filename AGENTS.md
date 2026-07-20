# AGENTS.md: Cross-Assistant Workflow Contract

## Core Workflow (For All AI Assistants)
All AI assistants working on Codely must follow this workflow, regardless of tooling (Cursor, Claude Code, Windsurf, etc.):

1. **Start with RULES_CHECKLIST**: First, read `.docs/RULES_CHECKLIST.md` to confirm current constraints and requirements
2. **Check Current State**: Run `git status` and look at `next-task.md` (if present) to know what's in progress
3. **Plan with TodoWrite**: For complex tasks, use TodoWrite to break into steps
4. **Test Before Committing**: Run manual verification before committing changes (per `CLAUDE.md` testing commands)
5. **Update Documentation**: Update relevant `.docs/` files (IMPLEMENTATION_SUMMARY.md, API_SPEC.md, etc.) whenever adding features or fixing bugs
6. **Commit Atomic Changes**: Keep commits focused on a single feature/fix; use descriptive commit messages

## Assistant-Specific Rules
- **Architect/Planning Agent**: Writes/updates `prd.md`, `architecture.md`, `next-task.md`, `plan.md`
- **Coding Agent**: Follows `CLAUDE.md` style, uses TodoWrite, updates docs
- **Testing Agent**: Follows `testing.md` patterns, verifies changes
- **Audit Agent**: Checks `threat_model.md` and `vulnerabilities.md`, ensures no regressions
- **Documentation Agent**: Keeps all docs up-to-date

## Handover Protocol
If an agent is switching to another, always:
1. Update `next-task.md` with the current task/state
2. Update `memory.md` with what was done and why
3. Ensure git is clean (no uncommitted changes unless explicitly handed off)
