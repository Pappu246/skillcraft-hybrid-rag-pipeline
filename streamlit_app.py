"""User-friendly web demo for the SkillCraft Hybrid RAG pipeline."""
from __future__ import annotations

import html
import inspect
import logging
import os

import pandas as pd
import streamlit as st

from rag_pipeline.core import MAX_PDF_PAGES, Chunk, SearchResult, generate_answer
from rag_pipeline.demo import (
    MAX_UPLOAD_BYTES,
    build_comparison_csv,
    build_index_from_uploads,
    build_sample_index,
    compare_retrievers,
    upload_collection_signature,
)

logger = logging.getLogger(__name__)


def _stretch_width(widget) -> dict[str, object]:
    """Use Streamlit's non-deprecated full-width option across supported versions."""
    if "width" in inspect.signature(widget).parameters:
        return {"width": "stretch"}
    return {"use_container_width": True}


st.set_page_config(
    page_title="SkillCraft | Document Search",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      :root { color-scheme: dark; }
      .stApp { background: #0b1020; color: #edf2ff; }
      [data-testid="stSidebar"] { background: #111a30; }
      [data-testid="stMarkdownContainer"] p,
      [data-testid="stMarkdownContainer"] li,
      [data-testid="stWidgetLabel"] p { font-size: 1rem; line-height: 1.65; }
      [data-testid="stCaptionContainer"] p { font-size: .9rem; line-height: 1.5; }
      h1, h2, h3, h4 { letter-spacing: -.02em; }
      .hero { padding: 1.6rem 1.8rem; border: 1px solid #2d4164; border-radius: 20px;
              background: linear-gradient(125deg, #172d50 0%, #10192c 70%, #15223c 100%);
              margin: .3rem 0 1.4rem 0; }
      .hero-kicker { color: #9fc4ff; font-size: .82rem; font-weight: 800;
                     letter-spacing: .12em; text-transform: uppercase; }
      .hero h1 { color: #f5f8ff; margin: .45rem 0 .55rem 0; font-size: clamp(2rem, 4vw, 2.8rem); }
      .hero p { color: #d0dbee; max-width: 900px; margin: 0; font-size: 1.05rem; }
      .step { color: #9fc4ff; text-transform: uppercase; letter-spacing: .08em;
              font-size: .78rem; font-weight: 800; margin-bottom: .25rem; }
      .result-card { border: 1px solid #344b70; border-radius: 14px; padding: 1.25rem;
                     margin: .6rem 0; background: #111a2c; }
      .citation { color: #9fc4ff; font-size: 1rem; font-weight: 800; margin-bottom: .55rem; }
      .evidence-text { font-size: 1.02rem; line-height: 1.75; color: #edf2ff; }
      .subtle { color: #bac8df; font-size: .9rem; line-height: 1.6; }
      div[data-testid="stMetric"] { background: #111a2c; border: 1px solid #2a3855;
                                    padding: .8rem; border-radius: 12px; }
      .stButton > button, .stFormSubmitButton > button { min-height: 2.7rem;
                  border-radius: 10px; font-weight: 700; white-space: normal; }
      .stTextInput input { min-height: 3rem; font-size: 1rem; }
      button[kind="primary"] { border: 1px solid #8db8ff; }
      @media (max-width: 900px) {
        .hero { padding: 1.1rem; }
        .hero p { font-size: 1rem; }
      }
    </style>
    <div class="hero">
      <div class="hero-kicker">SkillCraft Technology · AI Engineering · Task 01</div>
      <h1>Find answers in your documents</h1>
      <p>Ask a question in everyday language. SkillCraft finds relevant passages and shows exactly which page they came from, so you can check the source yourself.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "sample_index" not in st.session_state:
    st.session_state.sample_index = build_sample_index()
if "uploaded_index" not in st.session_state:
    st.session_state.uploaded_index = None
if "uploaded_chunk_count" not in st.session_state:
    st.session_state.uploaded_chunk_count = 0
if "uploaded_signature" not in st.session_state:
    st.session_state.uploaded_signature = None
if "retrieval_report" not in st.session_state:
    st.session_state.retrieval_report = None
if "retrieval_question" not in st.session_state:
    st.session_state.retrieval_question = ""
if "retrieval_mode" not in st.session_state:
    st.session_state.retrieval_mode = ""
if "question_input" not in st.session_state:
    st.session_state.question_input = "How does binary search reduce search time?"
if "answer_text" not in st.session_state:
    st.session_state.answer_text = None
if "answer_question" not in st.session_state:
    st.session_state.answer_question = ""
if "recent_searches" not in st.session_state:
    st.session_state.recent_searches = []


def _use_suggestion(value: str) -> None:
    st.session_state.question_input = value
    st.session_state.answer_text = None


def _use_history_entry(question: str, source_mode_value: str) -> None:
    """Load a prior query into the current session without auto-running it."""
    st.session_state.question_input = question
    st.session_state.source_mode = source_mode_value
    st.session_state.retrieval_report = None
    st.session_state.retrieval_question = ""
    st.session_state.retrieval_mode = ""
    st.session_state.answer_text = None
    st.session_state.answer_question = ""


def _clear_search_results() -> None:
    """Clear the current question, retrieval results, and generated answer."""
    st.session_state.question_input = ""
    st.session_state.retrieval_report = None
    st.session_state.retrieval_question = ""
    st.session_state.retrieval_mode = ""
    st.session_state.answer_text = None
    st.session_state.answer_question = ""


def _build_evidence_markdown(
    question: str, source_label: str, report: dict[str, object]
) -> str:
    """Export user-visible evidence and provenance without claiming answer accuracy."""
    titles = {
        "hybrid": "Combined search (Hybrid RRF)",
        "dense": "Search by meaning (Dense)",
        "bm25": "Search by keywords (BM25)",
    }
    errors = report.get("_errors", {})
    lines = [
        "# SkillCraft — Retrieved Evidence Report",
        "",
        f"**Question:** {question.strip()}",
        f"**Selected material:** {source_label}",
        "**Purpose:** Retrieved source passages for verification; this report does not guarantee factual correctness.",
        "",
        "## Retrieved passages",
        "",
    ]
    any_results = False
    for method in ("hybrid", "dense", "bm25"):
        items = report.get(method, [])
        if not items:
            continue
        any_results = True
        lines.extend([f"### {titles[method]}", ""])
        for item in items:
            citation = str(item.get("citation", "Citation unavailable"))
            text = str(item.get("text", "")).strip()
            rank = item.get("rank", "?")
            lines.extend([
                f"**{citation}** · Rank {rank}",
                "",
                text,
                "",
            ])
    if not any_results:
        lines.extend(["No evidence passages were returned for this query.", ""])
    if errors:
        lines.extend(["## Retrieval notes", ""])
        for method, message in errors.items():
            lines.append(f"- **{str(method).upper()}:** {message}")
        lines.append("")
    lines.extend([
        "## Verification note",
        "",
        "Check each cited source page and its surrounding context before relying on a passage. "
        "A retrieved passage is evidence, not proof that an answer is complete or correct.",
        "",
    ])
    return "\n".join(lines)


with st.sidebar:
    st.markdown("## Start here")
    source_mode = st.radio(
        "What do you want to search?",
        ["Try the sample guide", "Search my own PDF"],
        key="source_mode",
        help="Choose the sample guide to try the app right away, or upload a text-based PDF you have permission to use.",
    )

    if source_mode == "Search my own PDF":
        uploads = st.file_uploader(
            "1. Choose PDF file(s)",
            type=["pdf"],
            accept_multiple_files=True,
            max_upload_size=MAX_UPLOAD_BYTES // (1024 * 1024),
            help=f"Text-based PDFs only. Combined limit: 20 MB and {MAX_PDF_PAGES:,} pages. Scanned PDFs need OCR first.",
        )
        current_upload_signature = upload_collection_signature(uploads)
        if (
            st.session_state.uploaded_index is not None
            and st.session_state.uploaded_signature != current_upload_signature
        ):
            st.session_state.uploaded_index = None
            st.session_state.uploaded_chunk_count = 0
            st.session_state.uploaded_signature = None
            st.session_state.retrieval_report = None
            st.session_state.answer_text = None
        if st.button("2. Prepare my PDF", type="primary", **_stretch_width(st.button)):
            if not uploads:
                st.warning("Choose at least one PDF first.")
            else:
                st.session_state.retrieval_report = None
                st.session_state.answer_text = None
                st.session_state.uploaded_index = None
                st.session_state.uploaded_chunk_count = 0
                st.session_state.uploaded_signature = None
                with st.spinner("Reading PDF pages and preparing search..."):
                    try:
                        idx, chunk_count = build_index_from_uploads(uploads)
                        st.session_state.uploaded_index = idx
                        st.session_state.uploaded_chunk_count = chunk_count
                        st.session_state.uploaded_signature = current_upload_signature
                        st.success(f"Your PDF is ready. {chunk_count} text passages indexed.")
                    except Exception as exc:
                        logger.exception("Uploaded PDF indexing failed")
                        st.error(f"Could not prepare these PDFs: {exc}")
        upload_matches_index = (
            st.session_state.uploaded_index is not None
            and st.session_state.uploaded_signature == current_upload_signature
            and bool(current_upload_signature)
        )
        if upload_matches_index:
            st.success(f"PDF ready · {st.session_state.uploaded_chunk_count} passages")
        else:
            st.info("After choosing your PDF, select Prepare my PDF.")
    else:
        st.success("Sample guide ready")
        st.caption("No upload, login, or AI API key is needed to try document search.")

    st.divider()
    st.markdown("### Try one of these")
    for label, value in [
        ("Binary search", "How does binary search reduce search time?"),
        ("Stacks and queues", "What is the difference between a stack and a queue?"),
        ("Hash tables", "How does a hash table handle collisions?"),
    ]:
        st.button(
            label,
            key=f"suggest_{label}",
            **_stretch_width(st.button),
            on_click=_use_suggestion,
            args=(value,),
        )

    st.button(
        "Clear search results",
        key="clear_search_results",
        on_click=_clear_search_results,
        **_stretch_width(st.button),
        help="Clear the current question, retrieved passages, and generated answer. Your prepared PDF remains available.",
    )

    st.divider()
    st.markdown("### What the app does")
    st.markdown(
        "1. Reads text from PDF pages\n"
        "2. Searches by keywords and meaning\n"
        "3. Combines search results\n"
        "4. Shows the matching passage and page citation"
    )
    st.caption("Your uploaded PDFs are processed in a temporary folder for extraction and are not added to the GitHub repository.")

if source_mode == "Try the sample guide":
    active_index = st.session_state.sample_index
    source_ready = True
    active_source_label = "Built-in Data Structures Guide"
else:
    active_index = st.session_state.uploaded_index if upload_matches_index else None
    source_ready = active_index is not None
    active_source_label = "Your uploaded PDF collection"

st.markdown('<div class="step">Step 1 of 2</div>', unsafe_allow_html=True)
st.markdown("## Ask a question")
st.write("Ask one clear question about the selected material. You can use one of the example questions in the left panel.")
with st.form("query_form"):
    question = st.text_input(
        "Your question",
        key="question_input",
        placeholder="For example: How does a hash table handle collisions?",
        help="Tip: ask about one concept at a time for more focused passages.",
    )
    top_k = st.select_slider(
        "How many passages should we find?",
        options=[1, 2, 3, 4, 5],
        value=3,
        help="Three passages is a good starting point. Increase this when you need more context.",
    )
    submitted = st.form_submit_button(
        "Find relevant passages",
        type="primary",
        **_stretch_width(st.form_submit_button),
        disabled=not source_ready,
    )

if not source_ready:
    st.warning("Your own PDF is not ready yet. Choose a PDF and select Prepare my PDF in the left panel.")
else:
    st.caption(f"Selected material: **{active_source_label}**")

if submitted:
    if not question.strip():
        st.warning("Type a question or choose an example first.")
    else:
        with st.spinner("Searching the document. The first meaning-based search can take a little longer while the model loads..."):
            try:
                st.session_state.retrieval_report = compare_retrievers(active_index, question, top_k)
                st.session_state.retrieval_question = question.strip()
                st.session_state.retrieval_mode = source_mode
                st.session_state.answer_text = None
                st.session_state.answer_question = ""

                current_report = st.session_state.retrieval_report
                best_method = next(
                    (name for name in ("hybrid", "dense", "bm25") if current_report.get(name)),
                    None,
                )
                best_items = current_report.get(best_method, []) if best_method else []
                citation = best_items[0].get("citation", "No evidence citation") if best_items else "No evidence returned"
                history_entry = {
                    "question": question.strip(),
                    "source_mode": source_mode,
                    "source_label": active_source_label,
                    "citation": str(citation),
                }
                previous = [
                    item for item in st.session_state.recent_searches
                    if not (
                        item.get("question") == history_entry["question"]
                        and item.get("source_mode") == history_entry["source_mode"]
                    )
                ]
                st.session_state.recent_searches = [history_entry, *previous][:5]
            except Exception as exc:
                logger.exception("Document search failed")
                st.session_state.retrieval_report = None
                st.error(f"Search did not complete: {exc}")

with st.sidebar:
    history = st.session_state.recent_searches
    if history:
        with st.expander("Recent searches (this session)", expanded=False):
            st.caption("Select a previous question to fill it in again. The search will run only after you press Find relevant passages.")
            for index, item in enumerate(history):
                st.caption(f"{item['source_label']} · {item['citation']}")
                visible_question = item["question"]
                if len(visible_question) > 48:
                    visible_question = visible_question[:45] + "..."
                st.button(
                    f"Use recent query: {visible_question}",
                    key=f"recent_query_{index}",
                    on_click=_use_history_entry,
                    args=(item["question"], item["source_mode"]),
                    **_stretch_width(st.button),
                )

report = st.session_state.retrieval_report
report_is_current = (
    report is not None
    and st.session_state.retrieval_mode == source_mode
    and st.session_state.retrieval_question == question.strip()
    and source_ready
)

if report_is_current:
    st.divider()
    st.markdown('<div class="step">Step 2 of 2</div>', unsafe_allow_html=True)
    st.markdown("## Best matching passage")
    st.write("Start with this passage. The citation tells you which source and page to check.")
    errors = report.get("_errors", {})
    for error_message in dict.fromkeys(errors.values()):
        st.warning(error_message)
    best_method = next((name for name in ("hybrid", "dense", "bm25") if report.get(name)), None)
    best_results = report.get(best_method, []) if best_method else []
    if best_results:
        best = best_results[0]
        st.markdown(
            '<div class="result-card">'
            f'<div class="citation">{html.escape(best["citation"])}</div>'
            f'<div class="evidence-text">{html.escape(best["text"])}</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if best_method == "hybrid":
            st.caption("Retrieved evidence from the selected source, not a guaranteed correct answer. Open the cited page to verify the context.")
        else:
            st.caption(f"Retrieved evidence using {best_method} search because a higher-priority method was unavailable. Open the cited page to verify the context.")
    else:
        st.info("No matching passage was found. Try a more specific question or upload a text-based PDF with the relevant topic.")

    export_markdown = _build_evidence_markdown(
        st.session_state.retrieval_question,
        active_source_label,
        report,
    )
    st.download_button(
        "Download evidence report (.md)",
        data=export_markdown,
        file_name="skillcraft-evidence-report.md",
        mime="text/markdown",
        **_stretch_width(st.download_button),
        help="Export the question, source/page citations, retrieved passages, and any retrieval warnings.",
    )
    st.caption("The export contains retrieved evidence and citations; it is not a certified answer.")

    comparison_csv = build_comparison_csv(
        st.session_state.retrieval_question,
        active_source_label,
        report,
    )
    st.download_button(
        "Download comparison CSV (.csv)",
        data=comparison_csv,
        file_name="skillcraft-retrieval-comparison.csv",
        mime="text/csv",
        **_stretch_width(st.download_button),
        help="Open in Excel to compare ranks, scores, citations, passages, and method failures.",
    )
    st.caption("CSV includes results or an explicit error/no-results row for each retrieval method.")

    has_generation = all(os.getenv(key) for key in ("RAG_API_KEY", "RAG_API_BASE_URL", "RAG_MODEL"))
    with st.expander("Would you like an AI-written response?"):
        if has_generation:
            st.write("When you choose Generate, the question and retrieved passages will be sent to the configured model provider. Do not use this for confidential documents unless you trust that provider.")
            if best_results and st.button("Generate a response with source context", type="primary"):
                try:
                    cited_results = [
                        SearchResult(
                            Chunk(item["chunk_id"], item["text"], item["source"], item["page"], rank),
                            float(item["score"]), rank + 1, item["method"],
                        )
                        for rank, item in enumerate(best_results)
                    ]
                    st.session_state.answer_text = generate_answer(
                        st.session_state.retrieval_question, cited_results
                    )
                    st.session_state.answer_question = st.session_state.retrieval_question
                except Exception as exc:
                    logger.exception("Answer generation failed")
                    st.error(f"Could not generate the response: {exc}")
        else:
            st.info(
                "AI answer generation is not configured in this demo. Search and page citations work without an API key. "
                "To enable generation, configure RAG_API_KEY, RAG_API_BASE_URL, and RAG_MODEL in a trusted environment."
            )
        if st.session_state.answer_text and st.session_state.answer_question == st.session_state.retrieval_question:
            st.markdown("### Generated response")
            st.text(st.session_state.answer_text)
            st.caption("This is model-generated text. Verify factual details against the source citations.")

    with st.expander("Compare how the three search methods performed"):
        st.write("These are three ways of finding passages for the same question. You do not need to understand the technical scores to use the app.")
        tabs = st.tabs(["Combined search (recommended)", "Search by meaning", "Search by keywords"])
        for tab, method_name in zip(tabs, ["hybrid", "dense", "bm25"]):
            with tab:
                results = report.get(method_name, [])
                if not results:
                    st.info(errors.get(method_name, "No passages were returned by this method."))
                for item in results:
                    with st.container(border=True):
                        st.markdown(f"**{html.escape(item['citation'])}**")
                        st.text(item["text"])
                        with st.expander("Technical details"):
                            st.caption(f"Rank: {item['rank']} · Method: {item['method']} · Internal score: {item['score']:.4f}")

with st.expander("What do the search methods mean?"):
    st.markdown(
        "**Search by keywords (BM25):** looks for words and phrases that match your question.\n\n"
        "**Search by meaning (Dense):** looks for passages with similar meaning, even when the wording is different.\n\n"
        "**Combined search (Hybrid):** combines the two result lists to balance exact terms and meaning. This is the recommended starting view."
    )

with st.expander("Recorded evaluation results (advanced)"):
    st.caption("These are previously recorded results for 34 manually labelled questions from one Data Structures PDF. They are not a live test of this question and do not measure the correctness of generated answers.")
    metrics = pd.DataFrame(
        [
            {"Search method": "BM25 keywords", "Recall@5": 0.824, "MRR@5": 0.674, "nDCG@5": 0.712},
            {"Search method": "Dense semantic", "Recall@5": 0.971, "MRR@5": 0.785, "nDCG@5": 0.832},
            {"Search method": "Hybrid (combined)", "Recall@5": 0.941, "MRR@5": 0.741, "nDCG@5": 0.792},
        ]
    )
    st.dataframe(metrics, hide_index=True, **_stretch_width(st.dataframe))
    st.caption("On this particular labelled set, Dense retrieval ranked highest. These figures should not be presented as overall answer accuracy.")

st.divider()
st.markdown(
    '<p class="subtle">SkillCraft Technology · AI Engineering Internship · Task 01 · '
    '<a href="https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline" target="_blank">View the source code</a></p>',
    unsafe_allow_html=True,
)
