"""Policy interfaces for context history governance."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.context.models import (
    ContextSelectionResult,
    ContextSummaryResult,
    ContextTruncationResult,
    ContextWindow,
)


class WindowSelectionPolicy(ABC):
    """Selects a manageable history window from raw session context."""

    name: str = "window_selection.base"

    @abstractmethod
    def select(self, window: ContextWindow) -> ContextSelectionResult:
        raise NotImplementedError


class TruncationPolicy(ABC):
    """Applies budget-like truncation on selected history."""

    name: str = "truncation.base"

    @abstractmethod
    def truncate(self, selection_result: ContextSelectionResult) -> ContextTruncationResult:
        raise NotImplementedError


class SummaryPolicy(ABC):
    """Optionally compacts dropped history into a deterministic summary."""

    name: str = "summary.base"

    @abstractmethod
    def summarize(
        self,
        *,
        window: ContextWindow,
        selection_result: ContextSelectionResult,
        truncation_result: ContextTruncationResult,
    ) -> ContextSummaryResult:
        raise NotImplementedError


class HistorySerializationPolicy(ABC):
    """Serializes provider-agnostic history messages for request assembly."""

    name: str = "serialization.base"

    @abstractmethod
    def serialize(self, summary_result: ContextSummaryResult) -> list[dict[str, str]]:
        raise NotImplementedError
