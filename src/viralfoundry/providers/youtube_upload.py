from __future__ import annotations

import json
import mimetypes
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from viralfoundry.domain import UploadResult, UploadStatus
from viralfoundry.storage import record_upload_result


YOUTUBE_UPLOAD_ENDPOINT = "https://www.googleapis.com/upload/youtube/v3/videos"
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
PROVIDER = "youtube_data_api_v3"


def upload_youtube_from_index(
    db_path: Path,
    index_path: Path,
    render_dir: Path,
    out_dir: Path,
    limit: Optional[int] = None,
    dry_run: bool = True,
    access_token: Optional[str] = None,
    owner_approved: bool = False,
    privacy_status: str = "private",
    category_id: str = "24",
) -> List[UploadResult]:
    data = json.loads(index_path.read_text())
    drafts = [Path(path) for path in data.get("drafts", [])]
    youtube_drafts = [path for path in drafts if _is_youtube_draft(path)]
    if limit is not None:
        youtube_drafts = youtube_drafts[:limit]
    return [
        upload_youtube_draft(
            db_path=db_path,
            draft_path=draft_path,
            render_dir=render_dir,
            out_dir=out_dir,
            dry_run=dry_run,
            access_token=access_token,
            owner_approved=owner_approved,
            privacy_status=privacy_status,
            category_id=category_id,
        )
        for draft_path in youtube_drafts
    ]


def upload_youtube_draft(
    db_path: Path,
    draft_path: Path,
    render_dir: Path,
    out_dir: Path,
    dry_run: bool = True,
    access_token: Optional[str] = None,
    owner_approved: bool = False,
    privacy_status: str = "private",
    category_id: str = "24",
) -> UploadResult:
    draft = json.loads(draft_path.read_text())
    publish_job_id = str(draft["post_plan_id"])
    package_dir = _render_package_dir(render_dir, draft)
    render_path = package_dir / "render.mp4"
    preflight_path = package_dir / "preflight.json"
    payload_path = _payload_path(out_dir, draft)
    metadata = build_youtube_metadata(draft, privacy_status=privacy_status, category_id=category_id)
    failure = _preflight_upload(draft, render_path, preflight_path, owner_approved)
    if failure:
        result = UploadResult(
            publish_job_id=publish_job_id,
            provider=PROVIDER,
            platform=str(draft["platform"]),
            video_uri="",
            payload_uri=str(_write_payload(payload_path, draft_path, draft, metadata, render_path, failure, dry_run)),
            status=UploadStatus.FAIL,
            error_message=failure,
        )
        _record(db_path, result)
        return result

    if dry_run:
        result = UploadResult(
            publish_job_id=publish_job_id,
            provider=PROVIDER,
            platform=str(draft["platform"]),
            video_uri="",
            payload_uri=str(_write_payload(payload_path, draft_path, draft, metadata, render_path, "", dry_run)),
            status=UploadStatus.DRY_RUN,
            error_message="",
        )
        _record(db_path, result)
        return result

    token = access_token or os.environ.get("YOUTUBE_ACCESS_TOKEN", "")
    if not token:
        result = UploadResult(
            publish_job_id=publish_job_id,
            provider=PROVIDER,
            platform=str(draft["platform"]),
            video_uri="",
            payload_uri=str(
                _write_payload(payload_path, draft_path, draft, metadata, render_path, "Missing YOUTUBE_ACCESS_TOKEN.", dry_run)
            ),
            status=UploadStatus.FAIL,
            error_message="Missing YOUTUBE_ACCESS_TOKEN with YouTube upload scope.",
        )
        _record(db_path, result)
        return result

    try:
        response = _resumable_upload(render_path, metadata, token)
        video_id = str(response.get("id", ""))
        video_uri = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""
        result = UploadResult(
            publish_job_id=publish_job_id,
            provider=PROVIDER,
            platform=str(draft["platform"]),
            video_uri=video_uri,
            payload_uri=str(_write_payload(payload_path, draft_path, draft, metadata, render_path, "", dry_run, response)),
            status=UploadStatus.SUCCESS,
            error_message="",
        )
    except YouTubeUploadError as exc:
        result = UploadResult(
            publish_job_id=publish_job_id,
            provider=PROVIDER,
            platform=str(draft["platform"]),
            video_uri="",
            payload_uri=str(_write_payload(payload_path, draft_path, draft, metadata, render_path, str(exc), dry_run)),
            status=UploadStatus.FAIL,
            error_message=str(exc),
        )
    _record(db_path, result)
    return result


def build_youtube_metadata(
    draft: Dict[str, Any],
    privacy_status: str = "private",
    category_id: str = "24",
) -> Dict[str, Any]:
    if privacy_status not in {"private", "unlisted", "public"}:
        raise ValueError("privacy_status must be private, unlisted, or public")
    caption = _primary_caption(draft)
    description = "\n".join(
        line
        for line in [
            caption,
            "",
            _script_summary(draft),
            "",
            "Disclosure: AI-assisted synthetic media." if draft["policy"].get("ai_disclosure_required") else "",
            "Source and rights provenance retained in the ViralFoundry draft package.",
        ]
        if line
    )
    return {
        "snippet": {
            "title": _shorten(str(draft["script"]["title"]), 100),
            "description": _shorten(description, 5000),
            "tags": _tags_for(draft),
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": bool(draft["policy"].get("ai_disclosure_required")),
            "embeddable": True,
            "license": "youtube",
        },
    }


def _is_youtube_draft(path: Path) -> bool:
    try:
        data = json.loads(path.read_text())
    except OSError:
        return False
    except json.JSONDecodeError:
        return False
    return data.get("platform") == "youtube_shorts"


def _render_package_dir(render_dir: Path, draft: Dict[str, Any]) -> Path:
    return render_dir / f"{draft['scheduled_at'][:10]}-{draft['platform']}-{draft['post_plan_id']}"


def _payload_path(out_dir: Path, draft: Dict[str, Any]) -> Path:
    return out_dir / f"{draft['scheduled_at'][:10]}-{draft['platform']}-{draft['post_plan_id']}.json"


def _preflight_upload(
    draft: Dict[str, Any],
    render_path: Path,
    preflight_path: Path,
    owner_approved: bool,
) -> str:
    if draft.get("platform") != "youtube_shorts":
        return "YouTube uploader only accepts youtube_shorts draft packages."
    policy = draft.get("policy", {})
    if policy.get("status") == "block":
        return "Policy blocked draft cannot be uploaded."
    if policy.get("owner_approval_required") and not owner_approved:
        return "Owner approval is required before upload. Re-run with --owner-approved after review."
    if not render_path.exists() or render_path.stat().st_size == 0:
        return f"Rendered MP4 missing or empty: {render_path}"
    if not preflight_path.exists():
        return f"Render preflight report missing: {preflight_path}"
    preflight = _load_preflight(preflight_path)
    if preflight.get("status") != "pass":
        return "Render preflight did not pass: " + "; ".join(preflight.get("findings", []))
    return ""


def _load_preflight(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {"status": "fail", "findings": ["Render preflight report is not valid JSON."]}


def _write_payload(
    path: Path,
    draft_path: Path,
    draft: Dict[str, Any],
    metadata: Dict[str, Any],
    render_path: Path,
    preflight_error: str,
    dry_run: bool,
    response: Optional[Dict[str, Any]] = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "provider": PROVIDER,
        "scope": YOUTUBE_UPLOAD_SCOPE,
        "endpoint": YOUTUBE_UPLOAD_ENDPOINT,
        "upload_type": "resumable",
        "dry_run": dry_run,
        "publish_job_id": draft["post_plan_id"],
        "draft_package_uri": str(draft_path),
        "render_uri": str(render_path),
        "metadata": metadata,
        "preflight_error": preflight_error,
        "response": response or {},
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def _resumable_upload(render_path: Path, metadata: Dict[str, Any], access_token: str) -> Dict[str, Any]:
    metadata_bytes = json.dumps(metadata, sort_keys=True).encode("utf-8")
    content_type = mimetypes.guess_type(str(render_path))[0] or "video/mp4"
    upload_size = render_path.stat().st_size
    query = urllib.parse.urlencode({"uploadType": "resumable", "part": "snippet,status"})
    request = urllib.request.Request(
        f"{YOUTUBE_UPLOAD_ENDPOINT}?{query}",
        data=metadata_bytes,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
            "Content-Length": str(len(metadata_bytes)),
            "X-Upload-Content-Length": str(upload_size),
            "X-Upload-Content-Type": content_type,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            upload_url = response.headers.get("Location")
    except urllib.error.HTTPError as exc:
        raise YouTubeUploadError(_http_error_message("Unable to start YouTube upload session", exc)) from exc
    except OSError as exc:
        raise YouTubeUploadError(f"Unable to start YouTube upload session: {exc}") from exc
    if not upload_url:
        raise YouTubeUploadError("YouTube upload session response did not include a Location header.")

    video_bytes = render_path.read_bytes()
    put_request = urllib.request.Request(
        upload_url,
        data=video_bytes,
        method="PUT",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Length": str(upload_size),
            "Content-Type": content_type,
        },
    )
    try:
        with urllib.request.urlopen(put_request, timeout=600) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        raise YouTubeUploadError(_http_error_message("YouTube upload failed", exc)) from exc
    except OSError as exc:
        raise YouTubeUploadError(f"YouTube upload failed: {exc}") from exc


def _http_error_message(prefix: str, exc: urllib.error.HTTPError) -> str:
    body = exc.read().decode("utf-8", errors="replace")
    return f"{prefix}: HTTP {exc.code} {body}".strip()


def _primary_caption(draft: Dict[str, Any]) -> str:
    variants = draft.get("caption_variants", [])
    if variants:
        return str(variants[0].get("caption", ""))
    return str(draft["script"]["hook"])


def _script_summary(draft: Dict[str, Any]) -> str:
    script = str(draft["script"].get("script_text", ""))
    return script.replace("\n", " ")[:1200]


def _tags_for(draft: Dict[str, Any]) -> List[str]:
    tags: List[str] = []
    for variant in draft.get("caption_variants", []):
        tags.extend(str(tag).lstrip("#") for tag in variant.get("hashtags", []))
    tags.extend([str(draft["niche_id"]), "shorts"])
    return list(dict.fromkeys(tag for tag in tags if tag))[:30]


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "."


def _record(db_path: Path, result: UploadResult) -> None:
    record_upload_result(
        db_path=db_path,
        publish_job_id=result.publish_job_id,
        provider=result.provider,
        platform=result.platform,
        video_uri=result.video_uri,
        payload_uri=result.payload_uri,
        status=result.status.value,
        error_message=result.error_message,
    )


class YouTubeUploadError(Exception):
    pass
