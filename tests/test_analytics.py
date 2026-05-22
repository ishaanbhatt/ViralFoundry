import unittest

from viralfoundry.analytics import score_snapshot
from viralfoundry.domain import MetricSnapshot


class AnalyticsTests(unittest.TestCase):
    def test_scores_high_engagement_above_low_distribution(self):
        high = MetricSnapshot(
            publish_job_id="high",
            platform="tiktok",
            captured_at="2026-05-21T00:00:00Z",
            views=5000,
            likes=600,
            comments=50,
            shares=40,
            saves=80,
            avg_view_duration_seconds=40,
            duration_seconds=60,
            followers_delta=20,
            revenue_cents=1200,
        )
        low = MetricSnapshot(
            publish_job_id="low",
            platform="tiktok",
            captured_at="2026-05-21T00:00:00Z",
            views=200,
            likes=8,
            comments=0,
            shares=0,
            saves=1,
            avg_view_duration_seconds=8,
            duration_seconds=60,
            followers_delta=0,
            revenue_cents=0,
        )

        self.assertGreater(score_snapshot(high).score, score_snapshot(low).score)


if __name__ == "__main__":
    unittest.main()

