import json
import tempfile
import unittest
from pathlib import Path

from viralfoundry.domain import LifecycleState, PolicyDecision, PolicyStatus, PostPlan
from viralfoundry.providers.local_generation import write_draft_packages
from viralfoundry.providers.youtube_upload import build_youtube_metadata, upload_youtube_from_index
from viralfoundry.storage import list_upload_attempts


class YouTubeUploadTests(unittest.TestCase):
    def test_dry_run_writes_official_upload_payload_after_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_path = write_draft_packages([_sample_plan(owner_review=False)], root / "drafts")[0]
            draft = json.loads(draft_path.read_text())
            _write_render_artifacts(root / "renders", draft)

            results = upload_youtube_from_index(
                db_path=root / "viral.db",
                index_path=root / "drafts" / "index.json",
                render_dir=root / "renders",
                out_dir=root / "uploads" / "youtube",
                dry_run=True,
            )
            payload = json.loads(Path(results[0].payload_uri).read_text())
            attempts = list_upload_attempts(root / "viral.db")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status.value, "dry_run")
        self.assertEqual(payload["endpoint"], "https://www.googleapis.com/upload/youtube/v3/videos")
        self.assertEqual(payload["upload_type"], "resumable")
        self.assertTrue(payload["metadata"]["status"]["containsSyntheticMedia"])
        self.assertEqual(payload["metadata"]["status"]["privacyStatus"], "private")
        self.assertEqual(attempts[0]["status"], "dry_run")
        self.assertEqual(attempts[0]["provider"], "youtube_data_api_v3")

    def test_owner_review_required_blocks_upload_until_flagged_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            draft_path = write_draft_packages([_sample_plan(owner_review=True)], root / "drafts")[0]
            draft = json.loads(draft_path.read_text())
            _write_render_artifacts(root / "renders", draft)

            results = upload_youtube_from_index(
                db_path=root / "viral.db",
                index_path=root / "drafts" / "index.json",
                render_dir=root / "renders",
                out_dir=root / "uploads" / "youtube",
                dry_run=True,
            )

        self.assertEqual(results[0].status.value, "fail")
        self.assertIn("Owner approval is required", results[0].error_message)

    def test_metadata_uses_youtube_synthetic_media_status_field(self):
        draft = {
            "niche_id": "archive-317",
            "script": {"title": "Archive 317", "hook": "The phone rang twice.", "script_text": "A short script."},
            "caption_variants": [{"caption": "AI-assisted story.", "hashtags": ["#shorts", "#horror"]}],
            "policy": {"ai_disclosure_required": True},
        }

        metadata = build_youtube_metadata(draft)

        self.assertEqual(metadata["status"]["containsSyntheticMedia"], True)
        self.assertEqual(metadata["status"]["selfDeclaredMadeForKids"], False)
        self.assertIn("shorts", metadata["snippet"]["tags"])


def _sample_plan(owner_review: bool) -> PostPlan:
    return PostPlan(
        id="post-youtube-1",
        content_id="content-youtube-1",
        platform="youtube_shorts",
        scheduled_at="2026-05-23T10:00:00-06:00",
        niche_id="archive-317",
        title="Archive 317: Found File 1.1",
        hook="The phone rang twice after the power went out.",
        caption="The phone rang twice after the power went out. AI-assisted.",
        hashtags=["#shorts", "#story", "#originalaihorror"],
        duration_seconds=15,
        lifecycle_state=LifecycleState.NEEDS_OWNER_REVIEW if owner_review else LifecycleState.RENDER_READY,
        policy=PolicyDecision(
            status=PolicyStatus.REVIEW if owner_review else PolicyStatus.PASS,
            owner_approval_required=owner_review,
            ai_disclosure_required=True,
            findings=["Owner review required."] if owner_review else ["No blocking policy findings."],
        ),
        render_spec={
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "caption_style": "compressed",
            "ai_label": True,
            "source_mode": "original_ip",
        },
    )


def _write_render_artifacts(render_dir: Path, draft: dict) -> None:
    package_dir = render_dir / f"{draft['scheduled_at'][:10]}-{draft['platform']}-{draft['post_plan_id']}"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "render.mp4").write_bytes(b"not-a-real-mp4-but-non-empty")
    (package_dir / "preflight.json").write_text(
        json.dumps({"status": "pass", "findings": ["Rendered MP4 passed local preflight checks."]}) + "\n"
    )


if __name__ == "__main__":
    unittest.main()
