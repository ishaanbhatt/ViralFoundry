# Product Roadmap Progress

Goal: keep building the local video draft machine until the major design aspects are represented as concrete artifacts and validated outputs.

## Phase 1 + Phase 2 Baseline

- [x] Generate complete draft packages from `content/briefs.json`.
- [x] Render real local MP4 files from generated packages.
- [x] Validate draft packages and rendered MP4 files.

## Design Coverage Roadmap

- [x] Define a reusable visual, motion, audio, caption, and platform design system.
- [x] Expand draft packages with design briefs, platform variants, shot lists, motion plans, audio plans, captions, and production notes.
- [x] Upgrade rendering so local MP4s use package-level design decisions instead of only generic text slates.
- [x] Generate thumbnails and preview frames for local review.
- [x] Build a local review board that shows each package, MP4, thumbnail, metadata, and QA state.
- [x] Extend validation to audit design coverage, sidecar assets, review board output, and render manifests.
- [x] Update documentation with the end-to-end design workflow and product roadmap.

## Phase 3: Quality And Approval

- [x] Score every draft package against creative, design, platform, caption, and render-readiness gates.
- [x] Generate per-video quality reports and an aggregate quality index.
- [x] Surface approval recommendations before anything is prepared for publishing.

## Phase 4: Publishing Preparation

- [x] Generate platform-specific publish payloads for every video and target platform.
- [x] Produce a publish plan that separates ready assets from missing credentials and final voiceover needs.
- [x] Keep publishing in local dry-run mode until platform integrations are added.

## Phase 5: Operations

- [x] Generate a content calendar from the locally rendered package set.
- [x] Generate an operations run report tying together drafts, renders, quality, review, and publish prep.
- [x] Add a single full-pipeline command that runs build, quality, provider contracts, publish prep, operations, and validation.

## Phase 6: Provider Abstraction

- [x] Add a dry-run video provider adapter behind a provider-agnostic request and response contract.
- [x] Generate one provider job contract per draft package without submitting paid API work.
- [x] Preserve local MP4s as the fallback render source and record provider provenance.
- [x] Extend validation and operations reporting to cover provider job artifacts.

## Phase 7: Publish Ledger And Approval Controls

- [x] Generate one dry-run publish ledger entry per platform payload.
- [x] Track future platform IDs, upload status, retry state, errors, idempotency keys, and approval blockers.
- [x] Require human approval in ledger state before any future live upload attempt.
- [x] Extend validation and operations reporting to cover publish ledger artifacts.

## Phase 8: Product Documentation

- [x] Document the full local product workflow across draft, design, render, QA, review, publish prep, and operations.
- [x] Document the provider contract, publish ledger phase, and the next integration phases left after local MP4 production is proven.

## Phase 9: Approval Queue

- [x] Generate one manual approval queue item per dry-run publish ledger entry.
- [x] Tie approval tasks back to review board, package, MP4, thumbnail, publish payload, idempotency key, and credential requirement.
- [x] Keep live upload disabled until explicit human approval, platform credentials, and live upload clients exist.
- [x] Extend validation and operations reporting to cover approval queue artifacts.

## Phase 10: Brand Kit Registry

- [x] Add a local dry-run brand kit registry input with positioning, audience, voice, visual tokens, typography, placeholder assets, compliance notes, and provenance.
- [x] Generate brand kit artifacts under `output/brand-kits/` for operator review.
- [x] Keep brand kits local until hosted accounts, workspace ownership, uploaded assets, and permission checks exist.
- [x] Extend build, validation, operations reporting, and documentation to cover brand kit artifacts.

## Phase 11: Workspace Job Registry

- [x] Add a local dry-run workspace input with owner, plan, permission, entitlement, default brand kit, and provenance placeholders.
- [x] Generate one workspace job record per draft package that links package, render, quality, provider, publish, ledger, approval, blocker, and next-action state.
- [x] Keep workspace jobs local until authenticated accounts, durable permissions, object storage, billing, and live upload credentials exist.
- [x] Extend full pipeline, validation, operations reporting, and documentation to cover workspace job artifacts.

## Current Validation Gates

- [x] `npm run build`
- [x] `npm run validate`
- [x] `npm run full`
