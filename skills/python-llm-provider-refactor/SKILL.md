---
name: python-llm-provider-refactor
description: Use this skill when refactoring or adding a text-generation / chat-model provider in a Python project. This includes OpenAI-style chat/completions, DeepSeek-style chat, streaming/non-streaming text generation, and unified LLM request/response handling. Use it for LLM provider abstraction, chat request/response normalization, and service-layer decoupling. Do not use it for image, video, audio, embedding, reranker, RAG, or Agent workflow implementation.
---

# Purpose

This skill standardizes how LLM/text-generation provider refactoring is done in this repository.

It is specifically for:
- chat/text-generation provider integration
- OpenAI-style message-based model calls
- streaming and non-streaming text output
- normalized LLM request/response models
- LLM provider abstraction
- service-layer decoupling from vendor SDKs

# Use This Skill When

Use this skill when:
- adding a new LLM provider
- refactoring direct chat-completion calls into provider modules
- introducing a BaseLLMProvider abstraction
- standardizing text-generation request/response models
- moving model-specific chat logic out of scripts or business code
- adding streaming support for text output
- preparing for future prompt-service integration

# Do Not Use This Skill For

Do not use this skill for:
- image generation providers
- video generation providers
- audio providers
- embeddings or rerankers
- RAG pipelines
- Agent systems
- workflow engines
- database or queue work

# Required Workflow

Always follow this order:

1. Understand the current LLM-related structure
2. Find vendor-coupled text-generation code
3. Propose a minimal refactor plan
4. Wait for confirmation before major edits
5. Implement focused LLM-provider changes only
6. Report changed files, run steps, and verification steps

# LLM-Specific Refactor Rules

## 1. Standardize request shape
Prefer a unified LLM request model that can support:
- provider
- model
- system prompt
- user prompt or messages
- temperature
- stream flag
- optional future metadata

## 2. Standardize response shape
Prefer a unified LLM response model that can support:
- content
- provider
- model
- usage
- metadata
- raw response if needed

## 3. Prepare for future growth
The refactor should leave room for:
- multi-turn messages
- streaming output
- structured output
- prompt services
- tool calling integration later

## 4. Keep raw SDK details inside providers
Do not expose raw vendor SDK response objects deep into business layers unless explicitly required.

## 5. Preserve service entrypoint
Business code should call a service-layer method such as:
- chat()
- stream_chat()
rather than directly invoking SDK clients.

# Expected Output Before Coding

Before coding, provide:
- task understanding
- scope
- assumptions
- file-level change plan
- normalized request/response plan
- service/provider design
- future extensibility considerations

# Expected Output After Coding

After coding, provide:
- changed files
- what changed in each file
- how to run
- how to verify
- next incremental step