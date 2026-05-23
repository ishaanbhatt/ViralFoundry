from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from .domain import MetricSnapshot, PerformanceScore, PostPlan


SCHEMA = """
CREATE TABLE IF NOT EXISTS content_items (
  id TEXT PRIMARY KEY,
  niche_id TEXT NOT NULL,
  title TEXT NOT NULL,
  hook TEXT NOT NULL,
  lifecycle_state TEXT NOT NULL,
  policy_status TEXT NOT NULL,
  owner_approval_required INTEGER NOT NULL,
  ai_disclosure_required INTEGER NOT NULL,
  policy_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publish_jobs (
  id TEXT PRIMARY KEY,
  content_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  scheduled_at TEXT NOT NULL,
  caption TEXT NOT NULL,
  hashtags_json TEXT NOT NULL,
  render_spec_json TEXT NOT NULL,
  state TEXT NOT NULL,
  dry_run_payload_uri TEXT
);

CREATE TABLE IF NOT EXISTS render_attempts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  publish_job_id TEXT NOT NULL,
  draft_package_uri TEXT NOT NULL,
  output_uri TEXT NOT NULL,
  report_uri TEXT NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS metric_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  publish_job_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  captured_at TEXT NOT NULL,
  views INTEGER NOT NULL,
  likes INTEGER NOT NULL,
  comments INTEGER NOT NULL,
  shares INTEGER NOT NULL,
  saves INTEGER NOT NULL,
  avg_view_duration_seconds REAL NOT NULL,
  duration_seconds INTEGER NOT NULL,
  followers_delta INTEGER NOT NULL,
  revenue_cents INTEGER NOT NULL,
  negative_feedback INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS performance_scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  publish_job_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  score REAL NOT NULL,
  confidence REAL NOT NULL,
  interpretation TEXT NOT NULL,
  features_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def save_plans(db_path: Path, plans: Iterable[PostPlan]) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        for plan in plans:
            conn.execute(
                """
                INSERT OR REPLACE INTO content_items (
                  id, niche_id, title, hook, lifecycle_state, policy_status,
                  owner_approval_required, ai_disclosure_required, policy_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan.content_id,
                    plan.niche_id,
                    plan.title,
                    plan.hook,
                    plan.lifecycle_state.value,
                    plan.policy.status.value,
                    int(plan.policy.owner_approval_required),
                    int(plan.policy.ai_disclosure_required),
                    json.dumps(plan.policy.to_dict(), sort_keys=True),
                ),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO publish_jobs (
                  id, content_id, platform, scheduled_at, caption, hashtags_json,
                  render_spec_json, state, dry_run_payload_uri
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, COALESCE(
                  (SELECT dry_run_payload_uri FROM publish_jobs WHERE id = ?),
                  NULL
                ))
                """,
                (
                    plan.id,
                    plan.content_id,
                    plan.platform,
                    plan.scheduled_at,
                    plan.caption,
                    json.dumps(plan.hashtags),
                    json.dumps(plan.render_spec, sort_keys=True),
                    plan.lifecycle_state.value,
                    plan.id,
                ),
            )
        conn.commit()


def list_publish_jobs(db_path: Path) -> List[sqlite3.Row]:
    init_db(db_path)
    with connect(db_path) as conn:
        return list(conn.execute("SELECT * FROM publish_jobs ORDER BY scheduled_at, platform"))


def mark_dry_run_payload(db_path: Path, publish_job_id: str, uri: str) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            "UPDATE publish_jobs SET dry_run_payload_uri = ? WHERE id = ?",
            (uri, publish_job_id),
        )
        conn.commit()


def record_render_result(
    db_path: Path,
    publish_job_id: str,
    draft_package_uri: str,
    output_uri: str,
    report_uri: str,
    status: str,
    error_message: str = "",
) -> None:
    init_db(db_path)
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO render_attempts (
              publish_job_id, draft_package_uri, output_uri, report_uri,
              status, error_message, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                publish_job_id,
                draft_package_uri,
                output_uri,
                report_uri,
                status,
                error_message,
                created_at,
            ),
        )
        conn.commit()


def list_render_attempts(db_path: Path) -> List[sqlite3.Row]:
    init_db(db_path)
    with connect(db_path) as conn:
        return list(conn.execute("SELECT * FROM render_attempts ORDER BY id"))


def insert_metrics(db_path: Path, snapshots: Iterable[MetricSnapshot]) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        for snap in snapshots:
            conn.execute(
                """
                INSERT INTO metric_snapshots (
                  publish_job_id, platform, captured_at, views, likes, comments,
                  shares, saves, avg_view_duration_seconds, duration_seconds,
                  followers_delta, revenue_cents, negative_feedback
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snap.publish_job_id,
                    snap.platform,
                    snap.captured_at,
                    snap.views,
                    snap.likes,
                    snap.comments,
                    snap.shares,
                    snap.saves,
                    snap.avg_view_duration_seconds,
                    snap.duration_seconds,
                    snap.followers_delta,
                    snap.revenue_cents,
                    snap.negative_feedback,
                ),
            )
        conn.commit()


def latest_metric_snapshots(db_path: Path) -> List[MetricSnapshot]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT m.*
            FROM metric_snapshots m
            INNER JOIN (
              SELECT publish_job_id, MAX(captured_at) AS captured_at
              FROM metric_snapshots
              GROUP BY publish_job_id
            ) latest
            ON latest.publish_job_id = m.publish_job_id
            AND latest.captured_at = m.captured_at
            ORDER BY m.views DESC
            """
        ).fetchall()
    return [
        MetricSnapshot(
            publish_job_id=row["publish_job_id"],
            platform=row["platform"],
            captured_at=row["captured_at"],
            views=row["views"],
            likes=row["likes"],
            comments=row["comments"],
            shares=row["shares"],
            saves=row["saves"],
            avg_view_duration_seconds=row["avg_view_duration_seconds"],
            duration_seconds=row["duration_seconds"],
            followers_delta=row["followers_delta"],
            revenue_cents=row["revenue_cents"],
            negative_feedback=row["negative_feedback"],
        )
        for row in rows
    ]


def insert_scores(db_path: Path, scores: Iterable[PerformanceScore]) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        for score in scores:
            conn.execute(
                """
                INSERT INTO performance_scores (
                  publish_job_id, platform, score, confidence,
                  interpretation, features_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    score.publish_job_id,
                    score.platform,
                    score.score,
                    score.confidence,
                    score.interpretation,
                    json.dumps(score.features, sort_keys=True),
                    score.created_at,
                ),
            )
        conn.commit()
