# system-instructions.md: Model Behavioral Rules

## Core Behavioral Rules
- **Prefer Succinct Comments**: In code, only write comments when necessary to explain *why*, not what the code does. Keep docstrings clear, but avoid redundancy.
- **Always Use Python**: For backend/engine code; never switch to other languages for core logic.
- **Follow Existing Architecture**: Always use the existing folder structure, core modules, and API patterns (look at core/api/main.py, core/memory/vector_store.py, core/rag/engine.py first).
- **Respect Single-Responsibility Principle**: Keep functions focused on one task; don't overload functions with multiple concerns.
- **Prioritize User Isolation**: Never bypass user-scoped memory/storage; always use get_memory_for_user(user_id) or FAISSVectorStore(user_id=...).

## Communication Style
- Be direct, blunt, and to the point. No sugarcoating.
- If something is wrong or violates RULES_CHECKLIST.md, state it clearly without ambiguity.
- Use clear, specific examples when explaining fixes or changes.

## Workflow Reminders
- Check RULES_CHECKLIST.md *first* before making changes.
- Check git status and next-task.md at the start of any session.
- Always update relevant .docs/ files (IMPLEMENTATION_SUMMARY.md, memory.md, chatmem.md) after making changes.
- Commit atomic changes with descriptive messages.
