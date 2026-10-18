# Task 01 — Final Report and Release Status

Detailed verification limits and the deployment audit are documented in [`reports/ENGINEERING_AUDIT.md`](ENGINEERING_AUDIT.md).

## Implemented and merged

- **PDF ingestion and hybrid retrieval:** [PR #9](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/9), merged as `b4371a8`.
- **Evidence export and search reset:** [PR #10](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/10), merged as `933d709`.
- **Session-only recent search history:** [PR #11](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/11), merged as `48e545f`. History is limited to five entries in the current Streamlit session.
- **Retrieval comparison CSV export:** [PR #13](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/13), merged as `1c370c3`. The export includes selected document, search method, result status, rank/score, source, page, citation, passage, and explicit error or no-results rows.
- **Evidence-first UI copy:** [PR #14](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/14), merged as `2d813bf`. The app describes retrieval as cited evidence and makes AI-generated responses optional.

## Current production status — verified 2026-10-18

- **Deployment:** `dpl_2BjLPgR1w6SRQiHyPzXEmQq2ow84`, Vercel state `READY`, production target.
- **Deployed source:** main commit `63f3e35db465eb3a1eed95e93ef2449f29ff68b4`.
- **Homepage:** https://skillcraft-hybrid-rag-pipeline.vercel.app/ returned HTTP 200 and served the Streamlit HTML shell.
- **Health endpoint:** `/_stcore/health` returned HTTP 200, body `ok`.
- **Runtime errors:** no grouped runtime-error clusters were returned for the last 24 hours.

The current deployment source includes the merged CSV-export implementation. However, HTTP/health checks are not proof of a complete interactive session: a live browser/WebSocket test of PDF upload, retrieval, and clicking the CSV download has not been completed in this verification pass.

## Source-filter feature — still pending release

[PR #16](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/16) adds filtering of retrieved passages and report/CSV output by selected PDF source. It remains draft and unmerged.

- Exact head commit: `03d36a51b060bc3d2969ccbfac39abc5605ff2cd`.
- GitHub Actions run [#39055539663](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/39055539663) passed; Python compile check passed; `pytest -q` reported **56 passed**.
- Vercel's check for this head is failing due to a deployment/build rate-limit blocker. The direct preview request returned HTTP 402 `payment_required` / `api-deployments-free-per-day`.
- The available READY feature deployment is older than the exact head. Do not treat it as functional verification of the latest source-filter changes.

### Release gate for PR #16

Before merge, create an exact-head preview when Vercel permits it, then test a multi-PDF query, source selection, the reset after a new query/history restore/clear, filtered Markdown and CSV exports, and preservation of method-error rows. After merge/deployment, verify the canonical URL and health endpoint again.

## Evaluation limits

The corresponding `Module1.pdf` was not available in the checked workspace. The 34-question figures previously recorded are historical retrieval measurements, not new post-change measurements or generated-answer accuracy scores.

## Release decision

Production is responding and is running main commit `63f3e35`. The source-filter change has passing automated tests but is **not shipped**, because exact-head hosted UI verification is blocked by Vercel's daily deployment limit. Do not bypass that limit, change billing without authorization, or redirect production to an older preview.
