---
name: python-api-capability-skeleton
description: Use this skill to scaffold and standardize the API layer for Python AI Core services. Focus on thin protocol handlers, service delegation, route structure, and architecture boundaries.
---

# Purpose

This skill defines how to create minimal, extensible API skeletons for `vi_ai_core_service`.

# Use This Skill When

- creating new API route skeletons
- introducing health or chat protocol endpoints
- enforcing API-to-service boundary rules
- preparing API directories for future expansion without overengineering

# Do Not Use This Skill For

- direct vendor SDK integration in API modules
- implementing RAG/Agent/workflow logic
- database or queue integration

# Required Workflow

1. Confirm API boundary and current stage constraints.
2. Create thin protocol models and route handlers.
3. Delegate business logic to service layer.
4. Keep outputs aligned to canonical schemas.
5. Add minimal run/verification instructions.
