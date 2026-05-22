from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

from .domain import ContentIdea, LifecycleState, NicheConfig, PostPlan
from .guardrails import evaluate_idea


PLATFORM_SLOTS = {
    "tiktok": [9, 13, 18, 21],
    "instagram_reels": [11, 19],
    "youtube_shorts": [10, 16, 22],
}

PILLAR_FORMATS = {
    "original_ai_horror": [
        ("found file", "The first rule of this town is never answer a phone after midnight."),
        ("witness log", "The ending makes the first five seconds worse."),
        ("comment-led episode", "The comments picked door three, and that was the mistake."),
    ],
    "affiliate_decision_help": [
        ("budget comparison", "Here is the cheaper version nobody talks about."),
        ("problem-solution", "This fixes the most annoying part of a desk setup under $25."),
        ("worth-it test", "I would skip the popular one and buy this instead."),
    ],
    "mini_documentary": [
        ("internet history", "This vanished app left one clue behind."),
        ("lost media", "Everyone remembers the screenshot, but not where it came from."),
        ("timeline", "The weird part is not the rumor. It is the timestamp."),
    ],
    "fictional_moral_dilemmas": [
        ("verdict prompt", "The story sounds obvious until the final text message."),
        ("two-sided dilemma", "Reddit would blame the wrong person here."),
        ("comment verdict", "The comments changed my verdict on this one."),
    ],
    "authorized_streamer_commentary": [
        ("stakes-first clip", "If this play fails, the entire run is over."),
        ("mechanics breakdown", "The win happened two seconds before anyone noticed."),
        ("clip analysis", "This joke landed because the setup was hiding in chat."),
    ],
}

HASHTAGS = {
    "tiktok": ["#fyp", "#storytime", "#shorts"],
    "instagram_reels": ["#reels", "#explore", "#facelesscreator"],
    "youtube_shorts": ["#shorts", "#story", "#creator"],
}


def load_config(path: Path) -> Tuple[str, List[NicheConfig]]:
    data = json.loads(path.read_text())
    timezone_name = str(data.get("timezone", "America/Edmonton"))
    niches = [NicheConfig.from_dict(item) for item in data["niches"]]
    return timezone_name, niches


def plan_content(
    niches: Iterable[NicheConfig],
    days: int,
    timezone_name: str,
    start_at: Optional[datetime] = None,
) -> List[PostPlan]:
    tz = ZoneInfo(timezone_name)
    now = start_at.astimezone(tz) if start_at else datetime.now(tz)
    start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    plans: List[PostPlan] = []

    for day_offset in range(days):
        day = start_day + timedelta(days=day_offset)
        for niche in niches:
            for index in range(niche.daily_posts):
                idea = _make_idea(niche, day_offset, index)
                policy = evaluate_idea(idea)
                content_id = _stable_id("content", niche.id, str(day.date()), str(index), idea.title)

                for platform in niche.platforms:
                    scheduled_at = _slot_for(day, platform, index).isoformat()
                    post_id = _stable_id("post", content_id, platform, scheduled_at)
                    state = (
                        LifecycleState.NEEDS_OWNER_REVIEW
                        if policy.owner_approval_required or not niche.autonomous_publish
                        else LifecycleState.SCHEDULED
                    )
                    plans.append(
                        PostPlan(
                            id=post_id,
                            content_id=content_id,
                            platform=platform,
                            scheduled_at=scheduled_at,
                            niche_id=niche.id,
                            title=idea.title,
                            hook=idea.hook,
                            caption=_caption_for(idea, platform),
                            hashtags=_hashtags_for(platform, niche),
                            duration_seconds=niche.duration_seconds,
                            lifecycle_state=state,
                            policy=policy,
                            render_spec={
                                "aspect_ratio": "9:16",
                                "resolution": "1080x1920",
                                "caption_style": "compressed",
                                "ai_label": policy.ai_disclosure_required,
                                "source_mode": idea.source_mode,
                            },
                        )
                    )

    return sorted(plans, key=lambda item: item.scheduled_at)


def _make_idea(niche: NicheConfig, day_offset: int, index: int) -> ContentIdea:
    formats = PILLAR_FORMATS.get(niche.content_pillar, [("short", "This starts with a problem and ends with a choice.")])
    content_format, hook = formats[(day_offset + index) % len(formats)]
    hypothesis = niche.hypotheses[(day_offset + index) % len(niche.hypotheses)] if niche.hypotheses else "Test retention."
    title = f"{niche.name}: {content_format.title()} {day_offset + 1}.{index + 1}"
    return ContentIdea(
        id=_stable_id("idea", niche.id, str(day_offset), str(index), title),
        niche_id=niche.id,
        title=title,
        hook=hook,
        format=content_format,
        hypothesis=hypothesis,
        target_audience=_audience_for(niche),
        source_mode=niche.source_mode,
        risk_level=niche.risk_level,
        monetization_routes=niche.monetization_routes,
        uses_ai_generated_media=niche.uses_ai_generated_media,
        requires_source_permission=niche.requires_source_permission,
        permission_status="pending" if niche.requires_source_permission else None,
        citations_required=niche.source_mode in {"sourced_original_commentary", "original_review_or_research"},
    )


def _caption_for(idea: ContentIdea, platform: str) -> str:
    platform_hint = {
        "tiktok": "Watch to the end before you decide.",
        "instagram_reels": "Save this if the twist matters.",
        "youtube_shorts": "The last detail changes the whole story.",
    }.get(platform, "New test from ViralFoundry.")
    disclosure = " AI-assisted." if idea.uses_ai_generated_media else ""
    return f"{idea.hook} {platform_hint}{disclosure}"


def _hashtags_for(platform: str, niche: NicheConfig) -> List[str]:
    base = HASHTAGS.get(platform, ["#shorts"])
    pillar_tag = "#" + niche.content_pillar.replace("_", "")
    return list(dict.fromkeys(base + [pillar_tag]))


def _slot_for(day: datetime, platform: str, index: int) -> datetime:
    slots = PLATFORM_SLOTS.get(platform, [12])
    hour = slots[index % len(slots)]
    minute = (index * 17) % 60
    return day.replace(hour=hour, minute=minute)


def _audience_for(niche: NicheConfig) -> str:
    if niche.content_pillar == "affiliate_decision_help":
        return "buyers looking for quick, practical setup decisions"
    if niche.content_pillar == "original_ai_horror":
        return "horror viewers who binge serialized mystery content"
    if niche.content_pillar == "authorized_streamer_commentary":
        return "stream viewers who want context, stakes, and highlight analysis"
    return "short-form viewers who reward clear stakes and fast payoff"


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha1("::".join(parts).encode("utf-8")).hexdigest()
    return digest[:16]


def plans_to_json(plans: Iterable[PostPlan]) -> Dict[str, Any]:
    return {"plans": [plan.to_dict() for plan in plans]}
