# SkillCraft Hybrid RAG Pipeline

**SkillCraft Technology — AI Engineering Internship, Task 01**

A practical Retrieval-Augmented Generation (RAG) baseline that compares BM25 keyword retrieval, dense vector retrieval, and hybrid retrieval, optionally reranks candidates, and returns source/page citations with generated answers.

> This is an initial implementation scaffold. Run the tests and evaluation on your own documents before describing performance as measured or production-ready.

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

Compare retrieval strategies:
```powershell
rag-pipeline compare --index-dir .rag_index --question "What are the main findings?"
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
The comparison command reports retrieval latency and ranked source chunks. This is a diagnostic comparison, **not** an accuracy score. For defensible evaluation, create a labelled question-to-source dataset and measure Recall@k, MRR and nDCG on held-out questions.

## Current limitations
- PDF extraction quality depends on whether the PDF contains selectable text; scanned PDFs need OCR.
- Dense retrieval downloads a sentence-transformer model on first use.
- The included local index is intended for a single-user internship demo, not concurrent production traffic.
- Model answers can still be wrong; inspect the cited evidence.
- No benchmark claims are made until you run a reproducible evaluation on a documented dataset.

## Project deliverables
- Source code and tests
- BM25 vs Dense vs Hybrid retrieval comparison
- Citation-bearing grounded context and optional generated answer
- Optional UI can be added after the retrieval pipeline is validated

## License
No license has been selected yet. All rights remain with the repository owner unless a license is added.
