from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.rag.evaluation.models import (
    AnswerLabel,
    CitationLabel,
    EvaluationDataset,
    EvaluationSample,
    RetrievalLabel,
)
from app.rag.evaluation.runner import RAGEvaluationRunner
from app.rag.models import Citation, RetrievalResult, RetrievalTrace, RetrievedChunk


class StubRAGRuntime:
    def __init__(self, responses: dict[str, RetrievalResult]) -> None:
        self._responses = responses

    def retrieve_for_chat(
        self,
        *,
        query_text: str,
        metadata_filter: dict | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        del metadata_filter, top_k
        return self._responses[query_text]


class RAGEvaluationTests(unittest.TestCase):
    def test_dataset_supports_versioned_save_and_load(self) -> None:
        dataset = EvaluationDataset(
            dataset_id="rag-golden",
            version_id="v2026-04-12",
            samples=[
                EvaluationSample(
                    sample_id="q-1",
                    query_text="What is baseline law?",
                    retrieval_label=RetrievalLabel(
                        expected_document_ids=["doc-law"],
                        expected_chunk_ids=["chk-law-1"],
                        min_recall=1.0,
                    ),
                    citation_label=CitationLabel(
                        expected_citation_ids=["c-law-1"],
                        expected_document_ids=["doc-law"],
                        min_recall=1.0,
                        min_precision=1.0,
                    ),
                    answer_label=AnswerLabel(
                        required_terms=["law", "baseline"],
                        forbidden_terms=["hallucination"],
                        min_required_term_hit_ratio=1.0,
                        max_forbidden_term_hit_count=0,
                    ),
                )
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "dataset.json"
            dataset.save_json(path)
            reloaded = EvaluationDataset.load_json(path)

        self.assertEqual(reloaded.dataset_id, "rag-golden")
        self.assertEqual(reloaded.version_id, "v2026-04-12")
        self.assertEqual(len(reloaded.samples), 1)
        self.assertEqual(reloaded.samples[0].sample_id, "q-1")

    def test_retrieval_citation_answer_evaluation_methods(self) -> None:
        runner = RAGEvaluationRunner(rag_runtime=StubRAGRuntime({}))
        retrieval_result = RetrievalResult(
            knowledge_block="kb",
            retrieved_chunks=[
                RetrievedChunk(
                    chunk_id="chk-law-1",
                    document_id="doc-law",
                    text="law baseline text",
                    score=0.91,
                    title="Law Doc",
                    origin_uri="file:///law.md",
                    source_type="markdown_file",
                    jurisdiction=None,
                    domain="law",
                    effective_at=None,
                    updated_at="2026-04-10T00:00:00+00:00",
                    metadata={},
                )
            ],
            citations=[
                Citation(
                    citation_id="c-law-1",
                    document_id="doc-law",
                    chunk_id="chk-law-1",
                    title="Law Doc",
                    snippet="law baseline text",
                    origin_uri="file:///law.md",
                    source_type="markdown_file",
                    updated_at="2026-04-10T00:00:00+00:00",
                    metadata={},
                )
            ],
            trace=RetrievalTrace(status="succeeded", query_text="law", top_k=4),
        )

        retrieval_eval = runner.evaluate_retrieval(
            RetrievalLabel(
                expected_document_ids=["doc-law"],
                expected_chunk_ids=["chk-law-1"],
                min_recall=1.0,
            ),
            retrieval_result,
        )
        citation_eval = runner.evaluate_citation(
            CitationLabel(
                expected_citation_ids=["c-law-1"],
                expected_document_ids=["doc-law"],
                min_recall=1.0,
                min_precision=1.0,
            ),
            retrieval_result,
        )
        answer_eval = runner.evaluate_answer(
            AnswerLabel(
                required_terms=["law", "baseline"],
                forbidden_terms=["hallucination"],
                min_required_term_hit_ratio=1.0,
                max_forbidden_term_hit_count=0,
            ),
            "This answer follows law baseline.",
        )

        self.assertTrue(retrieval_eval.passed)
        self.assertEqual(retrieval_eval.recall, 1.0)
        self.assertTrue(citation_eval.passed)
        self.assertEqual(citation_eval.recall, 1.0)
        self.assertEqual(citation_eval.precision, 1.0)
        self.assertTrue(answer_eval.passed)
        self.assertEqual(answer_eval.required_term_hit_ratio, 1.0)

    def test_runner_outputs_regression_friendly_result_file_and_logs(self) -> None:
        retrieval_result = RetrievalResult(
            knowledge_block="[knowledge_block]\nlaw baseline",
            retrieved_chunks=[
                RetrievedChunk(
                    chunk_id="chk-law-1",
                    document_id="doc-law",
                    text="law baseline text",
                    score=0.95,
                    title="Law Doc",
                    origin_uri="file:///law.md",
                    source_type="markdown_file",
                    jurisdiction=None,
                    domain="law",
                    effective_at=None,
                    updated_at="2026-04-10T00:00:00+00:00",
                    metadata={},
                )
            ],
            citations=[
                Citation(
                    citation_id="c-law-1",
                    document_id="doc-law",
                    chunk_id="chk-law-1",
                    title="Law Doc",
                    snippet="law baseline text",
                    origin_uri="file:///law.md",
                    source_type="markdown_file",
                    updated_at="2026-04-10T00:00:00+00:00",
                    metadata={},
                )
            ],
            trace=RetrievalTrace(status="succeeded", query_text="law baseline", top_k=4),
        )
        runtime = StubRAGRuntime({"law baseline": retrieval_result})
        runner = RAGEvaluationRunner(
            rag_runtime=runtime,
            answer_generator=lambda sample, result: f"{sample.query_text}\n{result.knowledge_block}",
        )
        dataset = EvaluationDataset(
            dataset_id="rag-golden",
            version_id="v1",
            samples=[
                EvaluationSample(
                    sample_id="q-1",
                    query_text="law baseline",
                    retrieval_label=RetrievalLabel(
                        expected_document_ids=["doc-law"],
                        expected_chunk_ids=["chk-law-1"],
                        min_recall=1.0,
                    ),
                    citation_label=CitationLabel(
                        expected_citation_ids=["c-law-1"],
                        expected_document_ids=["doc-law"],
                        min_recall=1.0,
                        min_precision=1.0,
                    ),
                    answer_label=AnswerLabel(
                        required_terms=["law", "baseline"],
                        forbidden_terms=["forbidden"],
                        min_required_term_hit_ratio=1.0,
                        max_forbidden_term_hit_count=0,
                    ),
                )
            ],
        )

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "app.rag.evaluation.runner.log_report"
        ) as mocked_log_report:
            output_path = Path(temp_dir) / "result.json"
            run_result = runner.run(dataset, result_output_path=output_path)
            saved_payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(run_result.dataset_id, "rag-golden")
        self.assertEqual(run_result.dataset_version_id, "v1")
        self.assertEqual(run_result.summary.sample_count, 1)
        self.assertEqual(run_result.summary.overall_pass_count, 1)
        self.assertTrue(run_result.cases[0].passed)
        self.assertEqual(saved_payload["summary"]["overall_pass_rate"], 1.0)
        logged_events = [call.args[0] for call in mocked_log_report.call_args_list]
        self.assertIn("rag.evaluation.run.started", logged_events)
        self.assertIn("rag.evaluation.run.completed", logged_events)


if __name__ == "__main__":
    unittest.main()
