import json
import tempfile
import unittest
from pathlib import Path

from viralfoundry.domain import LifecycleState, PolicyDecision, PolicyStatus, PostPlan
from viralfoundry.providers.local_generation import generate_draft_package, write_draft_packages


class LocalGenerationTests(unittest.TestCase):
    def test_generates_complete_draft_package(self):
        plan = _sample_plan()

        package = generate_draft_package(plan)

        self.assertEqual(package.post_plan_id, plan.id)
        self.assertEqual(package.lifecycle_state, LifecycleState.RENDER_READY)
        self.assertGreaterEqual(len(package.script.segments), 4)
        self.assertEqual(len(package.caption_variants), 3)
        self.assertTrue(all(item["caption"].lower().count("ai-assisted") == 1 for item in package.caption_variants))
        self.assertEqual(package.voice.provider, "local_voice_manifest")
        self.assertEqual(package.render_manifest.aspect_ratio, "9:16")
        self.assertIn(plan.policy.findings[0], package.policy.findings)
        self.assertTrue(any(asset.asset_type == "script" for asset in package.provenance))
        self.assertTrue(all(asset.checksum for asset in package.provenance))

    def test_writes_draft_packages_and_index(self):
        plan = _sample_plan()

        with tempfile.TemporaryDirectory() as tmp:
            paths = write_draft_packages([plan], Path(tmp))
            index = json.loads((Path(tmp) / "index.json").read_text())
            draft = json.loads(paths[0].read_text())

        self.assertEqual(len(paths), 1)
        self.assertEqual(index["draft_count"], 1)
        self.assertEqual(draft["post_plan_id"], plan.id)
        self.assertEqual(draft["policy"]["status"], "review")


def _sample_plan() -> PostPlan:
    return PostPlan(
        id="post-1",
        content_id="content-1",
        platform="youtube_shorts",
        scheduled_at="2026-05-23T10:00:00-06:00",
        niche_id="setup-under-budget",
        title="Setup Under Budget: Budget Comparison 1.1",
        hook="Here is the cheaper version nobody talks about.",
        caption="Here is the cheaper version nobody talks about. The last detail changes the whole story. AI-assisted.",
        hashtags=["#shorts", "#story", "#creator", "#affiliatedecisionhelp"],
        duration_seconds=45,
        lifecycle_state=LifecycleState.NEEDS_OWNER_REVIEW,
        policy=PolicyDecision(
            status=PolicyStatus.REVIEW,
            owner_approval_required=True,
            ai_disclosure_required=True,
            findings=["Owner review required by campaign settings."],
        ),
        render_spec={
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "caption_style": "compressed",
            "ai_label": True,
            "source_mode": "original_review_or_research",
        },
    )


if __name__ == "__main__":
    unittest.main()
