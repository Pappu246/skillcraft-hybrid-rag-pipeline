# Evaluation reports

Save generated comparison JSON here (for example, `reports/generated/question-01.json`). Generated local reports are ignored by Git.

For a meaningful benchmark, document:
- PDF dataset name, version, license, and number of pages
- A held-out set of questions and the gold source/page for each answer
- Recall@k, Mean Reciprocal Rank (MRR), and nDCG@k
- Indexing time, query latency, hardware, embedding model, and reranker model
- Failure cases, missing evidence, and citation correctness

Do not report an accuracy percentage unless it was calculated from a defined labelled dataset with reproducible steps.
