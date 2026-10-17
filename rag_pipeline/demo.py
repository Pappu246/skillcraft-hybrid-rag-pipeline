"""Small helpers used by the interactive Streamlit demo.

The built-in guide is original demonstration content. User-uploaded PDFs are
extracted into in-memory chunks; their temporary upload files are removed as
soon as indexing finishes.
"""
from __future__ import annotations

import csv
import hashlib
import io
import logging
from pathlib import Path, PurePosixPath
import tempfile
from typing import Any

from .core import Chunk, HybridIndex, ingest_pdfs

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
SAMPLE_SOURCE = "Built-in Data Structures Guide"

_SAMPLE_PAGES = [
    "Data are raw facts, observations, or measurements. Information is data that has been processed, organised, or interpreted so it is meaningful for a particular purpose. A data structure is a way to organise and store data so operations such as search, insertion, deletion, and traversal can be performed effectively. An abstract data type (ADT) describes the behaviour and operations of a type without requiring a particular implementation.",
    "An array stores elements in contiguous memory locations and supports constant-time access by index when the index is valid. Inserting or deleting an element in the middle may require shifting later elements. A linked list stores elements in nodes connected by links. Linked lists can insert or remove a node efficiently when its position is known, but accessing the element at an arbitrary index requires traversal.",
    "A stack is a linear data structure that follows Last In, First Out (LIFO). Push adds an item and pop removes the most recently added item. A queue follows First In, First Out (FIFO): enqueue adds an item at the rear and dequeue removes an item from the front. Stacks are useful for function calls and undo operations; queues are useful for scheduling and breadth-first processing.",
    "Linear search checks items one by one and can work on an unsorted collection. Binary search repeatedly halves the remaining search interval, but it requires the collection to be sorted. With n elements, linear search takes O(n) time in the worst case, while binary search takes O(log n) time. The logarithmic reduction makes binary search efficient for large sorted arrays.",
    "Big-O notation describes an asymptotic upper bound on how an algorithm's resource use grows with input size. O(1) is constant time, O(log n) is logarithmic, O(n) is linear, O(n log n) commonly appears in efficient comparison sorting, and O(n squared) is quadratic. Complexity analysis helps compare algorithms independently of a particular computer's clock speed.",
    "A hash table uses a hash function to map keys to table positions, supporting expected near-constant-time lookup, insertion, and deletion when the hash function and load factor are suitable. Different keys may map to the same position; this is a collision. Separate chaining stores multiple entries in a bucket, while open addressing searches for another available slot within the table.",
    "A tree represents hierarchical relationships through nodes and edges. A binary tree has at most two children per node. In a binary search tree, keys in the left subtree are smaller than the node's key and keys in the right subtree are larger, subject to the chosen duplicate-key policy. Search performance depends on tree height; a badly skewed tree can degrade to O(n).",
    "A graph consists of vertices and edges and can model relationships such as roads, social connections, and network links. Graphs may be directed or undirected and weighted or unweighted. An adjacency list stores each vertex's neighbours and is often space-efficient for sparse graphs; an adjacency matrix uses a table and supports checking whether a particular edge exists in constant time."
]


def build_sample_chunks() -> list[Chunk]:
    """Return a tiny original, page-labelled corpus for a click-to-try demo."""
    return [
        Chunk(
            chunk_id=f"sample-p{page}-c0",
            text=text,
            source=SAMPLE_SOURCE,
            page=page,
            chunk_index=0,
        )
        for page, text in enumerate(_SAMPLE_PAGES, start=1)
    ]


def build_sample_index() -> HybridIndex:
    return HybridIndex(build_sample_chunks())


def upload_collection_signature(uploaded_files: list[Any] | None) -> tuple[tuple[str, str], ...]:
    """Fingerprint selected upload names and bytes for Streamlit session-state checks."""
    return tuple(
        (str(upload.name), hashlib.sha256(upload.getvalue()).hexdigest())
        for upload in (uploaded_files or [])
    )


def save_uploaded_pdfs(uploaded_files: list[Any], output_dir: str | Path) -> list[Path]:
    """Safely copy uploaded PDF bytes under sanitized, unique filenames."""
    if not uploaded_files:
        raise ValueError("Upload at least one PDF file.")

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    used_names: set[str] = set()
    saved: list[Path] = []

    for item in uploaded_files:
        raw_name = str(getattr(item, "name", "document.pdf")).replace("\\", "/")
        filename = PurePosixPath(raw_name).name
        if not filename or filename in {".", ".."}:
            raise ValueError("A file has an invalid filename.")
        if not filename.lower().endswith(".pdf"):
            raise ValueError(f"Only PDF files are supported: {filename}")

        payload = item.getvalue()
        if not isinstance(payload, (bytes, bytearray)) or not payload:
            raise ValueError(f"The uploaded file is empty or unreadable: {filename}")
        total_bytes += len(payload)
        if total_bytes > MAX_UPLOAD_BYTES:
            raise ValueError("Combined uploads must be 20 MB or smaller.")
        if b"%PDF-" not in bytes(payload[:1024]):
            raise ValueError(f"The uploaded file does not have a valid PDF header: {filename}")

        original = Path(filename)
        candidate = filename
        suffix = 2
        while candidate.casefold() in used_names:
            candidate = f"{original.stem}-{suffix}{original.suffix}"
            suffix += 1
        used_names.add(candidate.casefold())

        destination = root / candidate
        destination.write_bytes(bytes(payload))
        saved.append(destination)

    return saved


def build_index_from_uploads(uploaded_files: list[Any]) -> tuple[HybridIndex, int]:
    """Extract uploaded PDFs and return an index; temporary PDF files are cleaned."""
    with tempfile.TemporaryDirectory(prefix="skillcraft-rag-demo-") as temporary:
        save_uploaded_pdfs(uploaded_files, temporary)
        chunks = ingest_pdfs(temporary)
        index = HybridIndex(chunks)
    return index, len(chunks)


def build_comparison_csv(
    question: str,
    source_label: str,
    report: dict[str, Any],
) -> str:
    """Serialize retrieval results and method failures to an Excel-friendly CSV."""
    method_labels = {
        "hybrid": "Combined search (Hybrid RRF)",
        "dense": "Search by meaning (Dense)",
        "bm25": "Search by keywords (BM25)",
    }
    fields = [
        "question",
        "selected_material",
        "search_method",
        "status",
        "rank",
        "score",
        "source",
        "page",
        "citation",
        "passage",
        "retrieval_note",
    ]
    rows: list[dict[str, object]] = []
    errors = report.get("_errors", {})

    for method in ("hybrid", "dense", "bm25"):
        results = report.get(method, [])
        if results:
            for item in results:
                rows.append({
                    "question": question.strip(),
                    "selected_material": source_label,
                    "search_method": method_labels[method],
                    "status": "result",
                    "rank": item.get("rank", ""),
                    "score": item.get("score", ""),
                    "source": item.get("source", ""),
                    "page": item.get("page", ""),
                    "citation": item.get("citation", "Citation unavailable"),
                    "passage": str(item.get("text", "")).strip(),
                    "retrieval_note": "",
                })
        else:
            error = str(errors.get(method, "")).strip()
            rows.append({
                "question": question.strip(),
                "selected_material": source_label,
                "search_method": method_labels[method],
                "status": "error" if error else "no_results",
                "rank": "",
                "score": "",
                "source": "",
                "page": "",
                "citation": "",
                "passage": "",
                "retrieval_note": error,
            })

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def compare_retrievers(index: Any, question: str, top_k: int = 5) -> dict[str, Any]:
    """Run retrieval independently so one optional method cannot hide others.

    ``_errors`` contains safe, user-facing method failures. Detailed exceptions
    are logged server-side without document or question content.
    """
    clean_question = question.strip() if isinstance(question, str) else ""
    if not clean_question:
        raise ValueError("Enter a question before running retrieval.")
    if type(top_k) is not int or not 1 <= top_k <= 10:
        raise ValueError("top_k must be an integer between 1 and 10.")

    report: dict[str, Any] = {"bm25": [], "dense": [], "hybrid": []}
    errors: dict[str, str] = {}

    def run(name: str, method, requested_k: int) -> list[Any]:
        try:
            return method(clean_question, top_k=requested_k)
        except Exception as exc:
            # Model/dependency stacks expose heterogeneous exceptions. Log a
            # concise diagnostic and keep independent retrieval methods usable.
            logger.warning("Retrieval method %s failed (%s): %s", name, type(exc).__name__, exc)
            if name in {"dense", "hybrid"}:
                errors[name] = (
                    "Semantic search is unavailable right now. Check model installation/network access, "
                    "then retry; keyword results may still be available."
                )
            else:
                errors[name] = "Keyword search could not complete. Check the index and try again."
            return []

    if isinstance(index, HybridIndex):
        # Use a shared candidate set so semantic query embeddings are computed
        # once, not again inside hybrid search. Keep a wider candidate pool for RRF.
        candidate_k = max(20, top_k)
        lexical = run("bm25", index.search_bm25, candidate_k)
        semantic = run("dense", index.search_dense, candidate_k)
        report["bm25"] = [result.to_dict() for result in lexical[:top_k]]
        report["dense"] = [result.to_dict() for result in semantic[:top_k]]
        if not errors:
            fused = index.fuse_rrf([lexical, semantic], top_k=top_k)
            report["hybrid"] = [result.to_dict() for result in fused]
        else:
            errors["hybrid"] = "Hybrid search is unavailable because one of its retrieval methods failed."
    else:
        # Generic test doubles and alternate index adapters may expose their
        # own fusion implementation instead of the built-in shared-candidate path.
        methods = {
            "bm25": index.search_bm25,
            "dense": index.search_dense,
            "hybrid": index.search_hybrid,
        }
        for name, method in methods.items():
            if name == "hybrid" and "dense" in errors:
                errors[name] = "Hybrid search is unavailable because dense semantic retrieval failed."
                continue
            report[name] = [result.to_dict() for result in run(name, method, top_k)]

    report["_errors"] = errors
    return report
