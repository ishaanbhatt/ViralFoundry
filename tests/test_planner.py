import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from viralfoundry.domain import NicheConfig
from viralfoundry.planner import plan_content


class PlannerTests(unittest.TestCase):
    def test_generates_platform_variants(self):
        niche = NicheConfig(
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
            creative_rules=[],
            blocked_topics=[],
        )

        plans = plan_content(
            [niche],
            days=1,
            timezone_name="America/Edmonton",
            start_at=datetime(2026, 5, 21, 9, tzinfo=ZoneInfo("America/Edmonton")),
        )

        self.assertEqual(len(plans), 6)
        self.assertEqual({plan.platform for plan in plans}, {"tiktok", "instagram_reels", "youtube_shorts"})
        self.assertTrue(all(plan.policy.ai_disclosure_required for plan in plans))


if __name__ == "__main__":
    unittest.main()

