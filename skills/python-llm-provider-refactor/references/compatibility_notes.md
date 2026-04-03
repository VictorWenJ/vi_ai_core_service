# Compatibility Notes

- Prefer OpenAI-compatible reuse when supported by vendor APIs.
- Keep streaming as an extension point if not in current scope.
- Keep model fallback behavior in service layer, not provider routing logic.
- Preserve `chat()` as the business-facing service entrypoint.
