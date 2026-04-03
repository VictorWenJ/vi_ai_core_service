# AGENTS.md (app/prompts)

## Scope

`app/prompts/` is the prompt asset management layer.

## Rules

- Store stable prompt text as assets under `templates/`.
- Keep prompt rendering utilities deterministic and simple.
- Do not couple prompt assets to provider SDK details.
- Do not build complex prompt orchestration in this round.

## Current Round Guidance

- Provide only minimal registry + renderer skeleton.
- Ensure templates are easy to discover and version later.
