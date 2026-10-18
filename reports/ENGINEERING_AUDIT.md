## Deployment / current verification (updated 2026-10-18)

This audit snapshot reflects main commit `63f3e35db465eb3a1eed95e93ef2449f29ff68b4` and the production deployment built from that commit. The latest production deployment is now available; the prior statement that the CSV export was not live is superseded by this snapshot.

## Merged application changes

- [PR #9 — Harden PDF ingestion and hybrid retrieval](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/9) merged as `b4371a8e3fe4bf227c6ba17014c3bbf8753e26dc`.
- [PR #10 — Add evidence export and one-click search reset](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/10) merged as `933d709586015e18fd2f0eef9975ed165caae2e5`.
- [PR #11 — Add session-only recent search history](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/11) merged as `48e545f75227c77a3432f31553b3eef1bf840eb0`.
- [PR #13 — Add downloadable retrieval comparison CSV](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/13) merged as `1c370c3e610520b042597c23464c216e762d4fa6`. The CSV includes query, selected material, method, status, rank, score, source, page, citation, passage, and explicit error/no-results rows.
- [PR #14 — Clarify evidence-first UI behavior](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/14) merged as `2d813bf314832116600a78eaa35912308ac6b1c6`. The hero states “Find cited evidence in your documents” and explains that AI-written responses are optional.
- Main's latest commit `63f3e35db465eb3a1eed95e93ef2449f29ff68b4` changes release documentation; it does not change application code.

## Production state verified on 2026-10-18

- Vercel deployment: `dpl_2BjLPgR1w6SRQiHyPzXEmQq2ow84`.
- State: `READY`, production target; deployed Git SHA `63f3e35db465eb3a1eed95e93ef2449f29ff68b4`.
- Canonical URL: https://skillcraft-hybrid-rag-pipeline.vercel.app/
- The canonical homepage returned HTTP 200 and served the Streamlit HTML shell.
- `/_stcore/health` returned HTTP 200 with body `ok`.
- Vercel's deployment status for the current main commit is successful.
- A grouped Vercel runtime-error query over the last 24 hours returned no runtime-error clusters.

These checks establish that the production deployment is ready and its health endpoint responds. They do **not** constitute end-to-end browser/WebSocket verification of an uploaded PDF, retrieval query, or download interaction. The deployed source includes the merged CSV-export implementation, but a live click-through of the CSV button has not been independently verified in a browser during this check.

## Source-filter feature PR #16 — not released

[PR #16 — Filter retrieved evidence by PDF source](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/16) remains draft and unmerged.

- Exact PR head: `ba7e5a9bf8468b56510be0a7ea83d0ba54fb1a50`.
- GitHub Actions run [#39135709243](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/39135709243) completed successfully. Python compile check passed and `pytest -q` reported **56 passed in 1.62s**. This head includes a regression test that verifies a cached generated answer is cleared when the source filter changes.
- Vercel registered exact-head preview deployment `dpl_5Sw1HB6mnuWmiKVRQioe598ducFW` for commit `ba7e5a9`, but it remains `BUILDING`. An HTTP check of that protected preview's health route was redirected to `/sso-api` and could not verify app health; no hosted interaction test has been completed.
- The earlier direct preview request for the initial feature commit was rejected with HTTP 402 `payment_required` / `api-deployments-free-per-day`. The current Git-linked preview is now registered, but is not yet READY or functionally verified. The older READY feature-branch deployment is from a different commit and is not evidence for the exact current head.
- Keep this PR draft/unmerged until the exact-head preview is accessible and READY, then test the source selector, stale-answer invalidation, query/history reset behavior, filtered Markdown/CSV exports, and method-error handling in the real Streamlit UI.

Do not circumvent Vercel's deployment quota, change billing, redirect the production alias to an older preview, or claim the source-filter feature is released.

## Evaluation limits

The matching `Module1.pdf` is not present in the checked workspace. The previously recorded 34-question metrics remain historical retrieval measurements tied to the earlier test material; they are not new post-change results or generated-answer factuality scores.

## Rollback

The latest production deployment at the time of this audit is `dpl_2BjLPgR1w6SRQiHyPzXEmQq2ow84` from main commit `63f3e35`. If a later release regresses, use an authorized Vercel rollback to a known-good deployment and verify the canonical homepage and health endpoint afterward. Preserve Git history; do not force-push or reset main.
