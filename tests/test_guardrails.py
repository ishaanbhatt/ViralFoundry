import unittest

from viralfoundry.domain import ContentIdea, PolicyStatus
from viralfoundry.guardrails import evaluate_idea


class GuardrailTests(unittest.TestCase):
    def test_blocks_unauthorized_clip(self):
        idea = ContentIdea(
            id="idea-1",
            niche_id="clips",
            title="Random streamer clip",
            hook="If this play fails, the run is over.",
            format="clip",
            hypothesis="Test clip retention.",
            target_audience="stream viewers",
            source_mode="unauthorized_clip",
            risk_level="high",
            monetization_routes=["creator rewards"],
            uses_ai_generated_media=False,
            requires_source_permission=True,
            permission_status=None,
        )

        decision = evaluate_idea(idea)

        self.assertEqual(decision.status, PolicyStatus.BLOCK)
        self.assertTrue(decision.owner_approval_required)

    def test_ai_original_content_requires_disclosure(self):
        idea = ContentIdea(
            id="idea-2",
            niche_id="archive-317",
            title="Original horror",
            hook="The first rule of this town is never answer a phone after midnight.",
            format="found file",
            hypothesis="Test serialized horror.",
            target_audience="horror viewers",
            source_mode="original_ip",
            risk_level="medium",
            monetization_routes=["patreon"],
            uses_ai_generated_media=True,
            requires_source_permission=False,
        )

        decision = evaluate_idea(idea)

        self.assertEqual(decision.status, PolicyStatus.PASS)
        self.assertTrue(decision.ai_disclosure_required)


if __name__ == "__main__":
    unittest.main()

