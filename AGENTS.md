# AGENTS.md

## 1. Project Identity

This repository is `vi_ai_core_service`, the Python AI Core subsystem of a larger consumer-facing AI product portfolio.

It is not a demo repo. It is a long-lived engineering codebase that evolves into a production-grade AI capability layer.

## 2. Platform Boundary (Python vs Java)

The overall platform is split into two subsystems:

- Python AI Core (`vi_ai_core_service`)
  - model invocation
  - provider abstraction
  - prompt assets and rendering
  - context engineering foundation
  - future RAG / Agent / multimodal capability integration
- Java Product Backend
  - user/session/project/task lifecycle
  - state transitions, retries, quota/audit
  - product-oriented APIs for frontend applications

Python must stay focused on AI capability concerns. Java concerns must not leak into this repository.

## 3. Current Stage Priority

Current priority: **LLM full flow first, structure first**.

This round is for structure governance and skeleton hardening. Avoid business expansion.

### In Scope (Current Round)

- directory structure governance
- AGENTS.md rules at root and key subdirectories
- skills governance and skeleton skills
- minimal API/server/prompt/context skeletons

### Out of Scope (Current Round)

- RAG implementation
- Agent runtime implementation
- multimodal implementation
- Redis/DB integration
- workflow engine / MQ / Celery / LangGraph
- Java-side implementation

## 4. Core Engineering Rules

### 4.1 Layer boundaries are strict

- `app/api/`: protocol layer only, no vendor SDK calls
- `app/services/`: capability orchestration, no direct SDK internals
- `app/providers/`: vendor adapters and provider-specific logic only
- `app/schemas/`: canonical request/response contracts
- `app/prompts/`: prompt assets and rendering helpers
- `app/context/`: context engineering foundation for future session memory

### 4.2 Main entrypoint rule

`app/main.py` is only for local smoke tests.

It is not the formal system entrypoint.

### 4.3 Provider design rule

Business-facing layers must not depend on vendor SDK response structures.

Provider differences are normalized inside provider modules and returned as canonical schemas.

### 4.4 Prompt asset rule

Prompt content should be managed under `app/prompts/` as assets.

Avoid scattering stable prompt text across unrelated service files.

### 4.5 Context foundation rule

`app/context/` is a structural foundation for future multi-turn/session memory.

Keep it minimal in this round; do not implement advanced memory policies yet.

## 5. Security Rules

- Never commit real API keys, tokens, or secrets.
- `.env.example` must contain placeholders only.
- If a real key is accidentally exposed, rotate it immediately at the provider platform.

## 6. Implementation Workflow

For non-trivial tasks:

1. Understand scope and constraints.
2. Propose a minimal, architecture-safe plan.
3. Wait for user confirmation.
4. Implement incrementally without unrelated refactors.
5. Report changed files, run/verify steps, and next increment.

## 7. Definition of Good Changes

Good changes should:

- improve structure clarity
- preserve provider/service/schema boundaries
- keep current LLM foundation runnable
- increase extensibility with minimal risk
- avoid over-engineering at this stage

