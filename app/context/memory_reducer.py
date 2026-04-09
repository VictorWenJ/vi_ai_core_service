"""working memory 的规则化 reducer。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import re

from app.context.models import ContextMessage, WorkingMemoryState, now_utc_iso


class BaseWorkingMemoryReducer(ABC):
    """从最近一轮对话归并 working memory 的抽象接口。"""

    name: str = "working_memory.reducer.base"

    @abstractmethod
    def reduce(
        self,
        *,
        previous: WorkingMemoryState,
        latest_user_message: ContextMessage | None,
        latest_assistant_message: ContextMessage | None,
    ) -> WorkingMemoryState:
        raise NotImplementedError


@dataclass(frozen=True)
class WorkingMemoryReducerLimits:
    max_items_per_section: int
    max_value_chars: int


class RuleBasedWorkingMemoryReducer(BaseWorkingMemoryReducer):
    """默认规则版 reducer：高置信度、低噪音、可测试。"""

    name = "working_memory.reducer.rule_based_v1"

    def __init__(self, *, max_items_per_section: int, max_value_chars: int) -> None:
        if max_items_per_section <= 0:
            raise ValueError("max_items_per_section 必须大于 0。")
        if max_value_chars <= 0:
            raise ValueError("max_value_chars 必须大于 0。")
        self._limits = WorkingMemoryReducerLimits(
            max_items_per_section=max_items_per_section,
            max_value_chars=max_value_chars,
        )

    def reduce(
        self,
        *,
        previous: WorkingMemoryState,
        latest_user_message: ContextMessage | None,
        latest_assistant_message: ContextMessage | None,
    ) -> WorkingMemoryState:
        active_goal = previous.active_goal
        if latest_user_message:
            extracted_goal = self._extract_active_goal(latest_user_message.content)
            if extracted_goal:
                active_goal = extracted_goal

        constraints = self._merge_section(
            previous.constraints,
            self._extract_constraints(latest_user_message, latest_assistant_message),
        )
        decisions = self._merge_section(
            previous.decisions,
            self._extract_decisions(latest_user_message, latest_assistant_message),
        )
        open_questions = self._merge_section(
            previous.open_questions,
            self._extract_open_questions(latest_user_message),
        )
        next_step = self._merge_next_step(
            previous.next_step,
            self._extract_next_step(latest_assistant_message),
        )

        changed = (
            active_goal != previous.active_goal
            or constraints != previous.constraints
            or decisions != previous.decisions
            or open_questions != previous.open_questions
            or next_step != previous.next_step
        )
        updated_at = now_utc_iso() if changed else previous.updated_at
        return WorkingMemoryState(
            active_goal=active_goal,
            constraints=constraints,
            decisions=decisions,
            open_questions=open_questions,
            next_step=next_step,
            updated_at=updated_at,
        )

    def _extract_active_goal(self, text: str) -> str | None:
        normalized = self._normalize_text(text)
        if not normalized:
            return None
        goal_prefixes = ("我想", "我要", "请帮我", "希望", "目标", "需要")
        if not normalized.startswith(goal_prefixes):
            return None
        return normalized[: self._limits.max_value_chars]

    def _extract_constraints(
        self,
        latest_user_message: ContextMessage | None,
        latest_assistant_message: ContextMessage | None,
    ) -> list[str]:
        keywords = ("必须", "不要", "禁止", "只允许", "仅", "不能")
        return self._extract_by_keywords(
            [latest_user_message, latest_assistant_message],
            keywords,
        )

    def _extract_decisions(
        self,
        latest_user_message: ContextMessage | None,
        latest_assistant_message: ContextMessage | None,
    ) -> list[str]:
        keywords = ("决定", "确定", "采用", "保持", "选择")
        return self._extract_by_keywords(
            [latest_user_message, latest_assistant_message],
            keywords,
        )

    def _extract_open_questions(
        self,
        latest_user_message: ContextMessage | None,
    ) -> list[str]:
        if latest_user_message is None:
            return []
        sentences = self._split_sentences(latest_user_message.content)
        result: list[str] = []
        for sentence in sentences:
            if "?" in sentence or "？" in sentence:
                result.append(sentence[: self._limits.max_value_chars])
        return result

    def _extract_next_step(
        self,
        latest_assistant_message: ContextMessage | None,
    ) -> str | None:
        if latest_assistant_message is None:
            return None
        sentences = self._split_sentences(latest_assistant_message.content)
        next_step_markers = ("下一步", "接下来", "建议", "请先", "你可以先")
        for sentence in sentences:
            if any(marker in sentence for marker in next_step_markers):
                return sentence[: self._limits.max_value_chars]
        return None

    def _extract_by_keywords(
        self,
        messages: list[ContextMessage | None],
        keywords: tuple[str, ...],
    ) -> list[str]:
        result: list[str] = []
        for message in messages:
            if message is None:
                continue
            for sentence in self._split_sentences(message.content):
                if any(keyword in sentence for keyword in keywords):
                    result.append(sentence[: self._limits.max_value_chars])
        return result

    def _merge_section(self, existing: list[str], incoming: list[str]) -> list[str]:
        merged = list(existing)
        for item in incoming:
            normalized_item = self._normalize_text(item)
            if not normalized_item:
                continue
            merged.append(normalized_item[: self._limits.max_value_chars])
        return self._deduplicate_and_limit(merged)

    def _merge_next_step(self, existing: str | None, incoming: str | None) -> str | None:
        if incoming:
            normalized = self._normalize_text(incoming)
            return normalized[: self._limits.max_value_chars] if normalized else existing
        return existing

    def _deduplicate_and_limit(self, values: list[str]) -> list[str]:
        deduplicated: list[str] = []
        seen: set[str] = set()
        for value in values:
            normalized_value = self._normalize_text(value)
            if not normalized_value or normalized_value in seen:
                continue
            seen.add(normalized_value)
            deduplicated.append(normalized_value)
        if len(deduplicated) <= self._limits.max_items_per_section:
            return deduplicated
        return deduplicated[-self._limits.max_items_per_section :]

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        normalized = RuleBasedWorkingMemoryReducer._normalize_text(text)
        if not normalized:
            return []
        parts = re.split(r"[。！？\n]+", normalized)
        return [part.strip() for part in parts if part.strip()]

    @staticmethod
    def _normalize_text(value: str) -> str:
        return " ".join(value.strip().split())
