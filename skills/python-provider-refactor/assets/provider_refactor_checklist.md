# Provider Refactor Checklist

- Confirm provider logic is isolated under `app/providers/`.
- Ensure no vendor SDK structures leak into service/API layers.
- Keep request/response normalization aligned with canonical schemas.
- Externalize all runtime configuration.
- Verify error mapping is explicit and actionable.
- Add/update mock-based tests for mapping and failure paths.
