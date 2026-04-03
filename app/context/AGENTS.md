# AGENTS.md (app/context)

## Scope

`app/context/` is the context engineering foundation for future multi-turn/session memory.

## Rules

- Keep context models and store interfaces clean and explicit.
- Do not implement advanced memory strategy in this round.
- Keep current store implementation minimal (in-memory only).
- Avoid direct coupling to provider SDK structures.

## Current Round Guidance

- Focus on skeleton quality: interfaces, models, and extension points.
- Do not add persistence/queue/distributed state management now.
