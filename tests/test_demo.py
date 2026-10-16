from pathlib import Path

import pytest

from rag_pipeline.demo import (
    MAX_UPLOAD_BYTES,
    SAMPLE_SOURCE,
    build_sample_chunks,
    save_uploaded_pdfs,
)


class FakeUpload:
    def __init__(self, name: str, payload: bytes):
        self.name = name
        self._payload = payload

    def getvalue(self) -> bytes:
        return self._payload


def test_sample_corpus_has_unique_page_provenance():
    chunks = build_sample_chunks()
    assert len(chunks) >= 6
    assert all(chunk.source == SAMPLE_SOURCE for chunk in chunks)
    assert [chunk.page for chunk in chunks] == list(range(1, len(chunks) + 1))
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)


def test_uploaded_pdf_names_are_sanitized_and_duplicate_names_are_unique(tmp_path):
    uploaded = [
        FakeUpload("../../notes.pdf", b"%PDF sample one"),
        FakeUpload("notes.pdf", b"%PDF sample two"),
    ]
    paths = save_uploaded_pdfs(uploaded, tmp_path)

    assert [p.name for p in paths] == ["notes.pdf", "notes-2.pdf"]
    assert all(p.parent == Path(tmp_path) for p in paths)
    assert paths[0].read_bytes() == b"%PDF sample one"
    assert paths[1].read_bytes() == b"%PDF sample two"


@pytest.mark.parametrize("name", ["notes.txt", "../no-extension", ""])
def test_uploaded_files_must_be_pdfs(tmp_path, name):
    with pytest.raises(ValueError, match="PDF|filename"):
        save_uploaded_pdfs([FakeUpload(name, b"content")], tmp_path)


def test_uploaded_payload_size_is_limited(tmp_path):
    fake = FakeUpload("large.pdf", b"x" * (MAX_UPLOAD_BYTES + 1))
    with pytest.raises(ValueError, match="20 MB"):
        save_uploaded_pdfs([fake], tmp_path)


def test_empty_upload_list_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="at least one PDF"):
        save_uploaded_pdfs([], tmp_path)

def test_sample_corpus_bm25_retrieval_cites_the_relevant_page():
    from rag_pipeline.demo import build_sample_index

    index = build_sample_index()
    results = index.search_bm25("How does binary search reduce search time?", top_k=3)

    assert results
    assert results[0].chunk.page == 4
    assert results[0].chunk.source == SAMPLE_SOURCE
    assert results[0].chunk.citation == f"[{SAMPLE_SOURCE}, p. 4]"
