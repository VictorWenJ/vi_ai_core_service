# API Boundaries and Anti-Patterns

## Boundaries

- API: protocol translation and validation.
- Service: orchestration.
- Provider: vendor SDK interaction.

## Anti-Patterns

- Calling provider SDK clients directly in route handlers.
- Embedding business orchestration logic in API modules.
- Returning raw vendor SDK objects from API endpoints.
