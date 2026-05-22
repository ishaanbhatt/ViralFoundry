from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from viralfoundry.domain import PostPlan
from viralfoundry.storage import mark_dry_run_payload


def publish_dry_run(db_path: Path, plans: Iterable[PostPlan], outbox_dir: Path) -> List[Path]:
    outbox_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    for plan in plans:
        payload = {
            "provider": "dry_run",
            "publish_job_id": plan.id,
            "platform": plan.platform,
            "scheduled_at": plan.scheduled_at,
            "caption": plan.caption,
            "hashtags": plan.hashtags,
            "render_spec": plan.render_spec,
            "policy": plan.policy.to_dict(),
            "note": "This payload is intentionally not posted. Swap in an official provider adapter after OAuth/app review.",
        }
        path = outbox_dir / f"{plan.scheduled_at[:10]}-{plan.platform}-{plan.id}.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        mark_dry_run_payload(db_path, plan.id, str(path))
        written.append(path)
    return written

