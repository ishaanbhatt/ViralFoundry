# The Minimum Useful Video Factory

## Voiceover

The Minimum Useful Video Factory. Define the smallest pipeline that creates reviewable drafts and playable videos.

Point 1. A draft package should include script, storyboard, captions, metadata, and QA notes.

Point 2. The render step should consume the package directly, not a separate hand-built file.

Point 3. Validation should check both content completeness and MP4 existence.

What this unlocks. When the MP4 is real, publishing is just the next integration layer.

## QA Checklist

- Script has a hook, supporting points, and close.
- Storyboard contains one or more timed scenes.
- Captions are present for each scene.
- Metadata includes platform targets.
- Design brief covers visual, motion, audio, caption, and platform decisions.
- Renderer can create a local MP4, thumbnail, and preview frame from this package.
