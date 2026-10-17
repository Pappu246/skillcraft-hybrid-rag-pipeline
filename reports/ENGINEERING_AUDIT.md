## Deployment / current verification (updated 2026-10-17)

The latest merged application code is at main commit `1c370c3e610520b042597c23464c216e762d4fa6`. The latest production deployment currently listed by Vercel is older and must not be confused with that merged commit.

- [PR #9 — Harden PDF ingestion and hybrid retrieval](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/9) merged as `b4371a8e3fe4bf227c6ba17014c3bbf8753e26dc`.
- [PR #10 — Add evidence export and one-click search reset](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/10) merged as `933d709586015e18fd2f0eef9975ed165caae2e5`.
- [PR #11 — Add session-only recent search history](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/11) merged as `48e545f75227c77a3432f31553b3eef1bf840eb0`.
- [PR #13 — Add downloadable retrieval comparison CSV](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/pull/13) merged as `1c370c3e610520b042597c23464c216e762d4fa6`. The dedicated PR CI [#39051120832](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/39051120832) passed on the tested branch commit, and post-merge main CI [#39051290703](https://github.com/Pappu246/skillcraft-hybrid-rag-pipeline/actions/runs/39051290703) passed.
- The latest production deployment listed by Vercel is `dpl_EBUQC7mJdeRqp4W34eKfjQyWGQKN`, production target, deployment SHA `f255792e89ae949ec3372484168ef1f606a0e606`. Its app source is unchanged from the prior verified UI release `48e545f`; **the CSV export from commit `1c370c3` is not yet live**.
- An attempt to create a deployment from the merged commit was rejected with Vercel HTTP 402 `payment_required`: resource `api-deployments-free-per-day`, “more than 100” deployments for the day, retry window 86400 seconds. Do not bypass billing/security limits or reassign aliases to an older preview. Wait for Vercel to permit another deployment or obtain an authorized plan/team resolution.
- Current canonical homepage `https://skillcraft-hybrid-rag-pipeline.vercel.app/` returned HTTP 200; `/_stcore/health` returned HTTP 200 with body `ok`. These checks are against the currently available production deployment, not the unshipped CSV commit.
- The checked 30-minute filtered runtime-log query returned no error/fatal entries. This does not prove every user path is error-free.
- Streamlit AppTest covers initial rendering, a cited BM25 fallback, Markdown evidence download, recent-query restoration, clear-results interaction, and CSV download serialization/status rows. Real browser/WebSocket interaction against the private preview was not executed here because the preview is SSO-protected.
- The matching `Module1.pdf` is absent. The 34-question metrics remain historical retrieval metrics and are not post-change measurements or answer-factuality scores.

## Rollback

The latest production deployment available to roll back to is `dpl_EBUQC7mJdeRqp4W34eKfjQyWGQKN` from main docs commit `f255792`; its application code is equivalent to the previously verified `48e545f` app code. When Vercel deployment quota allows a new deployment, deploy current main commit `1c370c3` (or the later CI-verified main commit), then verify the canonical root and health endpoint. If a later release regresses, restore the known-good deployment using an authorized Vercel action. Preserve git history; do not force-push or reset main.
