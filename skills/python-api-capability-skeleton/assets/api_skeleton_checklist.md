# API Skeleton Checklist

- API route module created under `app/api/`.
- Route handler is thin and delegates to services.
- No vendor SDK imports in API layer.
- Protocol input is validated.
- Response shape is explicit and stable.
- Health endpoint exists for smoke validation.
