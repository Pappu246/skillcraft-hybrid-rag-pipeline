# SkillCraft Hybrid RAG Pipeline

**SkillCraft Technology — AI Engineering Internship, Task 01**

A practical Retrieval-Augmented Generation (RAG) baseline that compares BM25 keyword retrieval, dense vector retrieval, and hybrid retrieval, optionally reranks candidates, and returns source/page citations with generated answers.

> This is an internship/demo baseline. Evaluation figures below are specific to the included labelled set and are not claims of production-grade accuracy.

## Features
- PDF ingestion with page-level provenance
- Configurable chunking with source metadata
- BM25 lexical retrieval
- Sentence-Transformers dense retrieval (local embeddings)
- Reciprocal Rank Fusion (RRF) hybrid retrieval
- Optional CrossEncoder reranking
- Optional OpenAI-compatible answer generation endpoint
- Source citations in retrieved context and answer output
- Retrieval comparison report and automated tests
- Page-level duplicate suppression, deterministic ranking, and explicit empty-query/no-match behavior
- Clear method-level fallbacks when semantic model loading fails, without mislabelling keyword results as hybrid
- Optional answer-generation safeguards: untrusted evidence boundary, source-citation validation, and actionable provider errors
- Session-only recent search history (last five questions), with safe query restoration
- Downloadable Markdown evidence report and one-click clear-results control

## Requirements
- Python 3.10+
- Internet access for first-time model downloads (unless models are cached)
- An API key only if you enable answer generation

## Quick start (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pip install -e .
```

Put one or more PDF files in `data/documents/`, then index them:
```powershell
rag-pipeline ingest --input data/documents --index-dir .rag_index
```

Compare retrieval strategies (three timed runs by default; use `--repeats` to change that):
```powershell
rag-pipeline compare --index-dir .rag_index --question "What are the main findings?" --repeats 3 --output reports/comparison.json
```

Ask a question (generation is optional; without API settings the tool returns grounded retrieved context):
```powershell
rag-pipeline ask --index-dir .rag_index --question "Summarize the main findings."
```

Optional OpenAI-compatible generation settings:
- `RAG_API_BASE_URL` (for example, your provider's OpenAI-compatible base URL)
- `RAG_API_KEY`
- `RAG_MODEL`

Keep secrets in a local `.env` file or environment variables. Never commit credentials. The application reads environment variables; it does not automatically load `.env` unless you install and configure a dotenv loader.

## Interactive web demo

**Windows quick launch:** double-click `START_DEMO.bat` from the repository folder. It creates `.venv` if needed, installs missing dependencies, and starts the local demo.

Or launch manually from PowerShell:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

The app opens with an **original built-in Data Structures guide** so the demo works without uploading a document. The interface guides visitors through two steps: ask a question, then inspect the best matching passage and its page citation. Advanced retrieval comparisons and recorded metrics are tucked into expandable sections. Switch to **Upload your PDFs** to index text-based PDF files for that session (combined maximum 20 MB and 2,000 physical pages). Uploads must have a `.pdf` filename and a PDF header; encrypted, malformed, empty, and image-only PDFs receive an actionable error. Uploaded PDF bytes are written to a temporary directory only while text is extracted; the extracted chunks and index remain in the active Streamlit session. Changing the selected upload invalidates results until that selection is indexed. Do not upload confidential documents to a public hosted demo. Scanned PDFs need OCR before ingestion.

The interface leads with the best available passage, explains citations in plain language, and places BM25, dense, and hybrid RRF comparison details in an expandable section. Source filenames and 1-based physical PDF page citations remain visible. If semantic-model loading fails, keyword retrieval can still be shown and is labelled as a BM25 fallback rather than hybrid search. The “Generate cited answer” action calls an OpenAI-compatible model only when `RAG_API_KEY`, `RAG_API_BASE_URL`, and `RAG_MODEL` are set and you explicitly choose Generate. The question and retrieved passages are then sent to that configured provider. Without those settings, search remains local and the app labels its output as retrieved evidence, not a generated answer. Generated citations are checked against the retrieved pages; if the model invents a page citation, that response is withheld.

For a hosted demo, use a Python hosting service that supports Streamlit and the dependencies in `requirements.txt`. The first dense query downloads the Sentence-Transformers embedding model, so initial load can take longer than later queries.

## Architecture
1. Extract PDF text page-by-page and retain filename/page provenance.
2. Split text into overlapping chunks.
3. Retrieve candidates using BM25 and dense cosine similarity.
4. Fuse ranked lists using Reciprocal Rank Fusion.
5. Optionally rerank fused candidates with a cross-encoder.
6. Build a context restricted to retrieved evidence and attach citations.
7. If an API endpoint is configured, request an answer that must cite the supplied sources.

## Evaluation
Run:
```powershell
pytest -q
rag-pipeline compare --index-dir .rag_index --question "Your evaluation question"
```
The comparison command reports ranked source chunks and warmed retrieval latency. It performs one warm-up per method, then three timed runs by default and reports the median plus each individual timing. This reduces first-use initialization bias, but it is **not** a cold-start benchmark and does not measure retrieval accuracy.

### Labelled retrieval-quality evaluation

The repository includes a **34-question, page-labelled evaluation set** for the `Module1.pdf` Data Structures handout at `evaluation_datasets/module1.json`. It covers data structures and ADTs, algorithm properties and analysis, asymptotic notation, arrays and address calculations, and linear/binary search.

**Important label convention:** the dataset uses the physical PDF page number counted from 1, matching the page number emitted by `pypdf.PdfReader` during ingestion. It does not use the printed footer page number (the cover and contents pages make these differ). The source filename in the label is exactly `Module1.pdf`, so your index must have been built from that PDF under that filename.

Evaluate your local index:
```powershell
pytest -q
rag-pipeline evaluate --dataset evaluation_datasets/module1.json --index-dir .rag_index --top-k 5 --output reports/module1_evaluation.json
```

The report compares BM25, dense, and hybrid retrieval using page-level Recall@k, MRR@k, and nDCG@k, with macro averages across questions and per-question results in JSON. Multiple chunks from the same page collapse to a single page rank. The JSON also records the embedding/reranker names, chunk size and overlap, page limit, RRF constant, index chunk count, source filenames, question count, and SHA-256 fingerprints of the indexed chunk content and normalized evaluation labels to help identify both corpus and dataset. The label set is a useful document-specific evaluation baseline, not an independent benchmark or proof of general performance. Before using it for a formal claim, review the page labels and extend it with representative questions and all materially relevant pages from your own document/version. These metrics measure page retrieval, not answer-generation correctness.

## Troubleshooting

- **First semantic search is slow or unavailable:** the Sentence-Transformers model is loaded lazily and its weights must be available locally or downloadable from Hugging Face. Retry with network access or a populated model cache. BM25 keyword results remain available when the optional semantic method fails.
- **“No selectable text” or OCR guidance:** the PDF is scanned/image-only or its text layer is empty. Run OCR with a trusted local tool, save a searchable PDF, then upload it again.
- **Encrypted, malformed, or unsupported PDF:** remove password protection, re-export the PDF from a trusted source, and check the file opens in a standard viewer. A `.pdf` extension alone is not sufficient.
- **Generated answer unavailable:** check `RAG_API_BASE_URL`, `RAG_API_KEY`, and `RAG_MODEL`; provider credentials are optional for retrieval. HTTP 401/403 indicates credentials, 429 indicates rate limiting, and timeout/network errors can be retried.

## Current limitations
- PDF extraction quality depends on whether the PDF contains selectable text; scanned PDFs need OCR.
- Dense retrieval downloads a sentence-transformer model on first use.
- The included local index is intended for a single-user internship demo, not concurrent production traffic.
- Model answers can still be wrong; inspect the cited evidence.
- The included labelled dataset is a small, document-specific evaluation baseline—not independent ground truth. Retrieval scores are meaningful only when labels are verified and questions are representative.

## Final project report

The Task 01 report covering architecture, user interface, measured retrieval evaluation, test verification, limitations, and deployment status is available at [`reports/TASK01_FINAL_REPORT.md`](reports/TASK01_FINAL_REPORT.md). The follow-up implementation audit, regression findings, current test evidence, and deployment verification limits are recorded in [`reports/ENGINEERING_AUDIT.md`](reports/ENGINEERING_AUDIT.md).

## Project deliverables
- Source code and tests
- BM25 vs Dense vs Hybrid retrieval comparison
- Citation-bearing grounded context and optional generated answer
- Interactive Streamlit demo for uploaded PDFs and an original built-in sample guide

## License
No license has been selected yet. All rights remain with the repository owner unless a license is added.
