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

Latency is not quality. To compare retrieval relevance, create a JSON **array** of questions whose correct source pages have been checked against your own PDF. The `source` value must match the indexed PDF filename exactly, and `page` is 1-based.

Example schema only (the question and page below are placeholders; verify and replace them against your document before evaluating):
```json
[
  {
    "id": "q1",
    "question": "Replace with a question answerable from your PDF",
    "relevant_pages": [
      { "source": "Module1.pdf", "page": 1 }
    ]
  }
]
```

Save your labelled dataset as `data/evaluation.json`, then run:
```powershell
rag-pipeline evaluate --dataset data/evaluation.json --index-dir .rag_index --top-k 5 --output reports/evaluation.json
```

The evaluation compares BM25, dense, and hybrid retrieval using **page-level Recall@k, MRR@k, and nDCG@k**, with macro averages across questions and per-question details in the JSON report. Chunk results from the same source page are collapsed to one page rank. The evaluator requests extra candidate chunks to reduce duplicate-page crowding, but results still depend on the labelled questions and available candidates. Use a representative held-out set (for a small demo, start with 20–30 carefully labelled questions if the document supports them), inspect all labels, and do not present an illustrative or tiny sample as proof of general accuracy. These metrics evaluate retrieval, not generated-answer correctness.

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
