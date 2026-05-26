import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from viralfoundry.domain import NicheConfig
from viralfoundry.planner import generate_content_ideas, plan_content


class PlannerTests(unittest.TestCase):
    def _niche(self):
        return NicheConfig(
            id="setup-under-budget",
            name="Setup Under Budget",
            content_pillar="affiliate_decision_help",
            source_mode="original_review_or_research",
            risk_level="low",
            daily_posts=2,
            account_count=1,
            duration_seconds=45,
            platforms=["tiktok", "instagram_reels", "youtube_shorts"],
            uses_ai_generated_media=True,
            requires_source_permission=False,
            autonomous_publish=False,
            monetization_routes=["amazon affiliate"],
            hypotheses=["Buyer intent wins."],
            creative_rules=["Start with the result or problem solved."],
            blocked_topics=[],
        )

    def test_generates_platform_variants(self):
        niche = self._niche()

        plans = plan_content(
            [niche],
            days=1,
            timezone_name="America/Edmonton",
            start_at=datetime(2026, 5, 21, 9, tzinfo=ZoneInfo("America/Edmonton")),
        )

        self.assertEqual(len(plans), 6)
        self.assertEqual({plan.platform for plan in plans}, {"tiktok", "instagram_reels", "youtube_shorts"})
        self.assertTrue(all(plan.policy.ai_disclosure_required for plan in plans))

    def test_generates_ranked_inspectable_ideas(self):
        ideas = generate_content_ideas(self._niche(), count=3)

        self.assertEqual([idea.rank for idea in ideas], [1, 2, 3])
        self.assertEqual([idea.score for idea in ideas], sorted((idea.score for idea in ideas), reverse=True))
        self.assertTrue(all(idea.angle for idea in ideas))
        self.assertTrue(all(idea.value_proposition for idea in ideas))
        self.assertTrue(all(set(idea.platform_fit) == {"tiktok", "instagram_reels", "youtube_shorts"} for idea in ideas))
        self.assertIn("connected to monetization routes", ideas[0].scoring_reasons)

    def test_plan_carries_idea_metadata_for_downstream_generation(self):
        niche = self._niche()
        plans = plan_content(
            [niche],
            days=1,
            timezone_name="America/Edmonton",
            start_at=datetime(2026, 5, 21, 9, tzinfo=ZoneInfo("America/Edmonton")),
        )

        idea = plans[0].render_spec["idea"]
        self.assertIn("angle", idea)
        self.assertIn("value_proposition", idea)
        self.assertIn("platform_fit", idea)
        self.assertGreater(idea["score"], 0)
        self.assertEqual(idea["rank"], 1)

    def test_idea_generation_is_deterministic(self):
        first = [idea.to_dict() for idea in generate_content_ideas(self._niche(), count=4)]
        second = [idea.to_dict() for idea in generate_content_ideas(self._niche(), count=4)]

        for ideas in (first, second):
            for idea in ideas:
                idea.pop("created_at")

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
