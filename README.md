# ViralFoundry

ViralFoundry is the seed of an autonomous short-form content operating system. The goal is not simply to generate videos. The goal is to run a repeatable experiment loop:

1. Generate and rank content ideas across monetizable niches.
2. Draft scripts, captions, render plans, and platform variants.
3. Enforce provenance, synthetic-media, rights, and platform policy checks.
4. Schedule or publish through official API adapters.
5. Collect engagement and revenue signals.
6. Feed those signals into the next batch of ideas.

The first implementation is intentionally local and dependency-light. It creates a schedule, stores a content ledger in SQLite, writes dry-run publish jobs, and scores engagement snapshots. The production path is documented in `docs/architecture.md`.

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
PYTHONPATH=src python3 -m viralfoundry publish-dry-run --plan var/outbox/plan.json
PYTHONPATH=src python3 -m viralfoundry ingest-sample-metrics
PYTHONPATH=src python3 -m viralfoundry rank
PYTHONPATH=src python3 -m unittest discover -s tests
```

## Current Capabilities

- Niche configuration in `config/niches.json`.
- Multi-platform schedule generation for TikTok, Instagram Reels, and YouTube Shorts.
- Rights-aware policy gate that blocks unauthorized clipping and flags review-required work.
- SQLite persistence for content items, publish jobs, metrics, and performance scores.
- Dry-run publisher that writes outbox payloads instead of touching real accounts.
- Engagement scoring that normalizes views, engagement, completion proxy, follower deltas, revenue, and policy risk.

## Next Build Steps

1. Add real generation providers for scripts, voice, captions, and render manifests.
2. Add FFmpeg or Remotion render workers.
3. Add a minimal dashboard for approval, calendar, and metrics.
4. Integrate YouTube upload first because the official API path is comparatively clear.
5. Add TikTok and Instagram once app review, OAuth, and account setup are ready.

## Research

The strategy and constraints are summarized in:

- `docs/research-brief.md`
- `docs/strategy.md`
- `docs/architecture.md`
- `docs/roadmap.md`
- `docs/policy-guardrails.md`
