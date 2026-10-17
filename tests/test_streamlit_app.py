from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_demo_renders_user_friendly_ui_without_llm_credentials():
    app_path = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()

    assert not app.exception
    rendered_markdown = "\n".join(str(element.value) for element in app.markdown)
    assert "Find answers in your documents" in rendered_markdown
    assert "Ask a question" in rendered_markdown
    assert "Best matching passage" not in rendered_markdown
    assert len(app.text_input) >= 1


def test_streamlit_config_disables_transformers_watcher_traceback_noise():
    root = Path(__file__).resolve().parents[1]
    config = (root / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert 'fileWatcherType = "none"' in config


def test_streamlit_query_shows_cited_bm25_fallback_when_dense_search_fails(monkeypatch):
    import rag_pipeline.demo as demo

    def partial_report(_index, _question, _top_k):
        return {
            "bm25": [{
                "chunk_id": "evidence-1",
                "text": "Binary search repeatedly halves the remaining interval.",
                "source": "Guide.pdf",
                "page": 4,
                "citation": "[Guide.pdf, p. 4]",
                "score": 2.1,
                "rank": 1,
                "method": "bm25",
            }],
            "dense": [],
            "hybrid": [],
            "_errors": {"dense": "Semantic search is unavailable in this test.", "hybrid": "Semantic search is unavailable in this test."},
        }

    monkeypatch.setattr(demo, "compare_retrievers", partial_report)
    app_path = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()
    app.text_input[0].set_value("binary search")
    app.get("form_submit_button")[0].click().run()

    assert not app.exception
    rendered_markdown = "\n".join(str(element.value) for element in app.markdown)
    assert "[Guide.pdf, p. 4]" in rendered_markdown
    assert "Binary search repeatedly halves" in rendered_markdown
    assert any("higher-priority method was unavailable" in item.value for item in app.caption)
    assert any("Semantic search is unavailable" in item.value for item in app.warning)

    downloads = app.get("download_button")
    assert any(item.label == "Download evidence report (.md)" for item in downloads)

    clear_button = next(item for item in app.button if item.label == "Clear search results")
    clear_button.click().run()
    assert not app.exception
    assert app.text_input[0].value == ""
    assert "Best matching passage" not in "\\n".join(str(item.value) for item in app.markdown)
