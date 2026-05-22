# Roadmap

## Phase 0: Strategic Scaffold

Status: complete for the initial local scaffold.

Deliverables:

- Research brief.
- Initial niche portfolio.
- Local planner.
- Policy gate.
- SQLite ledger.
- Dry-run publisher.
- Metrics scoring.

Exit criteria:

- Tests pass.
- A seven-day schedule can be generated.
- Dry-run outbox payloads can be written.
- Sample metrics can be scored.

## Phase 1: Generation MVP

Goal: produce publish-ready drafts without public posting.

Build:

- LLM script provider.
- Caption and hashtag variants.
- Voice provider adapter.
- Render manifest generator.
- Basic FFmpeg or Remotion template.
- Asset provenance tracking.

Exit criteria:

- System creates a complete draft package for each selected post.
- Owner can inspect script, caption, render manifest, and policy findings.

## Phase 2: Render and QA

Goal: produce real 9:16 MP4s locally.

Build:

- FFmpeg render pipeline or Remotion worker.
- Caption burn-in.
- Safe-margin checks.
- Duration, codec, and loudness checks.
- Black-frame and missing-audio checks.

Exit criteria:

- Generated videos pass platform preflight checks.
- Render failures are persisted and retryable.

## Phase 3: YouTube First

Goal: ship the first official publishing integration.

Build:

- Google OAuth.
- YouTube upload provider.
- Private upload and scheduled publish flow.
- Synthetic-media disclosure field.
- Status polling.
- YouTube Analytics ingestion.

Exit criteria:

- One approved video can upload privately.
- Metrics snapshots populate after publication.

## Phase 4: Dashboard

Goal: make the system operational without reading JSON.

Build:

- Calendar view.
- Approval queue.
- Policy findings view.
- Metrics dashboard.
- Account kill switch.
- Notification settings.

Exit criteria:

- Owner can approve, pause, inspect, and review results from the UI.

## Phase 5: TikTok and Instagram

Goal: add short-form platform adapters after account and app review setup.

Build:

- TikTok Direct Post provider.
- TikTok status polling and webhooks.
- Instagram Reels container/publish provider.
- Instagram Insights ingestion.
- Provider-specific error states.

Exit criteria:

- Posts are created through official APIs.
- Analytics are normalized into the same scoring model.

## Phase 6: Learning Loop

Goal: turn performance into better future content.

Build:

- Account and niche baselines.
- Hook-family scoring.
- Topic fatigue detection.
- Winner follow-up generator.
- Suppression list for weak patterns.
- Simple bandit allocation by platform and niche.

Exit criteria:

- The next planned batch includes explicit learned hypotheses from prior metrics.
