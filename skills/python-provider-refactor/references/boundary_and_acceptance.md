# Boundary and Acceptance Notes

## Boundaries

- Allowed: provider adapters, config wiring, normalization updates.
- Not allowed: RAG, Agent, workflow engine, DB/queue integration.

## Acceptance

- Provider compiles and runs behind the existing service entrypoint.
- Canonical response contract remains stable.
- Minimal, focused change set without unrelated refactors.
