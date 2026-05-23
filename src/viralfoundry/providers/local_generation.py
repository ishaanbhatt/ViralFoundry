from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from viralfoundry.domain import (
    AssetProvenance,
    DraftPackage,
    LifecycleState,
    PostPlan,
    RenderManifest,
    ScriptDraft,
    ScriptSegment,
    VoiceSpec,
)


CAPTION_VARIANT_FRAMES = {
    "tiktok": [
        "Fast version: {caption}",
        "{hook} Comment before the reveal.",
        "{caption} Part two only if the test wins.",
    ],
    "instagram_reels": [
        "{caption}",
        "{hook} Save this for the final detail.",
        "{caption} Share it with someone who would notice the clue.",
    ],
    "youtube_shorts": [
        "{caption}",
        "{hook} The last beat is the point.",
        "{caption} Subscribe for the next test.",
    ],
}

VOICE_BY_PILLAR = {
    "original_ip": "low-lit narrator",
    "original_review_or_research": "clear buyer guide",
    "sourced_original_commentary": "documentary explainer",
    "submitted_or_original_story": "verdict host",
    "licensed_or_partnered_clip": "analyst host",
}


def generate_draft_package(plan: PostPlan) -> DraftPackage:
    script = _script_for(plan)
    checksum = _checksum(script.script_text)
    voice = VoiceSpec(
        provider="local_voice_manifest",
        voice_name=VOICE_BY_PILLAR.get(str(plan.render_spec.get("source_mode")), "neutral narrator"),
        language="en-US",
        pace="compressed",
        estimated_seconds=plan.duration_seconds,
        script_checksum=checksum,
    )
    render_manifest = _render_manifest_for(plan, script)
    provenance = _provenance_for(plan, script, checksum)
    return DraftPackage(
        id=f"draft-{plan.id}",
        post_plan_id=plan.id,
        content_id=plan.content_id,
        niche_id=plan.niche_id,
        platform=plan.platform,
        scheduled_at=plan.scheduled_at,
        lifecycle_state=LifecycleState.RENDER_READY,
        script=script,
        caption_variants=_caption_variants_for(plan),
        voice=voice,
        render_manifest=render_manifest,
        provenance=provenance,
        policy=plan.policy,
    )


def write_draft_packages(
    plans: Iterable[PostPlan],
    out_dir: Path,
    limit: Optional[int] = None,
) -> List[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    selected = list(plans)
    if limit is not None:
        selected = selected[:limit]

    for plan in selected:
        package = generate_draft_package(plan)
        package_dir = out_dir / f"{plan.scheduled_at[:10]}-{plan.platform}-{plan.id}"
        package_dir.mkdir(parents=True, exist_ok=True)
        path = package_dir / "draft.json"
        path.write_text(json.dumps(package.to_dict(), indent=2, sort_keys=True) + "\n")
        written.append(path)

    index = {
        "draft_count": len(written),
        "drafts": [str(path) for path in written],
    }
    (out_dir / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
    return written


def _script_for(plan: PostPlan) -> ScriptDraft:
    total = max(plan.duration_seconds, 15)
    segments = [
        ScriptSegment(
            label="hook",
            start_second=0,
            end_second=min(5, total),
            narration=plan.hook,
            on_screen_text=_shorten(plan.hook, 64),
            visual_prompt=f"9:16 opening frame for {plan.title}; high contrast, clear subject, no logos",
        ),
        ScriptSegment(
            label="context",
            start_second=min(5, total),
            end_second=max(min(total // 3, total), min(12, total)),
            narration=_context_line(plan),
            on_screen_text=_shorten(plan.title, 56),
            visual_prompt=f"Establish the setting for {plan.niche_id} with readable caption space",
        ),
        ScriptSegment(
            label="turn",
            start_second=max(min(total // 3, total), min(12, total)),
            end_second=max(min((total * 2) // 3, total), min(18, total)),
            narration=_turn_line(plan),
            on_screen_text="Watch the detail change the decision.",
            visual_prompt="Close-up detail shot with motion that supports the narration",
        ),
        ScriptSegment(
            label="payoff",
            start_second=max(min((total * 2) // 3, total), min(18, total)),
            end_second=total,
            narration=_payoff_line(plan),
            on_screen_text=_platform_cta(plan.platform),
            visual_prompt="Final frame with clean safe margins for burned-in captions",
        ),
    ]
    script_text = "\n".join(segment.narration for segment in segments if segment.narration)
    prompt = (
        f"Create a {plan.duration_seconds}-second {plan.platform} short for {plan.niche_id}. "
        f"Open with the supplied hook, preserve policy findings, and avoid unsupported claims."
    )
    return ScriptDraft(
        provider="local_script_provider",
        model="deterministic-template-v1",
        prompt=prompt,
        title=plan.title,
        hook=plan.hook,
        script_text=script_text,
        segments=segments,
    )


def _caption_variants_for(plan: PostPlan) -> List[Dict[str, Any]]:
    frames = CAPTION_VARIANT_FRAMES.get(plan.platform, ["{caption}", "{hook}", "{caption}"])
    disclosure = "AI-assisted draft." if plan.policy.ai_disclosure_required else ""
    variants = []
    for index, frame in enumerate(frames, start=1):
        caption = frame.format(caption=plan.caption, hook=plan.hook)
        if disclosure and "ai-assisted" not in caption.lower():
            caption = f"{caption} {disclosure}"
        variants.append(
            {
                "id": f"{plan.id}-caption-{index}",
                "caption": caption.strip(),
                "hashtags": plan.hashtags,
                "ai_disclosure_required": plan.policy.ai_disclosure_required,
                "owner_review_required": plan.policy.owner_approval_required,
            }
        )
    return variants


def _render_manifest_for(plan: PostPlan, script: ScriptDraft) -> RenderManifest:
    timeline = []
    for segment in script.segments:
        timeline.append(
            {
                "label": segment.label,
                "start_second": segment.start_second,
                "end_second": segment.end_second,
                "narration": segment.narration,
                "on_screen_text": segment.on_screen_text,
                "visual_asset_id": f"{plan.id}-{segment.label}-visual",
            }
        )
    return RenderManifest(
        provider="local_render_manifest",
        platform=plan.platform,
        aspect_ratio=str(plan.render_spec.get("aspect_ratio", "9:16")),
        resolution=str(plan.render_spec.get("resolution", "1080x1920")),
        duration_seconds=plan.duration_seconds,
        fps=30,
        caption_style=str(plan.render_spec.get("caption_style", "compressed")),
        safe_margin_percent=8,
        timeline=timeline,
        required_assets=[f"{plan.id}-script", f"{plan.id}-voice"]
        + [item["visual_asset_id"] for item in timeline],
    )


def _provenance_for(plan: PostPlan, script: ScriptDraft, checksum: str) -> List[AssetProvenance]:
    assets = [
        AssetProvenance(
            asset_id=f"{plan.id}-script",
            asset_type="script",
            source_type="generated_text",
            provider=script.provider,
            prompt_or_source=script.prompt,
            license_status="owned_generated_draft",
            owner_permission_status="not_required",
            ai_generated=plan.policy.ai_disclosure_required,
            checksum=checksum,
        ),
        AssetProvenance(
            asset_id=f"{plan.id}-voice",
            asset_type="voice_manifest",
            source_type="generation_instruction",
            provider="local_voice_manifest",
            prompt_or_source=script.script_text,
            license_status="manifest_only_not_rendered_audio",
            owner_permission_status="not_required",
            ai_generated=plan.policy.ai_disclosure_required,
            checksum=_checksum(script.script_text + "::voice"),
        ),
    ]
    for segment in script.segments:
        assets.append(
            AssetProvenance(
                asset_id=f"{plan.id}-{segment.label}-visual",
                asset_type="visual_prompt",
                source_type=str(plan.render_spec.get("source_mode", "generated_visual_prompt")),
                provider="local_render_manifest",
                prompt_or_source=segment.visual_prompt,
                license_status="prompt_only_pending_asset_generation",
                owner_permission_status="required" if plan.policy.owner_approval_required else "not_required",
                ai_generated=plan.policy.ai_disclosure_required,
                checksum=_checksum(segment.visual_prompt),
            )
        )
    return assets


def _context_line(plan: PostPlan) -> str:
    source_mode = str(plan.render_spec.get("source_mode", "original"))
    if source_mode == "original_review_or_research":
        return "The useful test is not what looks popular, it is what solves the problem for less money."
    if source_mode == "sourced_original_commentary":
        return "Start with the public timeline, then separate the fact from the version everyone repeats."
    if source_mode == "licensed_or_partnered_clip":
        return "The clip only works after the stakes are clear and the creator permission is verified."
    if source_mode == "submitted_or_original_story":
        return "The first version sounds simple, but the missing message changes who is responsible."
    return "This is an original episode, so the rule has to be simple enough to remember and strange enough to share."


def _turn_line(plan: PostPlan) -> str:
    if "setup" in plan.niche_id:
        return "Compare the hidden tradeoff before the price tag makes the choice feel obvious."
    if "archive" in plan.niche_id:
        return "The archive entry looks routine until the timestamp repeats in the wrong place."
    if "mysteries" in plan.niche_id:
        return "The clue is not the screenshot; it is the date attached to the first upload."
    if "clip" in plan.niche_id:
        return "Freeze the moment before the payoff and point out what the audience missed."
    return "Give both sides one fair reason before asking the viewer for a verdict."


def _payoff_line(plan: PostPlan) -> str:
    if plan.policy.owner_approval_required:
        return "Before this goes public, review the rights, disclosure, and claim risk flagged in the package."
    return "End with the decision, then leave one specific reason for the viewer to answer in comments."


def _platform_cta(platform: str) -> str:
    return {
        "tiktok": "Comment your read before part two.",
        "instagram_reels": "Save this before the clue disappears.",
        "youtube_shorts": "Subscribe for the next test.",
    }.get(platform, "Follow for the next test.")


def _shorten(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "."


def _checksum(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()
