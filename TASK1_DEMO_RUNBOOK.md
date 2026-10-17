# Task 01 Demo Runbook

Use this runbook to demonstrate the actual Hybrid RAG retrieval pipeline. This is a demo guide, not the internship report.

## What the audience should see

1. The app starts with an original built-in Data Structures guide; no document upload or model API key is required.
2. Choose one of the plain-language example questions or type your own question.
3. Compare the same question across BM25 keyword retrieval, dense semantic retrieval, and Hybrid RRF.
4. Show the top matching passage first, explain its source/page citation, then expand the comparison section to show keyword, meaning, and combined search.
5. Switch to **Upload your PDFs**, upload a small non-confidential, text-based PDF, build its index, ask a question grounded in that PDF, and show the page citations.
6. Show the recorded 34-question Module1.pdf retrieval table, clearly describing it as document-specific page-retrieval metrics, not answer-generation accuracy.

## Suggested 60-second demo

- **0–8 s:** Show the title and explain: "This project compares keyword, semantic, and hybrid retrieval for document-grounded search."
- **8–20 s:** Keep the sample guide selected, click **Binary search** in the left panel, and select **Find relevant passages**.
- **20–38 s:** Read the **Best matching passage** and point out the source/page citation. Expand **Compare how the three search methods performed**.
- **38–50 s:** Click **Hash tables**, run the search, and show the new passage and citation.
- **50–60 s:** Open the recorded evaluation table and state the exact scope: 34 manually labelled questions from one Data Structures handout; Recall@5/MRR@5/nDCG@5 evaluate page retrieval, not answer correctness.

If doing a longer demo, also show the PDF upload/index/query flow. Use a public, non-confidential PDF only.

## Local launch (Windows PowerShell)

From the repository root, with the project virtual environment activated:

```powershell
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

The first dense query downloads the Sentence-Transformers model and may take longer. The demo disables Streamlit's file watcher to prevent noisy Transformers-module tracebacks; restart the app after pulling updates. Retrieval comparison can run without `RAG_API_KEY`, `RAG_API_BASE_URL`, or `RAG_MODEL`. Without those settings, the UI labels retrieved passages as evidence and does not claim model generation. If semantic search fails, keyword results can still appear and are labelled as a BM25 fallback. When credentials are configured, generated responses are requested only after the user explicitly selects Generate; the question and retrieved passages are sent to the configured provider, and citations are validated before display.

## Upload and privacy checks

- Upload text-based PDFs only; combined uploads are limited to 20 MB and 2,000 physical pages. Files need a `.pdf` extension plus a PDF header.
- Encrypted, malformed, empty, or image-only files show actionable recovery guidance; scanned PDFs require OCR.
- The app sanitizes upload names and extracts content in a temporary directory that is cleaned on success or failure.
- Uploaded files are not committed to the repository.
- Avoid private, personal, or restricted files in any public demo.
- If LLM credentials are configured, the question and retrieved evidence are sent to the configured provider. Do not configure an endpoint you do not trust.

## Deployment readiness

- Streamlit Community Cloud: repository `Pappu246/skillcraft-hybrid-rag-pipeline`, branch `main`, entrypoint `streamlit_app.py`; dependencies are declared in `requirements.txt`. The hosting provider requires an authorized account action to create the public app URL.
- Docker: the root `Dockerfile` starts Streamlit on `0.0.0.0:$PORT`, includes a health check, and runs as an unprivileged user. Build with `docker build -t skillcraft-hybrid-rag .` and run with `docker run --rm -p 8501:8501 skillcraft-hybrid-rag`. The first model query still needs internet access to download model weights.

## Recorded evaluation numbers

| Method | Recall@5 | MRR@5 | nDCG@5 |
|---|---:|---:|---:|
| BM25 | 0.824 | 0.674 | 0.712 |
| Dense | 0.971 | 0.785 | 0.832 |
| Hybrid (RRF) | 0.941 | 0.741 | 0.792 |

These numbers are the user-observed evaluation run on the 34-question set. Dense ranked highest for this dataset. Do not describe them as overall answer accuracy, general benchmark performance, or a verified result for other documents.

## Final capture checklist

- [ ] Show app title and the selected knowledge source.
- [ ] Run at least two queries.
- [ ] Keep a citation visible while showing each retrieval strategy.
- [ ] Show the dataset size and metric names without overstating accuracy.
- [ ] Avoid exposing API keys, local file paths, private PDFs, terminal history, or personal notifications.
- [ ] If publishing a link, first open it in a private/incognito window and verify that the app loads for a viewer without repository write access.
