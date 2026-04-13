"""默认聊天工作流配置。"""

from __future__ import annotations

# 默认主流程步骤数组，顺序即执行顺序。
DEFAULT_CHAT_WORKFLOW = [
    "normalize_scope",
    "retrieve_knowledge",
    "assemble_llm_request",
    "normalize_llm_request",
    "select_provider",
    "invoke_model",
    "persist_context",
    "finalize_trace",
]

# 默认生命周期 Hook 绑定配置。
DEFAULT_CHAT_HOOKS: dict[str, list[str]] = {
    "before_request": ["request_audit", "prompt_guard"],
    "after_retrieval": ["retrieval_trace"],
    "before_model_call": ["request_audit"],
    "after_model_call": ["response_postprocess"],
    "after_stream_completed": ["stream_finalize"],
    "on_error": ["error_audit"],
}

# 默认步骤级 Hook 绑定配置。
DEFAULT_CHAT_STEP_HOOKS: dict[str, list[str]] = {
    "before_step:normalize_scope": [],
    "after_step:normalize_scope": [],
    "before_step:retrieve_knowledge": [],
    "after_step:retrieve_knowledge": [],
    "before_step:assemble_llm_request": [],
    "after_step:assemble_llm_request": [],
    "before_step:normalize_llm_request": [],
    "after_step:normalize_llm_request": [],
    "before_step:select_provider": [],
    "after_step:select_provider": [],
    "before_step:invoke_model": [],
    "after_step:invoke_model": [],
    "before_step:persist_context": [],
    "after_step:persist_context": [],
    "before_step:finalize_trace": [],
    "after_step:finalize_trace": [],
}

# 默认 skills 引用位（本轮仅声明，不做 runtime loader）。
DEFAULT_CHAT_SKILLS = [
    "prompt://default-chat-system",
    "rag://knowledge-retrieval",
]

