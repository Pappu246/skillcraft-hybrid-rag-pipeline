"""Small helpers used by the interactive Streamlit demo.

The built-in guide is original demonstration content. User-uploaded PDFs are
extracted into in-memory chunks; their temporary upload files are removed as
soon as indexing finishes.
"""
from __future__ import annotations

from pathlib import Path, PurePosixPath
import tempfile
from typing import Any

from .core import Chunk, HybridIndex, SearchResult, ingest_pdfs

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


def compare_retrievers(index: Any, question: str, top_k: int = 5) -> dict[str, list[dict[str, Any]]]:
    """Return top-k source-bearing result dictionaries for each retrieval method."""
    clean_question = question.strip()
    if not clean_question:
        raise ValueError("Enter a question before running retrieval.")
    if type(top_k) is not int or not 1 <= top_k <= 10:
        raise ValueError("top_k must be an integer between 1 and 10.")

    methods = {
        "bm25": index.search_bm25,
        "dense": index.search_dense,
        "hybrid": index.search_hybrid,
    }
    return {
        name: [result.to_dict() for result in method(clean_question, top_k=top_k)]
        for name, method in methods.items()
    }
