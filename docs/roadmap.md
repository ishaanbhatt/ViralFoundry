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

Status: complete for the selected local draft-package slice. Provider-backed generation can still replace the local stubs later, but the Phase 1 MVP now produces reviewable draft packages from an existing plan file.

Goal: produce publish-ready drafts without public posting.

Build:

- Complete: draft-package CLI that reads `var/outbox/plan.json` and writes draft artifacts under `var/drafts/`.
- Complete: script or beat-sheet generator.
- Complete: caption and hashtag variants.
- Complete: render manifest generator for a future FFmpeg or Remotion worker.
- Complete: voice or narration manifest.
- Complete: policy findings and owner-review status in each draft package.
- Complete: asset provenance tracking with source type, prompt or source reference, license status, and checksum when available.

Deferred out of this slice:

- Public publishing.
- Real MP4 rendering.
- Platform OAuth.
- Autonomous owner approval.

Exit criteria:

- System creates a complete draft package for each selected post.
- Owner can inspect script, caption, render manifest, and policy findings.
- Draft packages preserve provenance and disclosure metadata needed by `docs/policy-guardrails.md`.

Validation evidence:

- Complete: `PYTHONPATH=src python3 -m viralfoundry draft --plan var/outbox/plan.json --out var/drafts --limit 3` wrote 3 draft packages and `var/drafts/index.json`.
- Complete: sample package contained `script`, `caption_variants`, `voice`, `render_manifest`, `provenance`, and `policy`.
- Complete: `PYTHONPATH=src python3 -m unittest discover -s tests` ran 6 tests successfully.

## Phase 2: Render and QA

Status: complete for the selected local render-and-preflight slice. The renderer produces real MP4 files from draft packages and records both successful and failed attempts in SQLite for retry.

Goal: produce real 9:16 MP4s locally.

Build:

- Complete: FFmpeg render pipeline from `var/drafts/index.json` into `var/renders/`.
- Complete: caption burn-in through generated caption frames.
- Complete: safe-margin metadata checks.
- Complete: duration, codec, and loudness checks.
- Complete: black-frame and missing-audio checks.
- Complete: render attempts table for persisted success/failure history.

Exit criteria:

- Generated videos pass platform preflight checks.
- Render failures are persisted and retryable.

Validation evidence:

- Complete: `PYTHONPATH=src python3 -m viralfoundry render --draft-index var/drafts/index.json --out var/renders --limit 1` wrote `render.mp4` and `preflight.json`.
- Complete: sample preflight reported h264, 1080x1920, 75.0s duration, audio present, mean volume -35.1 dB, no sustained black frames, and status `pass`.
- Complete: missing-renderer and failed-render attempts were persisted in SQLite with status `fail`.
- Complete: `PYTHONPATH=src python3 -m unittest discover -s tests` ran 11 tests successfully.

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
