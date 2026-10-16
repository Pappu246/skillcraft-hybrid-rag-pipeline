from rag_pipeline.core import Chunk, HybridIndex, chunk_text, format_context, tokenize


def test_tokenize_is_case_insensitive():
    assert tokenize("Hybrid RAG pipeline") == ["hybrid", "rag", "pipeline"]


def test_chunk_text_empty_and_overlap():
    assert chunk_text("   ") == []
    text = "alpha beta gamma delta epsilon zeta eta theta"
    chunks = chunk_text(text, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    assert all(chunks)


def test_chunk_text_rejects_invalid_overlap():
    try:
        chunk_text("hello", chunk_size=10, overlap=10)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_rrf_fuses_rankings_and_keeps_provenance():
    a = Chunk("a", "alpha evidence", "a.pdf", 2, 0)
    b = Chunk("b", "beta evidence", "b.pdf", 1, 0)
    lexical = [
        __import__("rag_pipeline.core", fromlist=["SearchResult"]).SearchResult(a, 4.0, 1, "bm25"),
        __import__("rag_pipeline.core", fromlist=["SearchResult"]).SearchResult(b, 2.0, 2, "bm25"),
    ]
    dense = [
        __import__("rag_pipeline.core", fromlist=["SearchResult"]).SearchResult(b, 0.8, 1, "dense"),
        __import__("rag_pipeline.core", fromlist=["SearchResult"]).SearchResult(a, 0.7, 2, "dense"),
    ]
    fused = HybridIndex.fuse_rrf([lexical, dense], top_k=2)
    assert {r.chunk.chunk_id for r in fused} == {"a", "b"}
    assert fused[0].score > 0
    assert all(r.chunk.citation for r in fused)


def test_context_includes_source_and_page():
    chunk = Chunk("x", "Evidence text", "paper.pdf", 3, 0)
    from rag_pipeline.core import SearchResult
    context = format_context([SearchResult(chunk, 1.0, 1, "test")])
    assert "[paper.pdf, p. 3]" in context
    assert "Evidence text" in context


def test_comparison_warms_up_and_reports_median_latency(monkeypatch):
    from types import SimpleNamespace
    import rag_pipeline.core as core

    calls = {"bm25": 0, "dense": 0, "hybrid": 0}

    def method(name):
        def search(question, *, top_k):
            calls[name] += 1
            return []
        return search

    index = SimpleNamespace(
        search_bm25=method("bm25"),
        search_dense=method("dense"),
        search_hybrid=method("hybrid"),
    )
    # Three timed durations per method: BM25 1/4/8 ms, dense 2/5/9 ms,
    # hybrid 3/6/10 ms. Warm-ups do not consume clock ticks.
    milliseconds = [0, 1, 2, 6, 7, 15, 20, 22, 30, 35, 40, 49, 50, 53, 60, 66, 70, 80]
    ticks = iter(value / 1000 for value in milliseconds)
    monkeypatch.setattr(core.time, "perf_counter", lambda: next(ticks))

    report = core.retrieve_comparison(index, "question", top_k=2, repeats=3)

    assert calls == {"bm25": 4, "dense": 4, "hybrid": 4}
    assert report["benchmark"]["warmup_runs_per_method"] == 1
    assert report["benchmark"]["timed_runs_per_method"] == 3
    assert report["benchmark"]["latency_statistic"] == "median"
    assert report["methods"]["bm25"]["latency_ms"] == 4.0
    assert report["methods"]["dense"]["latency_ms"] == 5.0
    assert report["methods"]["hybrid"]["latency_ms"] == 6.0
    assert report["methods"]["bm25"]["latency_runs_ms"] == [1.0, 4.0, 8.0]


def test_comparison_rejects_invalid_repeat_count():
    from types import SimpleNamespace
    from rag_pipeline.core import retrieve_comparison

    index = SimpleNamespace(
        search_bm25=lambda question, *, top_k: [],
        search_dense=lambda question, *, top_k: [],
        search_hybrid=lambda question, *, top_k: [],
    )
    try:
        retrieve_comparison(index, "question", repeats=0)
    except ValueError as exc:
        assert "repeats must be positive" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
