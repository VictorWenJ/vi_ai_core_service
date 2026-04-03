# Prompt Layer Boundaries and Acceptance

## Boundaries

- Prompt assets belong to `app/prompts/`.
- Service layer may call renderer/registry, but should not own prompt files.
- Provider layer must remain prompt-agnostic.

## Acceptance

- Prompt skeleton is functional and discoverable.
- Template loading path is explicit.
- Complexity remains minimal in this stage.
