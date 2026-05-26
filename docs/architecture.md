# Architecture

## North Star

ViralFoundry should become a content operating system with memory. Every asset, prompt, caption, schedule, post, and metric should be traceable. The system should be able to answer:

- Why did we make this video?
- Which hypothesis did it test?
- Which assets and rights were used?
- Which account posted it?
- Which policy checks passed?
- What happened after publishing?
- What should the next batch learn from it?

## Local MVP

The current scaffold implements:

- JSON niche configuration.
- Schedule planner.
- Deterministic ranked idea generation.
- Policy gate.
- Local draft package generator.
- Local FFmpeg render and preflight worker.
- YouTube upload preflight and official Data API payload writer.
- SQLite ledger.
- Dry-run publisher.
- Sample metrics ingestion.
- Performance ranking.

Commands:

```bash
PYTHONPATH=src python3 -m viralfoundry init-db
PYTHONPATH=src python3 -m viralfoundry plan --days 7
PYTHONPATH=src python3 -m viralfoundry draft
PYTHONPATH=src python3 -m viralfoundry render
PYTHONPATH=src python3 -m viralfoundry upload-youtube --owner-approved
PYTHONPATH=src python3 -m viralfoundry publish-dry-run
PYTHONPATH=src python3 -m viralfoundry ingest-sample-metrics
PYTHONPATH=src python3 -m viralfoundry rank
```

## Production Services

Studio API:

- Owner dashboard.
- Account connections.
- Approval queue.
- Calendar.
- Metrics.
- Kill switch.

Idea Engine:

- Uses trend inputs, past winners, search signals, and niche rules.
- Outputs hypotheses, not just topics.

Script Engine:

- Creates hooks, scripts, captions, hashtags, and platform variants.
- Stores prompt, model, temperature, examples, and output hash.

Asset Engine:

- Generates voice, images, video clips, thumbnails, and music.
- Stores provider, model, license, prompt, attribution, and source rights.

Render Engine:

- Produces 9:16 MP4s with captions and thumbnails.
- Validates codec, duration, resolution, loudness, black frames, and caption overflow.

Policy Engine:

- Checks rights, AI disclosure, sensitive content, sponsor disclosure, duplicate content, and platform-specific rules.

Publisher:

- Uses official provider adapters.
- Owns scheduling when a platform does not support native scheduling.
- Tracks upload, processing, publish, failure, retry, and external post IDs.

Metrics Collector:

- Pulls platform metrics.
- Stores raw payloads.
- Normalizes views, likes, comments, shares, saves, watch time, follower deltas, and revenue.

Learning Loop:

- Scores results against account and platform baselines.
- Promotes winners.
- Suppresses weak patterns.
- Generates next hypotheses.

Notifier:

- Sends summaries when batches are ready, posts publish, metrics spike, accounts fail, or policy blocks content.

## Data Model

Production should move to Postgres with these tables:

- owners
- workspaces
- platform_accounts
- campaigns
- ideas
- content_items
- content_variants
- assets
- renders
- publish_jobs
- metric_snapshots
- performance_scores
- policy_reviews
- audit_events

The local SQLite schema mirrors the highest-value early concepts: content items, publish jobs, metrics, and scores.

## Lifecycle

Canonical lifecycle:

```text
DRAFT_IDEA
SCRIPT_READY
RENDER_READY
NEEDS_OWNER_REVIEW
APPROVED_FOR_PUBLISH
SCHEDULED
PUBLISHED
METRICS_COLLECTING
LEARNING_APPLIED
BLOCKED_BY_POLICY
FAILED
```

Autonomy should increase only as evidence improves:

1. Draft only.
2. Draft plus render.
3. Schedule with owner approval.
4. Publish within strict account/niche bounds.
5. Optimize across channels.

## Provider Interfaces

Social providers should expose:

- capabilities
- validate post
- upload media
- create post
- schedule post if supported
- poll status
- get metrics
- refresh auth

Generation providers should expose:

- LLM script generation
- image generation
- video generation
- TTS
- transcription
- moderation
- music or sound effects

Provider adapters must preserve raw request and response metadata without logging secrets.

## Queue Design

Queues:

- idea.generate
- script.generate
- asset.generate
- render.video
- policy.review
- publish.prepare
- publish.execute
- publish.poll_status
- metrics.collect
- learning.score
- notify.owner
- maintenance.token_refresh

Each job needs:

- idempotency key
- workspace id
- entity id
- attempt count
- max attempts
- locked until
- dead-letter reason

## Scale Path

Phase one:

- Local Python CLI.
- SQLite.
- Dry-run outbox.

Phase two:

- FastAPI service.
- Postgres.
- Redis or Postgres-backed queue.
- Local FFmpeg/Remotion renderer.

Phase three:

- Cloud workers.
- Object storage such as S3, GCS, or R2.
- Secrets manager.
- Observability and traces.
- Direct YouTube provider with OAuth token storage, status polling, and analytics ingestion.
- TikTok and Instagram provider adapters.
