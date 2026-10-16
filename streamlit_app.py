"""Interactive web demo for SkillCraft Hybrid RAG Pipeline."""
from __future__ import annotations

import html
import os

import pandas as pd
import streamlit as st

from rag_pipeline.core import generate_answer
from rag_pipeline.demo import build_index_from_uploads, build_sample_index, compare_retrievers

st.set_page_config(
    page_title="SkillCraft Hybrid RAG Studio",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp { background: #0b1020; color: #edf2ff; }
      [data-testid="stSidebar"] { background: #111a30; }
      .hero { padding: 1.4rem 1.6rem; border: 1px solid #263554; border-radius: 18px;
              background: linear-gradient(125deg, #162747 0%, #10192c 70%, #15223c 100%);
              margin-bottom: 1rem; }
      .hero-kicker { color: #8db8ff; font-size: .78rem; font-weight: 700;
                     letter-spacing: .13em; text-transform: uppercase; }
      .hero h1 { color: #f5f8ff; margin: .35rem 0 .45rem 0; font-size: 2.15rem; }
      .hero p { color: #b8c6df; max-width: 830px; margin-bottom: .35rem; }
      .result-card { border: 1px solid #2a3855; border-radius: 12px; padding: 1rem;
                     margin: .6rem 0; background: #111a2c; }
      .citation { color: #92bdff; font-weight: 700; }
      div[data-testid="stMetric"] { background: #111a2c; border: 1px solid #2a3855;
                    padding: .8rem; border-radius: 12px; }
      .small-note { color: #a6b4cc; font-size: .86rem; }
      .stButton > button[kind="primary"] { border-radius: 10px; font-weight: 700; }
    </style>
    <div class="hero">
      <div class="hero-kicker">SkillCraft Technology · AI Engineering · Task 01</div>
      <h1>Hybrid RAG Studio</h1>
      <p>Ask a question, compare keyword and semantic retrieval, and inspect the exact source-page evidence behind every result.</p>
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
if "retrieval_report" not in st.session_state:
    st.session_state.retrieval_report = None
if "retrieval_question" not in st.session_state:
    st.session_state.retrieval_question = ""
if "retrieval_mode" not in st.session_state:
    st.session_state.retrieval_mode = ""

with st.sidebar:
    st.markdown("### Knowledge source")
    source_mode = st.radio(
        "Choose your corpus",
        ["Built-in sample guide", "Upload your PDFs"],
        help="The built-in guide is original demo content. Uploaded PDFs are used for this session only.",
    )
    if source_mode == "Upload your PDFs":
        uploads = st.file_uploader(
            "Select PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            help="Select text-based PDFs, combined size up to 20 MB. Scanned PDFs need OCR first.",
        )
        if st.button("Build index from PDFs", type="primary", use_container_width=True):
            if not uploads:
                st.warning("Select at least one PDF first.")
            else:
                with st.spinner("Extracting PDF pages and building the retrieval index..."):
                    try:
                        idx, chunk_count = build_index_from_uploads(uploads)
                        st.session_state.uploaded_index = idx
                        st.session_state.uploaded_chunk_count = chunk_count
                        st.session_state.retrieval_report = None
                        st.success(f"Indexed {chunk_count} text chunks.")
                    except Exception as exc:
                        st.error(f"Could not index the selected PDFs: {exc}")
        if st.session_state.uploaded_index is not None:
            st.success(f"Uploaded corpus ready · {st.session_state.uploaded_chunk_count} chunks")
        else:
            st.info("Build the index to query your own PDFs.")
    else:
        st.caption("Ready to try immediately—no upload required.")
        st.markdown("**Suggested questions**")
        st.code("How does binary search reduce search time?")
        st.code("What is the difference between a stack and a queue?")
        st.code("How does a hash table handle collisions?")

    st.divider()
    st.markdown("### How it works")
    st.markdown(
        "1. Extract PDF text page-by-page\n"
        "2. Build BM25 and dense retrieval indexes\n"
        "3. Fuse ranks with Reciprocal Rank Fusion\n"
        "4. Return source and physical PDF page citations"
    )
    st.caption("Dense retrieval downloads the embedding model on first use. Retrieval comparison needs no LLM API key. If LLM settings are configured, your query and retrieved evidence are sent to that provider.")

if source_mode == "Built-in sample guide":
    active_index = st.session_state.sample_index
    source_ready = True
    active_source_label = "Built-in Data Structures Guide"
else:
    active_index = st.session_state.uploaded_index
    source_ready = active_index is not None
    active_source_label = "Uploaded PDF corpus"

left, right = st.columns([3, 1])
with left:
    st.markdown("#### Ask your document")
    with st.form("query_form"):
        question = st.text_input(
            "Question",
            value="How does binary search reduce search time?",
            placeholder="Ask a question that your PDF answers...",
        )
        top_k = st.slider("Results per method", min_value=1, max_value=5, value=3)
        submitted = st.form_submit_button(
            "Compare BM25 · Dense · Hybrid",
            type="primary",
            use_container_width=True,
            disabled=not source_ready,
        )
with right:
    st.markdown("#### Pipeline status")
    st.metric("Knowledge source", "Ready" if source_ready else "Needs index")
    st.metric("Retrieval methods", "3")
    st.metric("Citations", "Page-level")

if submitted:
    if not question.strip():
        st.warning("Enter a question first.")
    elif not source_ready:
        st.warning("Choose a sample guide or build an index from your PDFs.")
    else:
        with st.spinner("Running keyword, semantic, and hybrid retrieval..."):
            try:
                st.session_state.retrieval_report = compare_retrievers(active_index, question, top_k)
                st.session_state.retrieval_question = question.strip()
                st.session_state.retrieval_mode = source_mode
            except Exception as exc:
                st.session_state.retrieval_report = None
                st.error(f"Retrieval failed: {exc}")

report = st.session_state.retrieval_report
report_is_current = (
    report is not None
    and st.session_state.retrieval_mode == source_mode
    and st.session_state.retrieval_question == question.strip()
    and source_ready
)

if report_is_current:
    st.divider()
    st.markdown("### Retrieved evidence")
    st.caption(f"Source: {active_source_label} · Question: “{st.session_state.retrieval_question}”")
    tabs = st.tabs(["Hybrid · RRF", "Dense · Semantic", "BM25 · Keywords"])
    for tab, method_name in zip(tabs, ["hybrid", "dense", "bm25"]):
        with tab:
            results = report.get(method_name, [])
            if not results:
                st.info("No results were returned for this query.")
            for item in results:
                st.markdown(
                    '<div class="result-card">'
                    f'<div class="citation">{html.escape(item["citation"])}</div>'
                    f'<div class="small-note">Rank #{item["rank"]} · {item["method"]} · raw score {item["score"]:.4f}</div>'
                    f'<p>{html.escape(item["text"])}</p>'
                    '</div>',
                    unsafe_allow_html=True,
                )

    has_generation = all(os.getenv(key) for key in ("RAG_API_KEY", "RAG_API_BASE_URL", "RAG_MODEL"))
    button_label = "Generate cited answer with configured LLM" if has_generation else "Show grounded evidence context"
    if st.button(button_label, use_container_width=True):
        try:
            hybrid_chunks = active_index.search_hybrid(st.session_state.retrieval_question, top_k=top_k)
            answer = generate_answer(st.session_state.retrieval_question, hybrid_chunks)
            st.markdown("### Answer / evidence context")
            if has_generation:
                st.markdown(answer)
            else:
                st.info("No LLM endpoint is configured. This is retrieved source context, not an AI-generated answer.")
                st.markdown(answer)
        except Exception as exc:
            st.error(f"Answer generation failed: {exc}")

with st.expander("Recorded Module 1 evaluation (34 labelled questions)"):
    st.caption("These are recorded local evaluation results for Module1.pdf—not a live evaluation of this browser session.")
    metrics = pd.DataFrame(
        [
            {"Method": "BM25", "Recall@5": 0.824, "MRR@5": 0.674, "nDCG@5": 0.712},
            {"Method": "Dense", "Recall@5": 0.971, "MRR@5": 0.785, "nDCG@5": 0.832},
            {"Method": "Hybrid (RRF)", "Recall@5": 0.941, "MRR@5": 0.741, "nDCG@5": 0.792},
        ]
    )
    st.dataframe(metrics, hide_index=True, use_container_width=True)
    st.caption("Dense performed best on this particular set. These metrics measure page retrieval, not answer-generation accuracy.")

st.divider()
st.markdown(
    '<div class="small-note">Built for the SkillCraft Technology AI Engineering Internship · Task 01 · '
    '<a href="https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline" target="_blank">Source code on GitHub</a></div>',
    unsafe_allow_html=True,
)
