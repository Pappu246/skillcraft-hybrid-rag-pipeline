from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_streamlit_demo_renders_user_friendly_ui_without_llm_credentials():
    app_path = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()

    assert not app.exception
    rendered_markdown = "\n".join(str(element.value) for element in app.markdown)
    assert "Find cited evidence in your documents" in rendered_markdown
    assert "AI-written responses are optional" in rendered_markdown
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
    assert any(item.label == "Download comparison CSV (.csv)" for item in downloads)

    recent_button = next(item for item in app.button if item.label.startswith("Use recent query:"))
    recent_button.click().run()
    assert not app.exception
    assert app.text_input[0].value == "binary search"
    assert "Best matching passage" not in "\\n".join(str(item.value) for item in app.markdown)

    clear_button = next(item for item in app.button if item.label == "Clear search results")
    clear_button.click().run()
    assert not app.exception
    assert app.text_input[0].value == ""
    assert "Best matching passage" not in "\\n".join(str(item.value) for item in app.markdown)

def test_streamlit_source_filter_limits_visible_evidence_and_resets_for_new_query(monkeypatch):
    import rag_pipeline.demo as demo

    def multi_source_report(_index, _question, _top_k):
        return {
            "hybrid": [
                {
                    "chunk_id": "alpha", "text": "Evidence from alpha source.",
                    "source": "alpha.pdf", "page": 1, "citation": "[alpha.pdf, p. 1]",
                    "score": 0.9, "rank": 1, "method": "hybrid",
                },
                {
                    "chunk_id": "beta", "text": "Evidence from beta source.",
                    "source": "beta.pdf", "page": 2, "citation": "[beta.pdf, p. 2]",
                    "score": 0.8, "rank": 2, "method": "hybrid",
                },
            ],
            "dense": [
                {
                    "chunk_id": "beta-dense", "text": "Semantic evidence from beta source.",
                    "source": "beta.pdf", "page": 2, "citation": "[beta.pdf, p. 2]",
                    "score": 0.7, "rank": 1, "method": "dense",
                },
            ],
            "bm25": [],
            "_errors": {},
        }

    monkeypatch.setattr(demo, "compare_retrievers", multi_source_report)
    app_path = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    app = AppTest.from_file(str(app_path), default_timeout=30).run()
    app.text_input[0].set_value("find evidence")
    app.get("form_submit_button")[0].click().run()

    assert not app.exception
    source_filter = next(item for item in app.selectbox if item.label == "Limit evidence to source")
    assert source_filter.value == "All sources"
    source_filter.select("beta.pdf").run()

    assert not app.exception
    rendered = "\\n".join(
        [str(item.value) for item in app.markdown]
        + [str(item.value) for item in app.text]
        + [str(item.value) for item in app.caption]
    )
    assert "[beta.pdf, p. 2]" in rendered
    assert "Evidence from beta source." in rendered
    assert "Evidence from alpha source." not in rendered

    app.text_input[0].set_value("new question")
    app.get("form_submit_button")[0].click().run()
    assert not app.exception
    source_filter = next(item for item in app.selectbox if item.label == "Limit evidence to source")
    assert source_filter.value == "All sources"
