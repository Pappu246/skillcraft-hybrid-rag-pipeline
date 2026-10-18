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

- Exact head commit: `ba7e5a9bf8468b56510be0a7ea83d0ba54fb1a50`.
- GitHub Actions run [#39135709243](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/39135709243) passed; Python compile check passed; `pytest -q` reported **56 passed in 1.62s**. The test covers clearing a cached generated answer when the source filter changes.
- Vercel preview deployment `dpl_5Sw1HB6mnuWmiKVRQioe598ducFW` was registered for this exact head but remains `BUILDING`. The preview health fetch was redirected to `/sso-api`, so the deployment has not been functionally verified.
- A direct preview request for the initial feature head was previously rejected with HTTP 402 `payment_required` / `api-deployments-free-per-day`; do not bypass the deployment limit. The older READY feature deployment points to a different commit and does not validate this head.

### Release gate for PR #16

Before merge, create an exact-head preview when Vercel permits it, then test a multi-PDF query, source selection, the reset after a new query/history restore/clear, filtered Markdown and CSV exports, and preservation of method-error rows. After merge/deployment, verify the canonical URL and health endpoint again.

## Evaluation limits

The corresponding `Module1.pdf` was not available in the checked workspace. The 34-question figures previously recorded are historical retrieval measurements, not new post-change measurements or generated-answer accuracy scores.

## Release decision

Production is responding and is running main commit `63f3e35`. The source-filter change has passing automated tests but is **not shipped**: its exact-head preview remains `BUILDING`, and the protected health fetch redirected to `/sso-api`, so real UI verification is incomplete. Do not bypass Vercel deployment limits, change billing without authorization, or redirect production to an older preview.
