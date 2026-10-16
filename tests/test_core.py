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
