"""Sanity-check the bundled Module 1 labelled evaluation dataset."""
from __future__ import annotations

import json
from pathlib import Path

from rag_pipeline.evaluation import _validate_dataset

DATASET_PATH = Path(__file__).resolve().parents[1] / "evaluation_datasets" / "module1.json"


def test_module1_evaluation_dataset_has_broad_question_coverage():
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    assert len(dataset) == 34
    assert len({row["id"] for row in dataset}) == len(dataset)
    assert len({row["relevant_pages"][0]["page"] for row in dataset}) >= 25


def test_module1_evaluation_labels_match_expected_pdf_and_page_range():
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    for row in dataset:
        assert row["question"].strip()
        assert row["relevant_pages"]
        for label in row["relevant_pages"]:
            assert label["source"] == "Module1.pdf"
            assert type(label["page"]) is int
            assert 1 <= label["page"] <= 38


def test_module1_evaluation_dataset_passes_evaluator_validation():
    dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    validated = _validate_dataset(dataset)
    assert len(validated) == 34
    assert all(row["relevant_pages"] for row in validated)
