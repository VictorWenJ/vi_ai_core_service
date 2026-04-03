# AGENTS.md (app/api)

## Scope

`app/api/` is the HTTP protocol layer for `vi_ai_core_service`.

## Rules

- Keep API handlers thin.
- Do not call vendor SDKs directly from API modules.
- API should delegate AI operations to service-layer abstractions.
- Validate protocol input/output shape and convert to/from canonical schemas.
- Avoid embedding business orchestration in route handlers.

## Current Round Guidance

- Keep endpoints minimal and non-streaming.
- Provide only skeleton-ready routes (`/health`, `/chat`) with clean extension points.
- Do not implement advanced API concerns yet (auth, quota, multi-tenant policy, etc.).
