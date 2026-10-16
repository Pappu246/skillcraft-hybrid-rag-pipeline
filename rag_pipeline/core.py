"""Core ingestion and retrieval primitives for the internship RAG project."""
from __future__ import annotations

import json
import math
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
from pypdf import PdfReader
from rank_bm25 import BM25Okapi

TOKEN_RE = re.compile(r"[\w'-]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


@dataclass
class Chunk:
    chunk_id: str
    text: str
    source: str
    page: int
    chunk_index: int

    @property
    def citation(self) -> str:
        return f"[{self.source}, p. {self.page}]"


@dataclass
class SearchResult:
    chunk: Chunk
    score: float
    rank: int
    method: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk.chunk_id,
            "text": self.chunk.text,
            "source": self.chunk.source,
            "page": self.chunk.page,
            "citation": self.chunk.citation,
            "score": round(float(self.score), 6),
            "rank": self.rank,
            "method": self.method,
        }


def chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Split text into character windows, preferring whitespace boundaries."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and smaller than chunk_size")
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        if end < len(normalized):
            boundary = normalized.rfind(" ", start + chunk_size // 2, end)
            if boundary > start:
                end = boundary
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(normalized):
            break
        start = max(start + 1, end - overlap)
    return chunks


def ingest_pdfs(input_dir: str | Path, *, chunk_size: int = 900, overlap: int = 150) -> list[Chunk]:
    root = Path(input_dir)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {root}")
    pdf_paths = sorted(root.glob("*.pdf"))
    if not pdf_paths:
        raise ValueError(f"No PDF files found in {root}. Add at least one PDF first.")

    all_chunks: list[Chunk] = []
    for pdf_path in pdf_paths:
        reader = PdfReader(str(pdf_path))
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            for idx, piece in enumerate(chunk_text(text, chunk_size=chunk_size, overlap=overlap)):
                all_chunks.append(
                    Chunk(
                        chunk_id=f"{pdf_path.stem}-p{page_num}-c{idx}",
                        text=piece,
                        source=pdf_path.name,
                        page=page_num,
                        chunk_index=idx,
                    )
                )
    if not all_chunks:
        raise ValueError("PDFs were found, but no selectable text was extracted. Scanned PDFs require OCR.")
    return all_chunks


class HybridIndex:
    """In-memory BM25 + dense index. Persisted chunks are portable JSON."""

    def __init__(
        self,
        chunks: list[Chunk],
        *,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        reranker_model: str | None = None,
    ) -> None:
        if not chunks:
            raise ValueError("Cannot build an index without chunks")
        self.chunks = chunks
        self.embedding_model_name = embedding_model
        self.reranker_model_name = reranker_model
        self._bm25 = BM25Okapi([tokenize(c.text) or ["_empty_"] for c in chunks])
        self._model = None
        self._embeddings: np.ndarray | None = None
        self._reranker = None

    def _load_encoder(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.embedding_model_name)
        return self._model

    def _load_reranker(self):
        if not self.reranker_model_name:
            return None
        if self._reranker is None:
            from sentence_transformers import CrossEncoder
            self._reranker = CrossEncoder(self.reranker_model_name)
        return self._reranker

    def build_dense(self) -> None:
        if self._embeddings is None:
            model = self._load_encoder()
            vectors = model.encode([c.text for c in self.chunks], normalize_embeddings=True, show_progress_bar=True)
            self._embeddings = np.asarray(vectors, dtype=np.float32)

    def search_bm25(self, query: str, *, top_k: int = 5) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        tokens = tokenize(query)
        if not tokens:
            return []
        scores = np.asarray(self._bm25.get_scores(tokens), dtype=float)
        order = np.argsort(-scores, kind="stable")[:top_k]
        return [SearchResult(self.chunks[int(i)], float(scores[i]), rank + 1, "bm25") for rank, i in enumerate(order)]

    def search_dense(self, query: str, *, top_k: int = 5) -> list[SearchResult]:
        if top_k < 1:
            raise ValueError("top_k must be positive")
        self.build_dense()
        qv = self._load_encoder().encode([query], normalize_embeddings=True)
        scores = self._embeddings @ np.asarray(qv[0], dtype=np.float32)
        order = np.argsort(-scores, kind="stable")[:top_k]
        return [SearchResult(self.chunks[int(i)], float(scores[i]), rank + 1, "dense") for rank, i in enumerate(order)]

    @staticmethod
    def fuse_rrf(result_lists: list[list[SearchResult]], *, top_k: int = 5, k: int = 60) -> list[SearchResult]:
        fused: dict[str, float] = {}
        by_id: dict[str, Chunk] = {}
        for results in result_lists:
            for result in results:
                cid = result.chunk.chunk_id
                by_id[cid] = result.chunk
                fused[cid] = fused.get(cid, 0.0) + 1.0 / (k + result.rank)
        ordered = sorted(fused, key=lambda cid: (-fused[cid], cid))[:top_k]
        return [SearchResult(by_id[cid], fused[cid], rank + 1, "hybrid_rrf") for rank, cid in enumerate(ordered)]

    def search_hybrid(self, query: str, *, top_k: int = 5, candidate_k: int = 20, rerank: bool = False) -> list[SearchResult]:
        lexical = self.search_bm25(query, top_k=max(candidate_k, top_k))
        dense = self.search_dense(query, top_k=max(candidate_k, top_k))
        fused = self.fuse_rrf([lexical, dense], top_k=max(candidate_k, top_k))
        if rerank:
            model = self._load_reranker()
            if model is None:
                raise ValueError("Reranking requested but no reranker model was configured")
            pairs = [(query, result.chunk.text) for result in fused]
            scores = model.predict(pairs)
            fused = [
                SearchResult(result.chunk, float(score), 0, "cross_encoder")
                for result, score in zip(fused, scores)
            ]
            fused.sort(key=lambda r: -r.score)
            fused = [SearchResult(r.chunk, r.score, i + 1, r.method) for i, r in enumerate(fused)]
        return fused[:top_k]

    def save(self, index_dir: str | Path) -> None:
        target = Path(index_dir)
        target.mkdir(parents=True, exist_ok=True)
        payload = {
            "embedding_model": self.embedding_model_name,
            "reranker_model": self.reranker_model_name,
            "chunks": [asdict(chunk) for chunk in self.chunks],
        }
        (target / "chunks.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, index_dir: str | Path) -> "HybridIndex":
        path = Path(index_dir) / "chunks.json"
        if not path.exists():
            raise FileNotFoundError(f"Index file not found: {path}. Run ingest first.")
        payload = json.loads(path.read_text(encoding="utf-8"))
        chunks = [Chunk(**item) for item in payload["chunks"]]
        return cls(chunks, embedding_model=payload.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2"),
                   reranker_model=payload.get("reranker_model"))


def retrieve_comparison(
    index: HybridIndex,
    question: str,
    *,
    top_k: int = 5,
    repeats: int = 3,
) -> dict[str, Any]:
    """Compare retrieval latency after one warm-up, reporting median timed latency.

    This measures warmed retrieval latency within this process, not cold-start
    latency, model-download time, or retrieval accuracy.
    """
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if repeats < 1:
        raise ValueError("repeats must be positive")

    methods = {
        "bm25": index.search_bm25,
        "dense": index.search_dense,
        "hybrid": index.search_hybrid,
    }

    # Warm every method before collecting timings so first-use model/embedding
    # initialization does not unfairly dominate only the dense and hybrid rows.
    for method in methods.values():
        method(question, top_k=top_k)

    report: dict[str, Any] = {
        "question": question,
        "top_k": top_k,
        "benchmark": {
            "warmup_runs_per_method": 1,
            "timed_runs_per_method": repeats,
            "latency_statistic": "median",
            "latency_scope": "warmed retrieval only; excludes cold-start initialization",
        },
        "methods": {},
    }
    for name, method in methods.items():
        timings: list[float] = []
        results: list[SearchResult] = []
        for _ in range(repeats):
            started = time.perf_counter()
            results = method(question, top_k=top_k)
            timings.append((time.perf_counter() - started) * 1000)
        report["methods"][name] = {
            "latency_ms": round(float(np.median(timings)), 3),
            "latency_runs_ms": [round(value, 3) for value in timings],
            "results": [result.to_dict() for result in results],
        }
    return report


def format_context(results: list[SearchResult]) -> str:
    blocks = []
    for result in results:
        blocks.append(f"Source: {result.chunk.citation}\n{result.chunk.text}")
    return "\n\n---\n\n".join(blocks)


def generate_answer(question: str, results: list[SearchResult]) -> str:
    """Use an OpenAI-compatible endpoint if configured; otherwise return cited context."""
    import os
    import requests

    api_key = os.getenv("RAG_API_KEY")
    base_url = os.getenv("RAG_API_BASE_URL", "").rstrip("/")
    model = os.getenv("RAG_MODEL")
    context = format_context(results)
    if not (api_key and base_url and model):
        return (
            "Generation is not configured, so no model-generated answer was produced. "
            "Use the cited evidence below to answer the question:\n\n" + context
        )
    endpoint = base_url if base_url.endswith("/chat/completions") else base_url + "/chat/completions"
    response = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": (
                    "Answer only using the supplied evidence. If evidence is insufficient, say so. "
                    "Cite factual statements using the exact source labels such as [paper.pdf, p. 2]. "
                    "Never invent citations or claim that you read content not present in the context."
                )},
                {"role": "user", "content": f"Question: {question}\n\nEvidence:\n{context}"},
            ],
        },
        timeout=60,
    )
    response.raise_for_status()
    payload = response.json()
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Provider response did not contain choices[0].message.content") from exc
