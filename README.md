# ViralFoundry

ViralFoundry is the seed of an autonomous short-form content operating system. The goal is not simply to generate videos. The goal is to run a repeatable experiment loop:

1. Generate and rank content ideas across monetizable niches.
2. Draft scripts, captions, render plans, and platform variants.
3. Enforce provenance, synthetic-media, rights, and platform policy checks.
4. Schedule or publish through official API adapters.
5. Collect engagement and revenue signals.
6. Feed those signals into the next batch of ideas.

The first implementation is intentionally local and dependency-light. It creates a schedule, stores a content ledger in SQLite, writes reviewable draft packages, writes dry-run publish jobs, and scores engagement snapshots. The production path is documented in `docs/architecture.md`.

## Why This Shape

The research points to one practical conclusion: high-throughput faceless content can work, but lazy reposting and generic AI output are increasingly poor monetization bets. The system is designed around original formats, official posting paths, asset provenance, and a learning loop.

Recommended first channels:

- `archive-317`: original AI horror universe with recurring lore and owned IP.
- `setup-under-budget`: faceless gear and AI-tool explainers with affiliate intent.
- `internet-mysteries`: sourced mini-documentaries and internet history explainers.
- `clip-doctor`: authorized streamer clipping plus commentary, only with permission.

Avoid as a default:

- Unauthorized streamer clips.
- Scraped Reddit stories with generic gameplay.
- Reposted compilations with only captions, filters, or speed changes.
- High-volume duplicate posts across many accounts.

## Quick Start

```bash
cd /Users/ishaanbhatt/Developer/ViralFoundry
PYTHONPATH=src python3 -m viralfoundry init-db
PYTHONPATH=src python3 -m viralfoundry plan --days 7 --out var/outbox/plan.json
PYTHONPATH=src python3 -m viralfoundry draft --plan var/outbox/plan.json --out var/drafts
PYTHONPATH=src python3 -m viralfoundry render --draft-index var/drafts/index.json --out var/renders
PYTHONPATH=src python3 -m viralfoundry publish-dry-run --plan var/outbox/plan.json
PYTHONPATH=src python3 -m viralfoundry ingest-sample-metrics
PYTHONPATH=src python3 -m viralfoundry rank
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Draft Packages

Phase 1 runs after `plan` and before any publishing dry run. The local draft generator reads the planned schedule and writes inspection-ready JSON artifacts without calling public platform APIs:

```bash
PYTHONPATH=src python3 -m viralfoundry draft --plan var/outbox/plan.json --out var/drafts
```

Use `--limit N` for a smaller local batch while reviewing the output. The command writes `var/drafts/index.json` plus one `draft.json` package per selected planned post. Each package includes:

- Script or beat-sheet JSON.
- Caption and hashtag variants.
- Render manifest for a future FFmpeg or Remotion worker.
- Voice or narration manifest when voice is part of the draft.
- Policy findings, disclosure requirements, and owner-review status.
- Asset provenance records with source type, prompt or source reference, license status, and checksum when available.

The draft package is still a review artifact, not a public post. Run `publish-dry-run` only after the owner can inspect the generated script, caption, manifest, provenance, and policy output.

## Local Renders

Phase 2 renders draft packages into real 9:16 MP4 files with local preflight reports. Install `ffmpeg` and `ffprobe` on `PATH`, then run:

```bash
PYTHONPATH=src python3 -m viralfoundry render --draft-index var/drafts/index.json --out var/renders
```

Use `--limit N` for a smaller render batch. Each render writes `render.mp4` and `preflight.json`; attempts are also stored in SQLite so failed renders remain retryable. The local preflight checks resolution, codec, duration tolerance, audio presence, loudness, caption burn-in metadata, safe-margin metadata, and sustained black frames.

## Current Capabilities

- Niche configuration in `config/niches.json`.
- Multi-platform schedule generation for TikTok, Instagram Reels, and YouTube Shorts.
- Rights-aware policy gate that blocks unauthorized clipping and flags review-required work.
- SQLite persistence for content items, publish jobs, metrics, and performance scores.
- Local draft packages with script, caption variants, voice manifest, render manifest, policy output, and provenance metadata.
- Local 9:16 MP4 rendering with preflight reports and persisted retryable render attempts.
- Dry-run publisher that writes outbox payloads instead of touching real accounts.
- Engagement scoring that normalizes views, engagement, completion proxy, follower deltas, revenue, and policy risk.

## Next Build Steps

1. Add a minimal dashboard for approval, calendar, renders, and metrics.
2. Integrate YouTube upload first because the official API path is comparatively clear.
3. Add TikTok and Instagram once app review, OAuth, and account setup are ready.
4. Replace local generation stubs with provider-backed generation where it improves quality and remains policy-compliant.

## Research

The strategy and constraints are summarized in:

- `docs/research-brief.md`
- `docs/strategy.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/policy-guardrails.md`
