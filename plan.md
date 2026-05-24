# Product Plan

## Core Direction

Build the application layer as a local-first video draft machine, but avoid self-building every production capability. The product should own the workflow, package structure, review process, validation, and integration layer while relying on third-party providers for specialized video generation, creative production, or publishing capabilities when that is more practical than building from scratch.

## Third-Party Video Production And API Strategy

Use a hybrid model:

- Use freelancers or agencies, such as Fiverr or Upwork, for creative direction, launch assets, example videos, motion templates, thumbnails, voiceover style, and brand polish.
- Use video-generation APIs for repeatable in-app generation, async render jobs, status tracking, storage, billing, and user-facing output.
- Keep Fiverr or similar marketplaces out of the runtime path unless the product is intentionally a concierge/manual service.
- Wrap providers behind an internal interface so the app can switch between services such as Runway, Google Veo, OpenAI Sora, Synthesia, HeyGen, Replicate, or future providers without rewriting the product workflow.

Decision principle: build the orchestration layer, not the entire video engine. The application should generate briefs, prompts, packages, QA artifacts, review states, and publish-ready payloads; external services should handle the most expensive or specialized video production work when needed.

## Implementation Implications

- Design provider-agnostic job models for video generation requests, job status, outputs, errors, and cost metadata.
- Preserve the existing local renderer as a deterministic fallback and validation tool.
- Add integration phases only after the local draft, render, quality, review, and publish-prep workflow is reliable.
- Treat third-party output as one possible render source, not the single source of truth for the product package.
- Add clear provenance to generated assets so users can distinguish local renders, API-generated video, and human-produced assets.

## Near-Term Plan

Continue the local product roadmap in `progress.md`, then add provider abstraction and publish controls only after quality gates are in place. The current integration foundation uses a local dry-run brand kit registry, workspace/job registry, dry-run provider contracts, dry-run publish payloads, a publish ledger, and a manual approval queue before any paid API calls or live uploads are added.

## Future Hosting And Revenue Plan

The current project should be treated as the local production engine. The hosted business should wrap this engine with accounts, persistence, billing, background jobs, asset storage, approvals, and publishing controls.

### Target Hosted Architecture

- Web application: customer-facing dashboard for brief creation, brand kits, review, approvals, billing, and downloads.
- API service: validates briefs, creates jobs, exposes job status, reads package metadata, and enforces account permissions.
- Worker service: runs draft generation, rendering, quality scoring, publish-prep, provider API calls, and future upload jobs.
- Database: Postgres for users, teams, briefs, jobs, package versions, asset records, approval states, billing entitlements, and publish ledger entries.
- Queue: Redis/BullMQ, Cloud Tasks, SQS, or another managed queue for asynchronous render and publish jobs.
- Object storage: S3, Cloudflare R2, or Google Cloud Storage for MP4s, thumbnails, previews, manifests, and package artifacts.
- Auth provider: Clerk, Auth.js, Supabase Auth, or another provider that supports production user and team workflows.
- Billing provider: Stripe subscriptions, usage credits, and billing webhooks.
- Observability: structured logs, queue metrics, job duration, provider spend, failed render alerts, and publish failure alerts.

The hosted app should never make users wait on a long render inside a synchronous web request. Users submit work, the API creates a job, the worker produces artifacts, and the UI shows clear job states.

### Infrastructure Options

Recommended lean launch stack:

- Frontend: Vercel.
- API: Vercel route handlers for lightweight requests, or a dedicated Render/Fly/Railway service if the API needs long-running control.
- Workers: Render, Fly.io, Railway, AWS ECS, or Google Cloud Run jobs.
- Database: Neon, Supabase, RDS, or Cloud SQL Postgres.
- Queue: Upstash Redis, managed Redis, SQS, or Cloud Tasks.
- Assets: Cloudflare R2 or S3.
- Payments: Stripe.

Avoid relying only on serverless functions for rendering. Video rendering, provider polling, retries, and large file handling fit better in a worker process with durable storage.

### Production Data Model

Start with these core entities:

- `users`
- `workspaces`
- `workspace_members`
- `brand_kits`
- `briefs`
- `generation_jobs`
- `draft_packages`
- `assets`
- `quality_reports`
- `publish_payloads`
- `publish_approvals`
- `publish_ledger_entries`
- `billing_customers`
- `billing_entitlements`
- `audit_events`

Each generated artifact should have provenance: local renderer, AI provider, human-produced asset, upload target, provider job ID, license metadata, and cost metadata when available.

Local brand kit artifacts now act as the bridge between the local engine and the hosted `brand_kits` entity. They are not account-owned yet; the hosted version needs workspace-scoped ownership, uploaded asset storage, permission checks, audit events, and version history before customers can safely manage multiple brands.

Local workspace job artifacts now act as the bridge between the local engine and hosted `workspaces`, `generation_jobs`, and `draft_packages`. They are reviewable local records, not real account state; the hosted version needs authenticated users, workspace memberships, durable job rows, object-storage asset references, billing entitlements, and audit events before customers can safely run jobs.

### Product Milestones

1. Hosted read-only prototype: upload or enter briefs, run the current engine manually or from a worker, and show generated outputs in a dashboard.
2. Account-backed MVP: users can log in, create briefs, run jobs, view history, download videos, and manage a simple brand kit.
3. Paid private beta: Stripe subscription, usage limits, workspace ownership, and support workflows.
4. Approval workflow: job states, package versions, regenerate actions, manual approval gates, and audit log.
5. First platform integration: one live upload client, publish ledger, retries, and idempotency.
6. Provider-backed production: voiceover, video generation, stock media, or subtitle provider adapters with cost tracking.
7. Agency/team tier: multiple brand kits, team seats, approval queues, higher limits, and export bundles.

### Revenue Strategy

The fastest path to revenue is likely not pure self-serve automation on day one. Start with a narrow paid workflow that can tolerate some manual review while the hosted product matures.

Potential offers:

- Concierge package: monthly short-form content package with human review and final polish.
- Self-serve starter plan: generate and download a fixed number of draft packages per month.
- Pro plan: brand kits, higher render limits, platform variants, and quality reports.
- Agency plan: multiple brands, seats, approval workflows, and bulk generation.
- Usage add-ons: extra renders, provider-backed video generations, voiceover generations, or publish slots.

Recommended first monetization path:

1. Sell a concierge or assisted beta to a small group of users.
2. Use those users' briefs to harden templates, quality gates, and brand-kit features.
3. Add Stripe once the workflow has repeatable value and clear limits.
4. Keep live publishing behind manual approval until failure handling and platform compliance are mature.
5. Introduce higher-margin provider-backed upgrades only after local generation and review flows are trusted.

### Production Readiness Gates

Before using this for real revenue at scale, the hosted product needs:

- Authentication and authorization at every workspace boundary.
- Billing webhooks and entitlement enforcement.
- Secure environment variable and secret handling.
- Durable object storage with signed download URLs.
- Persistent job state and retry-safe queue processing.
- Asset deletion and data-retention controls.
- Backups for database and object storage.
- Platform terms, privacy policy, acceptable-use policy, and customer support path.
- Abuse, copyright, brand-safety, and claims-review controls.
- Admin tools for failed jobs, billing support, and publish incidents.
- Clear labeling of local renders, AI-generated assets, and human-produced assets.
