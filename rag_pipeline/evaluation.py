"""Page-level retrieval quality evaluation for labelled question datasets."""
from __future__ import annotations

import math
from typing import Any

PAGE_KEYS = ("source", "page")
METHODS = ("bm25", "dense", "hybrid")


def _validate_dataset(dataset: Any) -> list[dict[str, Any]]:
    if not isinstance(dataset, list) or not dataset:
        raise ValueError("Evaluation dataset must be a non-empty JSON array")

    cleaned: list[dict[str, Any]] = []
    for position, row in enumerate(dataset, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Dataset row {position} must be a JSON object")
        question = row.get("question")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Dataset row {position} must have a non-empty question")
        pages = row.get("relevant_pages")
        if not isinstance(pages, list) or not pages:
            raise ValueError(
                f"Dataset row {position} must have a non-empty relevant_pages array"
            )

        relevant: set[tuple[str, int]] = set()
        for page in pages:
            if not isinstance(page, dict):
                raise ValueError(
                    f"Every relevant_pages entry in row {position} must be an object"
                )
            source = page.get("source")
            page_number = page.get("page")
            if not isinstance(source, str) or not source.strip():
                raise ValueError(
                    f"Every relevant page in row {position} needs a non-empty source"
                )
            if type(page_number) is not int or page_number < 1:
                raise ValueError(
                    f"Every relevant page in row {position} needs a positive integer page"
                )
            relevant.add((source, page_number))

        cleaned.append({
            "id": str(row.get("id", position)),
            "question": question.strip(),
            "relevant_pages": relevant,
        })
    return cleaned


def _unique_page_ranking(results: list[Any]) -> list[tuple[str, int]]:
    """Collapse chunk results into a stable, first-seen ranking of source pages."""
    ranked: list[tuple[str, int]] = []
    seen: set[tuple[str, int]] = set()
    for result in results:
        key = (result.chunk.source, result.chunk.page)
        if key not in seen:
            ranked.append(key)
            seen.add(key)
    return ranked


def _score(ranking: list[tuple[str, int]], relevant: set[tuple[str, int]], k: int) -> dict[str, float]:
    hits = [1 if page in relevant else 0 for page in ranking[:k]]
    recall = len({page for page in ranking[:k] if page in relevant}) / len(relevant)

    reciprocal_rank = 0.0
    for rank, hit in enumerate(hits, start=1):
        if hit:
            reciprocal_rank = 1.0 / rank
            break

    dcg = sum(hit / math.log2(rank + 1) for rank, hit in enumerate(hits, start=1))
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    ndcg = dcg / idcg if idcg else 0.0
    return {
        f"recall@{k}": recall,
        f"mrr@{k}": reciprocal_rank,
        f"ndcg@{k}": ndcg,
    }


def evaluate_retrieval_dataset(
    index: Any,
    dataset: Any,
    *,
    top_k: int = 5,
    candidate_k: int | None = None,
) -> dict[str, Any]:
    """Evaluate BM25, dense and hybrid retrieval against manually labelled pages.

    Metrics use unique (source filename, 1-based page number) pairs, not chunk IDs.
    The index is asked for more than k chunks so duplicate chunks from one page
    are less likely to occupy all evaluated page ranks. This is a page-retrieval
    evaluation and should not be interpreted as answer-generation accuracy.
    """
    if type(top_k) is not int or top_k < 1:
        raise ValueError("top_k must be a positive integer")
    if candidate_k is not None and (
        type(candidate_k) is not int or candidate_k < top_k
    ):
        raise ValueError("candidate_k must be an integer greater than or equal to top_k")

    rows = _validate_dataset(dataset)
    fetch_k = candidate_k if candidate_k is not None else max(20, top_k * 5)
    method_functions = {
        "bm25": lambda question: index.search_bm25(question, top_k=fetch_k),
        "dense": lambda question: index.search_dense(question, top_k=fetch_k),
        "hybrid": lambda question: index.search_hybrid(
            question, top_k=fetch_k, candidate_k=fetch_k
        ),
    }

    report: dict[str, Any] = {
        "evaluation_unit": "unique source filename + 1-based page",
        "aggregation": "macro average across questions",
        "questions": len(rows),
        "top_k": top_k,
        "candidate_chunks_requested": fetch_k,
        "metrics": {},
    }

    method_reports: dict[str, Any] = {}
    for method_name, retrieve in method_functions.items():
        per_question: list[dict[str, Any]] = []
        for row in rows:
            ranking = _unique_page_ranking(retrieve(row["question"]))[:top_k]
            scores = _score(ranking, row["relevant_pages"], top_k)
            per_question.append({
                "id": row["id"],
                "question": row["question"],
                "relevant_pages": [
                    {"source": source, "page": page}
                    for source, page in sorted(row["relevant_pages"])
                ],
                "retrieved_pages": [
                    {"source": source, "page": page} for source, page in ranking
                ],
                **scores,
            })

        metric_names = (f"recall@{top_k}", f"mrr@{top_k}", f"ndcg@{top_k}")
        averages = {
            metric: round(
                sum(item[metric] for item in per_question) / len(per_question), 6
            )
            for metric in metric_names
        }
        method_reports[method_name] = {
            **averages,
            "per_question": per_question,
        }

    report["metrics"] = method_reports
    return report
