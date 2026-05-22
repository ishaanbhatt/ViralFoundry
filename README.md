# Local Video Draft Machine

Phase 1 and Phase 2 are wired together here:

1. Generate complete draft packages from `content/briefs.json`.
2. Render real local MP4 files from those packages.
3. Generate thumbnails, preview frames, and a local review board for design QA.

Run the full pipeline:

```bash
npm install
npm run full
```

Outputs:

- Draft packages: `drafts/<slug>/`
- MP4 renders: `output/videos/<slug>.mp4`
- Thumbnails: `output/thumbnails/<slug>.png`
- Preview frames: `output/previews/<slug>.png`
- Render manifests: `output/manifests/<slug>.render.json`
- Local review board: `output/review/index.html`
- Quality reports: `output/quality/`
- Dry-run publish payloads: `output/publish/`
- Operations report and calendar: `output/operations/`

Validate generated packages and videos:

```bash
npm run validate
```

## Input Briefs

Edit `content/briefs.json` to add or change draft inputs. Each brief supports:

- `title`
- `audience`
- `objective`
- `takeaways`
- `tone`
- `platforms`
- `durationSeconds`

The generator is deterministic and local. It creates a usable package with script, storyboard, captions, metadata, asset manifest, QA checklist, and render plan. The renderer uses a project-local FFmpeg binary from npm, so it does not require a system FFmpeg install.

## Design Coverage

The design layer is defined in `content/design-system.json` and then copied into each draft package as concrete decisions. Generated packages include:

- `design-brief.json`
- `platform-variants.json`
- `shot-list.json`
- `motion-plan.json`
- `audio-plan.json`
- `captions.srt`
- `production-notes.md`

The renderer consumes package-level design fields such as theme, layout, motion cue, caption timing, and render destinations. `npm run validate` checks that every package has design, platform, motion, audio, caption, thumbnail, preview, manifest, and review-board coverage.

## Local Product Workflow

Use `npm run full` as the main product command. It runs:

1. Draft package generation
2. Local MP4 rendering
3. Design review board generation
4. Quality scoring
5. Dry-run publishing payload preparation
6. Operations report and content calendar generation
7. Validation

Individual commands are available when debugging a specific phase:

- `npm run generate`
- `npm run render`
- `npm run review`
- `npm run quality`
- `npm run publish:prepare`
- `npm run operations`
- `npm run validate`

## Quality And Approval

`output/quality/` contains one quality report per package plus `index.json`. The scoring checks creative completeness, timed storyboards, design coverage, platform variants, captions, rendered assets, and explicit publish blockers.

Current approval recommendation values:

- `approved_for_publish_prep`
- `needs_light_review`
- `revise_before_publish_prep`

## Publishing Preparation

Publishing is intentionally dry-run only. `output/publish/` contains platform-specific payloads with video paths, thumbnails, captions, quality status, and the integration contract future upload clients should satisfy.

The local machine does not post publicly yet. Remaining publish blockers are explicit:

- Final voiceover
- Brand pack
- Platform credentials
- Platform upload clients
- Publish ledger for returned platform IDs

## Operations

`output/operations/run-report.json` ties together draft count, rendered videos, quality score, publish payload count, and review-board location. `output/operations/content-calendar.md` gives a simple local posting schedule generated from the current package set.

## Product Roadmap

Use `progress.md` as the living checklist. Items are checked only after the corresponding artifact exists and validation covers it.

## Remaining Integration Frontier

The local product problem is now mostly solved: it can produce complete packages, real MP4s, review assets, quality gates, dry-run publish payloads, and operations artifacts. The next phases are integration work:

- Replace guide tones with final voiceover generation or recorded audio.
- Add credential-backed upload clients for YouTube, TikTok, Instagram, and LinkedIn.
- Add a publish ledger that records platform IDs, upload status, retries, and errors.
- Add human approval controls before live posting.
- Add brand asset ingestion for logos, product imagery, and reusable lower-thirds.
