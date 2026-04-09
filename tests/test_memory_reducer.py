from __future__ import annotations

import unittest

from app.context.memory_reducer import RuleBasedWorkingMemoryReducer
from app.context.models import ContextMessage, WorkingMemoryState


class MemoryReducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.reducer = RuleBasedWorkingMemoryReducer(
            max_items_per_section=2,
            max_value_chars=40,
        )

    def test_reduce_applies_dedup_and_item_limits(self) -> None:
        previous = WorkingMemoryState(
            constraints=["必须保持分层边界"],
            decisions=["决定采用小步迭代"],
        )
        latest_user = ContextMessage(
            role="user",
            content="必须保持分层边界。必须补齐测试。必须补齐测试。",
        )
        latest_assistant = ContextMessage(
            role="assistant",
            content="决定采用小步迭代。决定先修复失败测试。下一步先补测试。",
        )

        result = self.reducer.reduce(
            previous=previous,
            latest_user_message=latest_user,
            latest_assistant_message=latest_assistant,
        )

        self.assertLessEqual(len(result.constraints), 2)
        self.assertEqual(len(result.constraints), len(set(result.constraints)))
        self.assertLessEqual(len(result.decisions), 2)
        self.assertEqual(len(result.decisions), len(set(result.decisions)))
        self.assertIsNotNone(result.next_step)

    def test_reduce_empty_input_does_not_pollute_previous_state(self) -> None:
        previous = WorkingMemoryState(
            active_goal="我想保持主链路稳定",
            constraints=["必须保留兼容"],
            decisions=["决定先改测试"],
            open_questions=["是否要补更多回归用例?"],
            next_step="先跑测试",
            updated_at="2026-04-09T00:00:00+00:00",
        )
        latest_user = ContextMessage(role="user", content="   ")
        latest_assistant = ContextMessage(role="assistant", content=" ")

        result = self.reducer.reduce(
            previous=previous,
            latest_user_message=latest_user,
            latest_assistant_message=latest_assistant,
        )

        self.assertEqual(result.active_goal, previous.active_goal)
        self.assertEqual(result.constraints, previous.constraints)
        self.assertEqual(result.decisions, previous.decisions)
        self.assertEqual(result.open_questions, previous.open_questions)
        self.assertEqual(result.next_step, previous.next_step)
        self.assertEqual(result.updated_at, previous.updated_at)
