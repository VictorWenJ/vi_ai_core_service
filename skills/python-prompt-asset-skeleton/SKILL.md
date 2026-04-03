---
name: python-prompt-asset-skeleton
description: Use this skill to scaffold prompt asset management with template files, lightweight registry/renderer modules, and clear separation from provider and service internals.
---

# Purpose

This skill standardizes prompt asset skeleton construction for `vi_ai_core_service`.

# Use This Skill When

- creating prompt template directories and default templates
- adding prompt registry and renderer skeleton modules
- enforcing prompt asset boundaries

# Do Not Use This Skill For

- complex prompt orchestration engines
- business-specific prompt catalogs with advanced routing logic
- provider-coupled prompt rendering

# Required Workflow

1. Create template directories and baseline templates.
2. Add minimal registry and renderer modules.
3. Keep behavior deterministic and easy to test.
4. Document extension points for future prompt governance.
