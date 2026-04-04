---
name: python-ai-provider-capability
description: Use this skill when refactoring or adding any external AI provider integration in a Python project. This includes LLM, image generation, video generation, audio, embedding, reranker, or similar providers. Use it for provider abstraction, request/response normalization, service-layer decoupling, config externalization, and focused structural refactoring. Do not use it for RAG orchestration, Agent logic, workflow engines, databases, or unrelated refactors.
---

# Purpose

This skill standardizes how provider-related refactoring is done in this repository.

It applies to all provider categories, including:
- text / LLM providers
- image generation providers
- video generation providers
- audio providers
- embedding providers
- reranker providers
- future external AI capability providers

Its purpose is to ensure all provider integrations follow the same engineering rules:
- vendor isolation
- schema normalization
- service-layer decoupling
- config externalization
- explicit error handling
- clean architecture boundaries

# Use This Skill When

Use this skill when:
- converting demo-style external AI calls into provider structure
- adding a new external provider under an existing architecture
- isolating SDK/API vendor details
- standardizing request and response models
- moving provider logic out of scripts or business modules
- improving maintainability of provider-related code

# Do Not Use This Skill For

Do not use this skill for:
- RAG pipeline implementation
- Agent logic
- workflow engine design
- background job systems
- database design
- queue design
- unrelated cleanup or broad architecture rewrites

# Required Workflow

Always follow this order:

1. Understand the current structure
2. Identify provider-related coupling points
3. Propose a minimal refactor plan
4. Wait for confirmation before major edits
5. Implement only the provider-related changes
6. Report changed files, run steps, and verification steps

# Refactor Rules

## 1. Keep provider logic isolated
Vendor-specific SDK/API logic must stay inside provider modules.

## 2. Normalize boundaries
Business and service layers should not depend directly on raw vendor SDK types.

## 3. Preserve structure
Prefer or preserve a structure such as:
- providers/
- schemas/
- services/
- core/config/

## 4. Keep scope minimal
Do not mix unrelated refactors into the provider task.

## 5. Preserve extensibility
The result should make future providers easier to add.

## 6. Externalize configuration
Do not hardcode:
- secrets
- environment-specific URLs
- vendor-specific runtime config that should be configurable

## 7. Respect future execution differences
Different provider types may differ in:
- sync vs async execution
- streaming vs non-streaming
- direct return vs task polling
- text vs file/media outputs

Preserve extension points for these differences.

# Expected Output Before Coding

Before coding, provide:
- task understanding
- scope
- assumptions
- file-level change plan
- interface/class design
- extensibility considerations
- risks/tradeoffs

# Expected Output After Coding

After coding, provide:
- changed files
- what changed in each file
- how to run
- how to verify
- next incremental step