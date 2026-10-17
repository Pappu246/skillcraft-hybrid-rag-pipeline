# SkillCraft Technology — AI Engineering Internship, Task 01
## Final Project Report: Hybrid Retrieval-Augmented Generation (RAG) Pipeline

**Report date:** 16 October 2026  
**Repository:** [Pappu246/skillcraft-hybrid-rag-pipeline](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline)

## 1. Abstract

This project implements a document-grounded retrieval pipeline for questions about PDFs. It extracts text page-by-page, builds BM25 keyword and Sentence-Transformers dense retrieval indexes, combines rankings using Reciprocal Rank Fusion (RRF), and retains source filename and physical PDF page citations. A Streamlit interface includes an original built-in Data Structures guide and a PDF upload path. Optional answer generation is supported through an OpenAI-compatible endpoint. Without the required generation settings, the interface clearly displays retrieved source context rather than claiming an LLM-generated answer.

## 2. Problem and objectives

Finding relevant passages in long study notes manually is time-consuming. Keyword retrieval can miss paraphrases, while semantic retrieval can be less exact for specific terms. The project compares both methods and a combined ranking while keeping the evidence and page provenance visible.

Objectives:
- Extract text from PDFs while preserving physical page numbers.
- Compare BM25 lexical retrieval, dense semantic retrieval, and hybrid RRF.
- Present the best matching evidence and traceable citations in an accessible web UI.
- Record document-specific retrieval evaluation metrics and automate regression checks.
- Keep optional LLM answer generation separate from evidence retrieval.

## 3. Architecture

1. **Input:** built-in sample guide or user-selected text-based PDF files.
2. **Ingestion:** extract page text and split it into searchable chunks.
3. **BM25:** lexical ranking based on matching terms.
4. **Dense retrieval:** sentence embeddings and semantic similarity.
5. **Hybrid RRF:** fuse ranks from keyword and dense search; optional CrossEncoder reranking is supported.
6. **Evidence interface:** show the best combined-search passage with a filename/page citation, with detailed method comparison tucked away for users who need it.
7. **Optional generation:** use `RAG_API_KEY`, `RAG_API_BASE_URL`, and `RAG_MODEL` only when configured.

## 4. User experience and privacy considerations

The interface follows a two-step flow: ask a question, then review the best matching passage. Sidebar examples help users start quickly. Advanced search-method details and historical metrics are placed in expandable sections. Uploaded PDFs are staged in a temporary directory for extraction and are not committed to the repository. Combined upload size is limited to 20 MB. Avoid uploading confidential documents to a public deployment; if generation is configured, the question and retrieved evidence are sent to the configured provider.

## 5. Evaluation results

The local evaluation used 34 manually labelled question-to-page mappings for one Data Structures handout named `Module1.pdf`.

| Method | Recall@5 | MRR@5 | nDCG@5 |
|---|---:|---:|---:|
| BM25 keyword retrieval | 0.824 | 0.674 | 0.712 |
| Dense semantic retrieval | 0.971 | 0.785 | 0.832 |
| Hybrid retrieval (RRF) | 0.941 | 0.741 | 0.792 |

**Interpretation:** dense retrieval scored highest on this particular set. Hybrid retrieval scored above BM25 on all three recorded metrics, but below Dense for this dataset. These metrics measure page retrieval, not generated-answer correctness. The dataset is small and document-specific; do not claim general or production-grade accuracy from these numbers.

## 6. Testing and fixes

The GitHub Actions workflow installs project/test/demo dependencies, compiles Python source for syntax errors, runs unit tests, and renders the Streamlit app through its smoke test.

- [UI simplification PR #7](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/7): merged after its CI run passed. The main interface now leads with the best matching passage and page citation.
- [Streamlit watcher fix PR #8](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/8): merged after CI passed. Streamlit file watching is disabled for this demo because the watcher was scanning lazy Transformers vision modules and repeatedly logging optional `torchvision` import errors. This was terminal noise from package inspection; it did not by itself prove that retrieval failed. The retrieval/indexing implementation was not altered by this configuration fix.
- [GitHub Actions run for PR #7](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/38939319142)
- [GitHub Actions run for PR #8](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/38941628804)

## 7. Local run

From the Windows PowerShell terminal in the cloned repository:

```powershell
git pull --ff-only origin main
.\START_DEMO.bat
```

Open `http://127.0.0.1:8501` on that same computer. Keep the terminal window open. The first dense query may take longer while the embedding model is downloaded. A localhost URL is not a public URL.

## 8. Deployment status

**The application is deployed to Vercel and the hosted service health checks pass.**

- Public URL: https://skillcraft-hybrid-rag-pipeline-git-main-pappu246s-projects.vercel.app/
- Vercel deployment: `dpl_BWZNaEMzMhjRvFEdKreVD1r6kf49` (state: `READY`)
- Source commit: `b71e7f4ac418cf8af365750fd95d479ed6a3e86f` on `main`
- Root page: HTTP 200 OK; returns the Streamlit application shell.
- Health endpoint: `/_stcore/health` returned HTTP 200 with body `ok`.
- Runtime logs: no error/fatal entries found in the checked 15-minute window.
- Container optimization: Vercel uses CPU-only PyTorch `2.9.1+cpu`; the first attempt using the default CUDA dependency set was canceled to avoid an unnecessarily large image.

The deployment and service health have been checked remotely. **A live interactive browser query has not been executed by this report's verifier**; before recording the demo, open the public URL and run both `How does binary search reduce search time?` and `How does a hash table handle collisions?`, confirming that the passages and source/page citations appear.

## 9. Limitations

- Evaluation is limited to 34 labelled questions on one document; labels should be reviewed and broadened.
- Recall@5, MRR@5, and nDCG@5 measure retrieval ranking, not answer truthfulness.
- Scanned/image-only PDFs need OCR; text extraction quality depends on PDF structure.
- First-time dense retrieval needs network access for model weights unless cached.
- Generated answers may be incorrect; source passages should be checked.
- The interface is a single-user internship demo, not a production multi-tenant service.

## 10. Conclusion

Task 01 includes hybrid retrieval methods, page-level evidence citations, a guided Streamlit interface, a small recorded evaluation, automated CI, and a verified public Vercel deployment. The UI simplification and terminal-noise fix have been merged into `main`. The public root and health endpoint return success; the remaining verification is to run interactive browser queries and capture screenshots or a short demo recording for the internship submission. Project claims should remain limited to the verified test results and document-specific retrieval measurements above.

## 11. Follow-up engineering audit and release status — 17 October 2026

Detailed root causes, fixes, and verification limits are documented in [`reports/ENGINEERING_AUDIT.md`](ENGINEERING_AUDIT.md).

- **PDF/retrieval hardening:** [PR #9](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/9) merged as `b4371a8`.
- **Evidence export and clear-search control:** [PR #10](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/10) merged as `933d709`.
- **Recent search history:** [PR #11](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/11) merged as `48e545f`. The last five searches are retained only for the current Streamlit session; a prior query is restored but not automatically re-executed.
- **Main-branch CI:** [run #39050135692](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/39050135692) passed on application commit `48e545f75227c77a3432f31553b3eef1bf840eb0`.
- **Production:** Vercel deployment `dpl_6C7P4mgoy5tcrosa1K7vG9E2iL7f` is `READY` with the canonical URL https://skillcraft-hybrid-rag-pipeline.vercel.app/.
- **HTTP/health checks:** canonical root returned HTTP 200; `/_stcore/health` returned HTTP 200 with body `ok`. No error/fatal runtime entries appeared in the checked 30-minute log window.
- **Interactive verification limit:** the private Vercel preview requires SSO and could not be exercised with real browser/WebSocket automation from this verifier. Automated Streamlit AppTest covers a cited BM25 fallback, evidence-download control, recent query selection, and clear-search behavior. Root/health success alone is not proof of end-to-end browser RAG behavior.
- **Evaluation:** no new Module 1 metrics are claimed because the matching `Module1.pdf` is absent. The stored 34-question metrics remain historical retrieval measures and are not generated-answer factuality scores.

Any remaining claims should stay limited to the tested behavior, historical dataset-specific metrics, and deployment checks described above.
