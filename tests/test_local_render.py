import json
import tempfile
import unittest
from pathlib import Path

from viralfoundry.domain import LifecycleState, PolicyDecision, PolicyStatus, PostPlan
from viralfoundry.providers.local_generation import write_draft_packages
from viralfoundry.providers.local_render import render_draft_package, render_from_index
from viralfoundry.storage import list_render_attempts


class LocalRenderTests(unittest.TestCase):
    def test_missing_ffmpeg_writes_retryable_failure_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_path = write_draft_packages([_sample_plan()], root / "drafts")[0]
            db_path = root / "viral.db"

            result = render_draft_package(
                db_path=db_path,
                draft_path=draft_path,
                out_dir=root / "renders",
                ffmpeg_bin="ffmpeg-definitely-missing",
            )
            report = json.loads(Path(result.report_uri).read_text())
            attempts = list_render_attempts(db_path)

        self.assertEqual(result.status.value, "fail")
        self.assertEqual(result.output_uri, "")
        self.assertIn("Renderer binary not found", result.error_message)
        self.assertEqual(report["status"], "fail")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["publish_job_id"], "post-1")
        self.assertEqual(attempts[0]["status"], "fail")

    def test_render_from_index_honors_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_draft_packages([_sample_plan("post-1"), _sample_plan("post-2")], root / "drafts")

            results = render_from_index(
                db_path=root / "viral.db",
                index_path=root / "drafts" / "index.json",
                out_dir=root / "renders",
                limit=1,
                ffmpeg_bin="ffmpeg-definitely-missing",
            )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].publish_job_id, "post-1")


def _sample_plan(plan_id: str = "post-1") -> PostPlan:
    return PostPlan(
        id=plan_id,
        content_id=f"content-{plan_id}",
        platform="tiktok",
        scheduled_at="2026-05-23T10:00:00-06:00",
        niche_id="archive-317",
        title="The Archive at 3:17: Found File 1.1",
        hook="The first rule of this town is never answer a phone after midnight.",
        caption="The first rule of this town is never answer a phone after midnight. AI-assisted.",
        hashtags=["#fyp", "#storytime", "#shorts", "#originalaihorror"],
        duration_seconds=15,
        lifecycle_state=LifecycleState.NEEDS_OWNER_REVIEW,
        policy=PolicyDecision(
            status=PolicyStatus.PASS,
            owner_approval_required=False,
            ai_disclosure_required=True,
            findings=["No blocking policy findings."],
        ),
        render_spec={
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "caption_style": "compressed",
            "ai_label": True,
            "source_mode": "original_ip",
        },
    )


if __name__ == "__main__":
    unittest.main()
