# Local Video Draft Machine

A local-first content production pipeline for turning structured video briefs into complete draft packages, rendered MP4s, thumbnails, quality reports, dry-run provider job contracts, dry-run publish payloads, and operations artifacts.

The project is intentionally not a public posting bot yet. Today it is a deterministic local production system: it creates assets, scores readiness, prepares platform-specific payloads, and makes the missing production pieces explicit before anything can be posted publicly.

## What This Application Does

The pipeline starts from `content/briefs.json` and produces:

- Complete draft folders under `drafts/<slug>/`
- Scripts, storyboards, captions, metadata, design briefs, motion plans, audio plans, and platform variants
- Real local MP4 videos under `output/videos/`
- Thumbnail PNGs and preview-frame PNGs
- Render manifests that describe generated assets
- A local HTML review board at `output/review/index.html`
- Quality reports under `output/quality/`
- Dry-run provider job contracts under `output/provider-jobs/`
- Dry-run publish payloads under `output/publish/`
- An operations report and content calendar under `output/operations/`

Use it when you want a repeatable local factory for short-form content ideas, review, and publish preparation before investing in hosted infrastructure, platform upload clients, paid APIs, or paid traffic.

## Repository Map

```text
.
├── content/
│   ├── briefs.json              # Input video briefs
│   └── design-system.json       # Visual, motion, audio, and platform rules
├── drafts/                      # Generated per-video draft packages
├── output/
│   ├── videos/                  # Rendered MP4 files
│   ├── thumbnails/              # Generated thumbnail images
│   ├── previews/                # Generated preview frames
│   ├── manifests/               # Render metadata
│   ├── review/                  # Local review board
│   ├── quality/                 # Quality scores and recommendations
│   ├── provider-jobs/           # Dry-run video provider contracts
│   ├── publish/                 # Dry-run publishing payloads
│   └── operations/              # Run report and content calendar
├── src/                         # Pipeline implementation
├── package.json                 # NPM scripts and runtime requirements
├── plan.md                      # Product and hosting strategy
└── progress.md                  # Current roadmap progress
```

## Prerequisites

- Node.js 20 or newer
- npm
- Enough local disk space for generated MP4 files

The renderer uses the npm package `@ffmpeg-installer/ffmpeg`, so you do not need to install FFmpeg globally.

Check your local runtime:

```bash
node --version
npm --version
```

If `node --version` is below 20, install or switch to Node 20 before running the pipeline.

## Local Setup

From the project root:

```bash
npm install
```

Then run the full local pipeline:

```bash
npm run full
```

This command generates draft packages, renders MP4s, builds review assets, scores quality, generates dry-run provider contracts, prepares dry-run publish payloads, creates operations artifacts, and validates the result.

Expected success output ends with a validation summary similar to:

```text
Validated 2 draft package(s) and MP4 render(s).
```

## Common Commands

```bash
npm run generate
```

Generates draft packages from `content/briefs.json`.

```bash
npm run render
```

Renders MP4 videos, thumbnails, preview frames, and render manifests from generated draft packages.

```bash
npm run review
```

Builds the local review board at `output/review/index.html`.

```bash
npm run quality
```

Scores generated packages and writes quality reports to `output/quality/`.

```bash
npm run providers
```

Creates dry-run provider job contracts in `output/provider-jobs/`. This does not submit paid API work.

```bash
npm run publish:prepare
```

Creates dry-run publish payloads in `output/publish/`. This does not publish publicly.

```bash
npm run operations
```

Creates the operations report and content calendar.

```bash
npm run build
```

Runs the baseline build flow: generate, render, and review.

```bash
npm run validate
```

Validates generated packages, videos, thumbnails, previews, manifests, quality reports, provider jobs, publish payloads, review board output, and operations artifacts.

```bash
npm run full
```

Runs the complete local product workflow plus validation. This is the main command for day-to-day use.

## Input Briefs

Edit `content/briefs.json` to add, remove, or modify videos.

Each brief supports:

- `title`
- `audience`
- `objective`
- `takeaways`
- `tone`
- `platforms`
- `durationSeconds`

Example workflow:

1. Add a new brief to `content/briefs.json`.
2. Run `npm run full`.
3. Review the generated draft package in `drafts/<slug>/`.
4. Watch the generated MP4 in `output/videos/<slug>.mp4`.
5. Open `output/review/index.html` in a browser for review.
6. Check `output/quality/<slug>.quality.json` before preparing any real publishing integration.

## Design System

The visual and production rules live in `content/design-system.json`.

Generated packages include concrete design artifacts:

- `design-brief.json`
- `platform-variants.json`
- `shot-list.json`
- `motion-plan.json`
- `audio-plan.json`
- `captions.srt`
- `production-notes.md`

The renderer consumes package-level design fields such as theme, layout, motion cue, caption timing, and output destinations. `npm run validate` checks that every package has the expected design, platform, motion, audio, caption, thumbnail, preview, manifest, and review-board coverage.

## Quality And Approval

Quality reports are written to `output/quality/`.

The scoring checks:

- Creative completeness
- Timed storyboard coverage
- Design coverage
- Platform variants
- Captions
- Rendered assets
- Explicit publish blockers

Current recommendation values:

- `approved_for_publish_prep`
- `needs_light_review`
- `revise_before_publish_prep`

Treat `approved_for_publish_prep` as approval to prepare assets, not approval to post publicly. Final voiceover, brand review, credentials, and platform-specific publishing checks still need to exist before the system can become a revenue-grade publishing tool.

## Publishing Status

Publishing is currently dry-run only.

`output/publish/` contains platform-specific JSON payloads with:

- Video path
- Thumbnail path
- Caption text
- Platform target
- Quality score
- Readiness status
- Required credential name
- Future upload client contract
- Idempotency key

The local machine does not post publicly yet. Known blockers are:

- Final voiceover or approved audio source
- Brand pack
- Platform credentials
- Platform upload clients
- Publish ledger for returned platform IDs
- Human approval controls before live posting

## Provider Job Contracts

Provider integration is also dry-run only.

`output/provider-jobs/` contains one provider job contract per draft package plus an aggregate provider plan. These artifacts map each local package, storyboard, design system, captions, local render, and quality report into a provider-agnostic request and response shape without submitting paid API work.

The first adapter is `dry-run-video-provider`. It records the live integration requirements the hosted product will need next: API credentials, status polling, durable storage, callbacks, and usage/cost ledgers. Local MP4s remain the fallback render source until external provider outputs can pass review.

## Opening Local Outputs

The project does not currently run a web server. Generated outputs are ordinary local files.

Open the review board directly:

```bash
open output/review/index.html
```

Open generated videos:

```bash
open output/videos
```

Open the content calendar:

```bash
open output/operations/content-calendar.md
```

## Troubleshooting

If generated files are missing, run the full pipeline again:

```bash
npm run full
```

If validation fails, read the exact error message. It usually points to a stale or missing artifact such as a draft package, quality report, render manifest, thumbnail, preview frame, or publish payload.

If MP4 rendering fails, verify:

- Node.js is version 20 or newer.
- `npm install` completed successfully.
- The machine has enough disk space.
- The generated draft package exists under `drafts/<slug>/`.

If quality scores are lower than expected, inspect:

- `drafts/<slug>/package.json`
- `drafts/<slug>/production-notes.md`
- `output/quality/<slug>.quality.json`

## Production Hosting Plan

The current application is a strong local prototype. To productionize it and use it to generate revenue, turn it into a hosted workflow with durable storage, accounts, billing, render jobs, publish approvals, and platform integrations.

### Phase 1: Productize The Local Workflow

Goal: make the local pipeline reliable enough to become a hosted backend contract.

- Keep `npm run full` green as the local acceptance test.
- Define a stable package schema for briefs, generated assets, quality reports, publish payloads, and operations reports.
- Add sample inputs that represent real paying-user use cases.
- Add a manual review checklist for brand safety, claims, compliance, and platform fit.
- Decide the first paid offer: done-for-you content production, self-serve content generation, or a hybrid concierge workflow.

### Phase 2: Add A Hosted Application Layer

Goal: wrap the generator in a real product interface.

Recommended architecture:

- Frontend: Next.js or another React framework for brief creation, review, approvals, billing, and account settings.
- API: Node.js service that accepts briefs, creates generation jobs, and exposes package status.
- Worker: background worker that runs generation, rendering, scoring, and publish-prep jobs.
- Database: Postgres for users, teams, briefs, jobs, assets, approvals, publish records, and billing state.
- Queue: Redis, BullMQ, Cloud Tasks, or a managed queue for async render and publish jobs.
- Object storage: S3, Cloudflare R2, or Google Cloud Storage for MP4s, thumbnails, manifests, and package artifacts.
- Auth: Clerk, Auth.js, Supabase Auth, or another production auth provider.
- Billing: Stripe subscriptions and usage-based add-ons.

The first hosted version should not run long video jobs inside the web request. Users should submit a brief, receive a job ID, and watch status update while workers process the package asynchronously.

### Phase 3: Choose Hosting Infrastructure

Recommended simple stack:

- Vercel for the web application.
- Render, Fly.io, Railway, or AWS ECS for long-running workers.
- Neon, Supabase, or RDS for Postgres.
- Upstash Redis or a managed Redis instance for queues.
- Cloudflare R2 or S3 for generated assets.
- Stripe for payments.

Avoid putting all rendering work on serverless functions unless video jobs are guaranteed to finish within the provider's time and file-size limits. MP4 rendering and future video API orchestration are better handled by workers.

### Phase 4: Add Revenue-Critical Product Features

Goal: make the app safe enough for real customers and useful enough to charge for.

- Account workspaces and team ownership
- Saved brand kits with colors, fonts, logos, disclaimers, and CTA templates
- Credit or subscription limits per workspace
- Brief templates by niche, platform, and funnel stage
- Job history with rerun, duplicate, and regenerate actions
- Human approval states before publishing
- Versioned generated packages
- Download links for MP4s and thumbnails
- Publish readiness report for each generated asset
- Audit log for billing, publishing, and manual approvals
- Basic analytics for asset output volume and platform readiness

### Phase 5: Add Platform Publishing Integrations

Goal: move from dry-run payloads to controlled public posting.

- Start with one platform, such as YouTube Shorts, before adding TikTok, Instagram Reels, and LinkedIn.
- Keep platform upload clients behind the existing dry-run payload contract.
- Store returned platform IDs in a publish ledger.
- Add retry handling, idempotency keys, and clear failed-publish states.
- Require explicit human approval before live posting.
- Keep downloaded/exportable assets available even if auto-publishing fails.

### Phase 6: Add Third-Party Video And Voice Providers

Goal: improve production value without rebuilding every media engine internally.

- Add provider adapters for voiceover, video generation, subtitles, stock media, or avatars.
- Track provider, cost, job ID, prompt, output URL, and license metadata for every generated asset.
- Preserve local rendering as a deterministic fallback and QA baseline.
- Avoid locking the product to a single provider contract.

### Phase 7: Launch Revenue Experiments

Start with offers that match the product's current strengths:

- Concierge short-form content packages for founders, consultants, agencies, and creators.
- Monthly subscription for a fixed number of generated content packages.
- Usage-based credits for additional renders, platform variants, or provider-backed generations.
- Agency workflow plan with multiple brand kits and approval queues.
- Download-only plan before live auto-publishing is fully trusted.

Useful early pricing tests:

- Starter: fixed monthly price for local-style generated draft packages and downloads.
- Pro: higher monthly price with brand kits, quality reports, and platform-ready variants.
- Agency: workspace seats, multiple brands, approval flows, and higher generation limits.
- Concierge: premium done-for-you service with human review and final polish.

### Phase 8: Production Readiness Checklist

Before charging customers at scale, add:

- Terms of service, privacy policy, and acceptable-use policy
- Secure secrets management
- Per-user and per-team authorization checks
- Asset retention and deletion controls
- Billing webhooks and entitlement enforcement
- Observability for job failures, queue depth, render time, and provider spend
- Backups for database and object storage
- Manual admin tools for failed jobs and customer support
- Abuse controls for generated content
- Clear disclosure when assets are locally rendered, AI-generated, or human-produced

## Current Roadmap

Use `progress.md` as the implementation checklist for the local pipeline. Use `plan.md` for the broader product and hosting strategy.
