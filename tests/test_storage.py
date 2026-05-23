import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from viralfoundry.storage import init_db, list_render_attempts, record_render_result


class StorageTests(unittest.TestCase):
    def test_init_db_creates_render_attempts_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "viral.db"

            init_db(db_path)
            attempts = list_render_attempts(db_path)

        self.assertEqual(attempts, [])

    def test_records_failed_render_result_for_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "viral.db"

            record_render_result(
                db_path=db_path,
                publish_job_id="job-1",
                draft_package_uri="var/outbox/drafts/job-1.json",
                output_uri="",
                report_uri="var/outbox/render-reports/job-1.json",
                status="failed",
                error_message="ffmpeg exited 1",
            )
            rows = list_render_attempts(db_path)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["publish_job_id"], "job-1")
        self.assertEqual(rows[0]["draft_package_uri"], "var/outbox/drafts/job-1.json")
        self.assertEqual(rows[0]["output_uri"], "")
        self.assertEqual(rows[0]["report_uri"], "var/outbox/render-reports/job-1.json")
        self.assertEqual(rows[0]["status"], "failed")
        self.assertEqual(rows[0]["error_message"], "ffmpeg exited 1")
        self.assertIsInstance(rows[0]["id"], int)
        datetime.fromisoformat(rows[0]["created_at"])

    def test_lists_render_attempts_in_insert_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "viral.db"

            record_render_result(
                db_path,
                publish_job_id="job-1",
                draft_package_uri="drafts/job-1.json",
                output_uri="renders/job-1.mp4",
                report_uri="reports/job-1.json",
                status="succeeded",
            )
            record_render_result(
                db_path,
                publish_job_id="job-2",
                draft_package_uri="drafts/job-2.json",
                output_uri="",
                report_uri="reports/job-2.json",
                status="failed",
                error_message="missing asset",
            )
            rows = list_render_attempts(db_path)

        self.assertEqual([row["publish_job_id"] for row in rows], ["job-1", "job-2"])
        self.assertEqual(rows[0]["error_message"], "")
        self.assertEqual(rows[1]["error_message"], "missing asset")


if __name__ == "__main__":
    unittest.main()
