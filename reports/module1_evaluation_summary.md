# Module 1 Retrieval Evaluation Results

**Document:** `Module1.pdf`  
**Evaluation set:** 34 manually labelled questions  
**Cutoff:** top 5 unique source pages (`k=5`)  
**Metrics:** macro-averaged page Recall@5, MRR@5, and nDCG@5  
**Evaluation date:** 2026-10-16

**Status:** Historical recorded baseline; not rerun after 2026-10-17 retrieval changes.

## Results

| Retrieval method | Recall@5 | MRR@5 | nDCG@5 |
|---|---:|---:|---:|
| BM25 | 0.824 | 0.674 | 0.712 |
| Dense | **0.971** | **0.785** | **0.832** |
| Hybrid (RRF) | 0.941 | 0.741 | 0.792 |

## Interpretation

- **Dense retrieval performed best** on this particular 34-question dataset across all three reported metrics.
- Hybrid retrieval outperformed BM25 on all three metrics, but did not outperform dense retrieval on this dataset.
- Recall@5 measures whether labelled relevant pages appeared among the top five unique pages. MRR@5 rewards ranking the first relevant page higher; nDCG@5 accounts for the ranking of relevant pages.
- These are **retrieval/page-ranking results**, not answer-generation accuracy, factuality, or proof that one method is universally best.

## Reproduce

From the repository root, with the project installed and `.rag_index` built from the matching `Module1.pdf` filename:

```powershell
pytest -q
rag-pipeline evaluate --dataset evaluation_datasets/module1.json --index-dir .rag_index --top-k 5 --output reports/module1_evaluation.json
```

The generated JSON contains per-question results and metrics. It is a local run artifact; this Markdown file records the aggregate values reported by the run.

## Limitations

- The dataset has only 34 manually labelled questions and is specific to one handout/version.
- The labels should be reviewed for completeness and relevance; they are not an independent or externally validated benchmark.
- Results can change with the PDF version, chunking/index settings, embedding model, or retrieval configuration. Subsequent implementation now suppresses zero-score BM25 matches and duplicate source pages, so these historic figures should not be cited as post-change results.
- The matching `Module1.pdf` is not present in the current repository checkout; the 34 labels and historic result table were preserved, but a fresh comparable run is blocked until the matching PDF is supplied locally.
- The first Hugging Face model download may require network access. An unauthenticated Hugging Face warning did not prevent the recorded evaluation from completing.
- No claim is made here about answer correctness, production readiness, or general performance on other documents.
