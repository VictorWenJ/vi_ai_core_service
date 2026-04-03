---
name: python-context-engineering-skeleton
description: Use this skill to scaffold context engineering modules for future multi-turn memory and session context management without implementing full production logic yet.
---

# Purpose

This skill standardizes minimal context-layer scaffolding in `vi_ai_core_service`.

# Use This Skill When

- creating context models and manager interfaces
- introducing store abstractions for session memory
- preparing extension points for future memory strategies

# Do Not Use This Skill For

- full memory policy implementation
- retrieval pipelines
- persistence/queue/distributed state integration

# Required Workflow

1. Define minimal context models.
2. Add store interface and in-memory implementation.
3. Add manager façade for future orchestration.
4. Keep implementation lightweight and deterministic.
