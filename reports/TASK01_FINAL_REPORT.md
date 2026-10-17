## 11. Follow-up engineering audit and release status — 17 October 2026

Detailed findings and verification limits are documented in [`reports/ENGINEERING_AUDIT.md`](ENGINEERING_AUDIT.md).

- **PDF/retrieval hardening:** [PR #9](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/9) merged as `b4371a8`.
- **Evidence export and clear-search control:** [PR #10](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/10) merged as `933d709`.
- **Recent search history:** [PR #11](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/11) merged as `48e545f`. History is limited to five entries in the current Streamlit session.
- **Comparison CSV export:** [PR #13](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/13) merged as `1c370c3`. CSV contains query, selected material, search method, status, rank, score, source, page, citation, passage and explicit error/no-results rows. Proper CSV quoting covers passages with commas, quotes, and embedded newlines.
- **Evidence-first UI wording:** [PR #14](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/14) merged as `2d813bf`. The hero now says “Find cited evidence in your documents” and explains that AI-written answers are optional; default output is retrieved evidence.
- **CI:** the PR-specific run [#39051120832](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/39051120832), post-merge main run [#39051290703](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/39051290703), and latest main run [#39051804509](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/39051804509) all passed.
- **Current production status:** the latest production deployment listed by Vercel is `dpl_EBUQC7mJdeRqp4W34eKfjQyWGQKN` at commit `f255792`. Canonical root returned HTTP 200 and `/_stcore/health` returned `ok`. The CSV feature from main commit `1c370c3` is merged and CI-passed but **not live yet**.
- **Deployment blocker:** Vercel rejected a new deployment request with HTTP 402 `payment_required`, reason `api-deployments-free-per-day` (daily deployment limit, retry in 86400 seconds). The project must wait for quota reset or an authorized team/plan resolution; no aliases were redirected to an older preview to pretend the new commit was live.
- **Interactive verification:** the preview requires Vercel SSO, so this verifier did not run a real browser/WebSocket RAG query against the private preview. Streamlit AppTest covers the query/fallback UI, Markdown export, recent-query selection, clear-results, and CSV export helper. HTTP health success is not proof that every interactive path works.
- **Evaluation:** no fresh Module 1 metrics are claimed because the matching `Module1.pdf` is absent. The 34-question scores remain historical document-specific retrieval metrics, not generated-answer correctness.

The next allowed release should deploy the latest CI-verified main commit after Vercel quota allows it, then verify the live CSV download and the two sample queries in a browser.
