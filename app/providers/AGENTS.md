# AGENTS.md (app/providers)

## Scope

`app/providers/` contains vendor adapters for model providers.

## Rules

- Vendor-specific SDK/API logic must stay in provider modules.
- Providers must return canonical schema objects, not raw SDK objects.
- Provider modules must not perform business orchestration.
- Keep provider-level exceptions explicit:
  - missing API key/config
  - invocation failure
  - malformed vendor response
- Prefer shared abstractions for compatible providers:
  - OpenAI-compatible providers should reuse `openai_compatible_base.py`.

## Current Round Guidance

- Preserve existing behavior of working providers.
- Allow scaffold providers, but keep interface shape stable.
- Avoid unrelated refactors outside provider responsibilities.
