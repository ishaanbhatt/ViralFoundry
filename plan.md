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

Continue the local product roadmap in `progress.md`, then add provider abstraction after Phase 3 quality and approval gates are in place. The next integration phase should start with one provider adapter and a dry-run provider contract before adding paid API calls.
