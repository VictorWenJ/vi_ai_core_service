# LLM Provider Test Matrix

- Request mapping:
  - role/content mapping
  - temperature/max_tokens forwarding
- Response normalization:
  - content/provider/model
  - usage extraction
  - finish_reason extraction
- Error handling:
  - missing api key/config
  - invocation exception wrapping
  - malformed response handling
