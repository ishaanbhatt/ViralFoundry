from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from .analytics import rank_snapshots
from .domain import MetricSnapshot, PolicyStatus, PostPlan
from .planner import load_config, plan_content, plans_to_json
from .providers.dry_run import publish_dry_run
from .providers.local_generation import write_draft_packages
from .providers.local_render import render_from_index
from .storage import init_db, insert_metrics, insert_scores, latest_metric_snapshots, save_plans


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "niches.json"
DEFAULT_DB = PROJECT_ROOT / "var" / "viralfoundry.db"
DEFAULT_PLAN = PROJECT_ROOT / "var" / "outbox" / "plan.json"
DEFAULT_DRAFTS = PROJECT_ROOT / "var" / "drafts"
DEFAULT_RENDERS = PROJECT_ROOT / "var" / "renders"


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="viralfoundry")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db")

    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    plan_parser.add_argument("--days", type=int, default=7)
    plan_parser.add_argument("--out", type=Path, default=DEFAULT_PLAN)

    publish_parser = sub.add_parser("publish-dry-run")
    publish_parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    publish_parser.add_argument("--outbox", type=Path, default=PROJECT_ROOT / "var" / "outbox")

    draft_parser = sub.add_parser("draft")
    draft_parser.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    draft_parser.add_argument("--out", type=Path, default=DEFAULT_DRAFTS)
    draft_parser.add_argument("--limit", type=int)

    render_parser = sub.add_parser("render")
    render_parser.add_argument("--draft-index", type=Path, default=DEFAULT_DRAFTS / "index.json")
    render_parser.add_argument("--out", type=Path, default=DEFAULT_RENDERS)
    render_parser.add_argument("--limit", type=int)
    render_parser.add_argument("--ffmpeg-bin", default="ffmpeg")
    render_parser.add_argument("--ffprobe-bin", default="ffprobe")

    sub.add_parser("ingest-sample-metrics")
    sub.add_parser("rank")

    args = parser.parse_args(argv)

    if args.command == "init-db":
        init_db(args.db)
        print(f"Initialized database at {args.db}")
        return 0

    if args.command == "plan":
        timezone_name, niches = load_config(args.config)
        plans = plan_content(niches=niches, days=args.days, timezone_name=timezone_name)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(plans_to_json(plans), indent=2, sort_keys=True) + "\n")
        save_plans(args.db, plans)
        blocked = sum(1 for plan in plans if plan.policy.status == PolicyStatus.BLOCK)
        review = sum(1 for plan in plans if plan.policy.owner_approval_required)
        print(f"Wrote {len(plans)} planned publish jobs to {args.out}")
        print(f"Policy summary: {blocked} blocked, {review} requiring owner review")
        return 0

    if args.command == "publish-dry-run":
        plans = _load_plans(args.plan)
        written = publish_dry_run(args.db, plans, args.outbox)
        print(f"Wrote {len(written)} dry-run publish payloads to {args.outbox}")
        return 0

    if args.command == "draft":
        plans = _load_plans(args.plan)
        written = write_draft_packages(plans, args.out, args.limit)
        print(f"Wrote {len(written)} draft packages to {args.out}")
        if written:
            print(f"Index: {args.out / 'index.json'}")
        return 0

    if args.command == "render":
        results = render_from_index(
            db_path=args.db,
            index_path=args.draft_index,
            out_dir=args.out,
            limit=args.limit,
            ffmpeg_bin=args.ffmpeg_bin,
            ffprobe_bin=args.ffprobe_bin,
        )
        passed = sum(1 for result in results if result.status.value == "pass")
        failed = len(results) - passed
        print(f"Rendered {passed} packages to {args.out}; {failed} failed preflight")
        return 1 if failed else 0

    if args.command == "ingest-sample-metrics":
        plans = _load_plans(DEFAULT_PLAN) if DEFAULT_PLAN.exists() else []
        snapshots = _sample_metrics(plans)
        insert_metrics(args.db, snapshots)
        print(f"Inserted {len(snapshots)} sample metric snapshots")
        return 0

    if args.command == "rank":
        snapshots = latest_metric_snapshots(args.db)
        scores = rank_snapshots(snapshots)
        insert_scores(args.db, scores)
        for score in scores[:10]:
            print(f"{score.score:6.2f} {score.platform:16} {score.publish_job_id} {score.interpretation}")
        if not scores:
            print("No metrics found. Run ingest-sample-metrics after plan.")
        return 0

    parser.error("Unknown command")
    return 2


def _load_plans(path: Path) -> List[PostPlan]:
    from .domain import LifecycleState, PolicyDecision

    data = json.loads(path.read_text())
    plans = []
    for item in data["plans"]:
        policy = PolicyDecision(
            status=PolicyStatus(item["policy"]["status"]),
            owner_approval_required=bool(item["policy"]["owner_approval_required"]),
            ai_disclosure_required=bool(item["policy"]["ai_disclosure_required"]),
            findings=list(item["policy"]["findings"]),
        )
        plans.append(
            PostPlan(
                id=item["id"],
                content_id=item["content_id"],
                platform=item["platform"],
                scheduled_at=item["scheduled_at"],
                niche_id=item["niche_id"],
                title=item["title"],
                hook=item["hook"],
                caption=item["caption"],
                hashtags=list(item["hashtags"]),
                duration_seconds=int(item["duration_seconds"]),
                lifecycle_state=LifecycleState(item["lifecycle_state"]),
                policy=policy,
                render_spec=dict(item["render_spec"]),
            )
        )
    return plans


def _sample_metrics(plans: List[PostPlan]) -> List[MetricSnapshot]:
    snapshots = []
    now = datetime.now(timezone.utc).isoformat()
    for index, plan in enumerate(plans[:24]):
        multiplier = 1 + (index % 6)
        snapshots.append(
            MetricSnapshot(
                publish_job_id=plan.id,
                platform=plan.platform,
                captured_at=now,
                views=350 * multiplier,
                likes=18 * multiplier,
                comments=3 * multiplier,
                shares=2 * multiplier,
                saves=4 * multiplier,
                avg_view_duration_seconds=min(plan.duration_seconds, 12 + (multiplier * 6)),
                duration_seconds=plan.duration_seconds,
                followers_delta=multiplier - 1,
                revenue_cents=25 * multiplier if "affiliate" in plan.niche_id else 0,
                negative_feedback=1 if plan.policy.status == PolicyStatus.REVIEW and multiplier < 3 else 0,
            )
        )
    return snapshots


if __name__ == "__main__":
    raise SystemExit(main())
