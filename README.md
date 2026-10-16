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

The report compares BM25, dense, and hybrid retrieval using page-level Recall@k, MRR@k, and nDCG@k, with macro averages across questions and per-question results in JSON. Multiple chunks from the same page collapse to a single page rank. The label set is a useful document-specific evaluation baseline, not an independent benchmark or proof of general performance. Before using it for a formal claim, review the page labels and extend it with representative questions and all materially relevant pages from your own document/version. These metrics measure page retrieval, not answer-generation correctness.

## Current limitations
- PDF extraction quality depends on whether the PDF contains selectable text; scanned PDFs need OCR.
- Dense retrieval downloads a sentence-transformer model on first use.
- The included local index is intended for a single-user internship demo, not concurrent production traffic.
- Model answers can still be wrong; inspect the cited evidence.
- Retrieval-quality scores are only meaningful when the question-to-page labels are manually verified and representative; the repo does not ship a ground-truth dataset.

## Project deliverables
- Source code and tests
- BM25 vs Dense vs Hybrid retrieval comparison
- Citation-bearing grounded context and optional generated answer
- Optional UI can be added after the retrieval pipeline is validated

## License
No license has been selected yet. All rights remain with the repository owner unless a license is added.
