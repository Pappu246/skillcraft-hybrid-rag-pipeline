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
        FakeUpload("../../notes.pdf", b"%PDF-1.4 sample one"),
        FakeUpload("notes.pdf", b"%PDF-1.4 sample two"),
    ]
    paths = save_uploaded_pdfs(uploaded, tmp_path)

    assert [p.name for p in paths] == ["notes.pdf", "notes-2.pdf"]
    assert all(p.parent == Path(tmp_path) for p in paths)
    assert paths[0].read_bytes() == b"%PDF-1.4 sample one"
    assert paths[1].read_bytes() == b"%PDF-1.4 sample two"


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

@pytest.mark.parametrize(
    "question, expected_page",
    [
        ("How does binary search reduce search time?", 4),
        ("How does a hash table handle collisions?", 6),
    ],
)
def test_sample_corpus_keyword_retrieval_cites_relevant_physical_page(question, expected_page):
    from rag_pipeline.demo import build_sample_index

    index = build_sample_index()
    results = index.search_bm25(question, top_k=3)

    assert results
    assert results[0].chunk.page == expected_page
    assert results[0].chunk.source == SAMPLE_SOURCE
    assert results[0].chunk.citation == f"[{SAMPLE_SOURCE}, p. {expected_page}]"


def test_upload_rejects_non_pdf_bytes_even_with_pdf_extension(tmp_path):
    with pytest.raises(ValueError, match="valid PDF header"):
        save_uploaded_pdfs([FakeUpload("fake.pdf", b"not a PDF")], tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_uploaded_temp_directory_is_cleaned_when_pdf_ingestion_fails(monkeypatch):
    import rag_pipeline.demo as demo

    observed = {}

    def fail_ingestion(path):
        observed["path"] = Path(path)
        assert list(Path(path).glob("*.pdf"))
        raise ValueError("Could not read 'broken.pdf': malformed PDF")

    monkeypatch.setattr(demo, "ingest_pdfs", fail_ingestion)
    with pytest.raises(ValueError, match="broken.pdf"):
        demo.build_index_from_uploads([FakeUpload("broken.pdf", b"%PDF-1.4 malformed")])
    assert "path" in observed
    assert not observed["path"].exists()


def test_comparison_keeps_keyword_results_when_dense_and_hybrid_fail(caplog):
    from types import SimpleNamespace
    from rag_pipeline.core import Chunk, SearchResult
    from rag_pipeline.demo import compare_retrievers

    result = SearchResult(Chunk("a", "keyword evidence", "notes.pdf", 2, 0), 1.0, 1, "bm25")

    def unavailable(*args, **kwargs):
        raise RuntimeError("model download failed")

    report = compare_retrievers(
        SimpleNamespace(
            search_bm25=lambda *args, **kwargs: [result],
            search_dense=unavailable,
            search_hybrid=unavailable,
        ),
        "question",
    )

    assert report["bm25"][0]["citation"] == "[notes.pdf, p. 2]"
    assert report["dense"] == []
    assert report["hybrid"] == []
    assert set(report["_errors"]) == {"dense", "hybrid"}
    assert "Semantic search is unavailable" in report["_errors"]["dense"]


def test_valid_text_pdf_upload_indexes_selectable_text_with_physical_page_citation(tmp_path):
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
    from rag_pipeline.demo import build_index_from_uploads

    pdf_path = tmp_path / "two-pages.pdf"
    writer = PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    font_ref = writer._add_object(font)
    resources = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})
    })
    for page_text in ("A cover page about course notes.", "Binary search repeatedly halves the sorted search interval."):
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = resources
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 72 720 Td ({page_text}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(stream)
    with pdf_path.open("wb") as output:
        writer.write(output)

    index, chunk_count = build_index_from_uploads(
        [FakeUpload("two-pages.pdf", pdf_path.read_bytes())]
    )
    results = index.search_bm25("How does binary search reduce the interval?", top_k=2)
    assert chunk_count == 2
    assert results[0].chunk.page == 2
    assert results[0].chunk.citation == "[two-pages.pdf, p. 2]"


def test_upload_collection_signature_changes_when_file_bytes_change():
    from rag_pipeline.demo import upload_collection_signature

    original = upload_collection_signature([FakeUpload("notes.pdf", b"%PDF-1.4 original")])
    changed_bytes = upload_collection_signature([FakeUpload("notes.pdf", b"%PDF-1.4 revised")])
    changed_name = upload_collection_signature([FakeUpload("new-notes.pdf", b"%PDF-1.4 original")])
    assert original != changed_bytes
    assert original != changed_name
    assert upload_collection_signature(None) == ()


def test_comparison_reuses_single_dense_query_embedding_for_hybrid():
    import numpy as np
    from rag_pipeline.core import Chunk, HybridIndex
    from rag_pipeline.demo import compare_retrievers

    class CountingEncoder:
        def __init__(self):
            self.query_calls = 0

        def encode(self, texts, **kwargs):
            if texts == ["query"]:
                self.query_calls += 1
                return np.asarray([[1.0, 0.0]], dtype=np.float32)
            return np.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)

    index = HybridIndex([
        Chunk("a", "query evidence", "guide.pdf", 1, 0),
        Chunk("b", "other text", "guide.pdf", 2, 0),
    ])
    encoder = CountingEncoder()
    index._model = encoder

    report = compare_retrievers(index, "query", top_k=2)

    assert encoder.query_calls == 1
    assert report["hybrid"]
    assert report["hybrid"][0]["citation"] == "[guide.pdf, p. 1]"


def test_build_comparison_csv_preserves_citations_and_reports_method_failures():
    import csv
    import io
    from rag_pipeline.demo import build_comparison_csv

    report = {
        "hybrid": [{
            "rank": 1,
            "score": 0.91,
            "source": "guide.pdf",
            "page": 2,
            "citation": "[guide.pdf, p. 2]",
            "text": 'A comma, quoted phrase ("example"), and newline.\\nSecond line.',
            "method": "hybrid",
        }],
        "dense": [],
        "bm25": [{
            "rank": 1,
            "score": 2.4,
            "source": "guide.pdf",
            "page": 3,
            "citation": "[guide.pdf, p. 3]",
            "text": "Keyword evidence.",
            "method": "bm25",
        }],
        "_errors": {"dense": "Semantic model unavailable."},
    }

    exported = build_comparison_csv(
        "  How does this work?  ",
        "My notes",
        report,
    )
    rows = list(csv.DictReader(io.StringIO(exported)))

    assert len(rows) == 3
    assert rows[0]["search_method"] == "Combined search (Hybrid RRF)"
    assert rows[0]["status"] == "result"
    assert rows[0]["question"] == "How does this work?"
    assert rows[0]["selected_material"] == "My notes"
    assert rows[0]["citation"] == "[guide.pdf, p. 2]"
    assert rows[0]["passage"] == 'A comma, quoted phrase ("example"), and newline.\\nSecond line.'
    assert rows[1]["search_method"] == "Search by meaning (Dense)"
    assert rows[1]["status"] == "error"
    assert rows[1]["retrieval_note"] == "Semantic model unavailable."
    assert rows[2]["status"] == "result"
    assert rows[2]["source"] == "guide.pdf"
    assert rows[2]["page"] == "3"


def test_build_comparison_csv_marks_empty_methods_without_errors_as_no_results():
    import csv
    import io
    from rag_pipeline.demo import build_comparison_csv

    rows = list(csv.DictReader(io.StringIO(
        build_comparison_csv("question", "Sample", {"hybrid": [], "dense": [], "bm25": []})
    )))
    assert len(rows) == 3
    assert all(row["status"] == "no_results" for row in rows)
