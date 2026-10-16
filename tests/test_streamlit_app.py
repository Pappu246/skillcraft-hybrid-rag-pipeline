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
