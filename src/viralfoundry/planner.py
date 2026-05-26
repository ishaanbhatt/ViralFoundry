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
        (
            "found file",
            "The first rule of this town is never answer a phone after midnight.",
            "forbidden local rule",
            "serial lore that viewers can decode and comment on",
            88.0,
        ),
        (
            "witness log",
            "The ending makes the first five seconds worse.",
            "reverse-twist testimony",
            "a replayable clue structure built for retention",
            84.0,
        ),
        (
            "comment-led episode",
            "The comments picked door three, and that was the mistake.",
            "viewer-choice consequence",
            "audience participation that turns comments into next-episode fuel",
            91.0,
        ),
    ],
    "affiliate_decision_help": [
        (
            "budget comparison",
            "Here is the cheaper version nobody talks about.",
            "price-to-outcome comparison",
            "a fast buying shortcut for viewers who want a useful setup upgrade",
            90.0,
        ),
        (
            "problem-solution",
            "This fixes the most annoying part of a desk setup under $25.",
            "pain-point fix",
            "one specific annoyance solved with a low-risk product choice",
            94.0,
        ),
        (
            "worth-it test",
            "I would skip the popular one and buy this instead.",
            "popular-versus-practical verdict",
            "a confident recommendation viewers can save before buying",
            87.0,
        ),
    ],
    "mini_documentary": [
        (
            "internet history",
            "This vanished app left one clue behind.",
            "artifact-led mystery",
            "a sourced micro-story with a concrete thing to inspect",
            88.0,
        ),
        (
            "lost media",
            "Everyone remembers the screenshot, but not where it came from.",
            "collective-memory gap",
            "a save-worthy explanation of why a web artifact disappeared",
            86.0,
        ),
        (
            "timeline",
            "The weird part is not the rumor. It is the timestamp.",
            "chronology reveal",
            "a claim-by-claim timeline that rewards careful watching",
            92.0,
        ),
    ],
    "fictional_moral_dilemmas": [
        (
            "verdict prompt",
            "The story sounds obvious until the final text message.",
            "late evidence reveal",
            "an original dilemma engineered for a specific comment verdict",
            89.0,
        ),
        (
            "two-sided dilemma",
            "Reddit would blame the wrong person here.",
            "sympathy flip",
            "a balanced conflict that keeps viewers arguing without copied posts",
            84.0,
        ),
        (
            "comment verdict",
            "The comments changed my verdict on this one.",
            "audience appeal",
            "a direct prompt for replies, stitches, and follow-up episodes",
            91.0,
        ),
    ],
    "authorized_streamer_commentary": [
        (
            "stakes-first clip",
            "If this play fails, the entire run is over.",
            "context-before-clip",
            "clear stakes before the highlight so non-fans can follow",
            90.0,
        ),
        (
            "mechanics breakdown",
            "The win happened two seconds before anyone noticed.",
            "hidden-skill explanation",
            "analysis that makes the creator look sharper, not just reposted",
            88.0,
        ),
        (
            "clip analysis",
            "This joke landed because the setup was hiding in chat.",
            "chat-context payoff",
            "commentary that adds meaning to an authorized clip",
            82.0,
        ),
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
    niche_list = list(niches)
    ideas_by_niche_id = {
        niche.id: generate_content_ideas(niche, max(1, days * niche.daily_posts))
        for niche in niche_list
    }

    for day_offset in range(days):
        day = start_day + timedelta(days=day_offset)
        for niche in niche_list:
            ideas = ideas_by_niche_id[niche.id]
            for index in range(niche.daily_posts):
                idea = ideas[(day_offset * niche.daily_posts + index) % len(ideas)]
                policy = evaluate_idea(idea)
                content_id = _stable_id("content", niche.id, idea.id, str(day.date()))

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
                                "idea": {
                                    "id": idea.id,
                                    "rank": idea.rank,
                                    "score": idea.score,
                                    "format": idea.format,
                                    "angle": idea.angle,
                                    "target_audience": idea.target_audience,
                                    "value_proposition": idea.value_proposition,
                                    "platform_fit": idea.platform_fit,
                                    "hypothesis": idea.hypothesis,
                                    "scoring_reasons": idea.scoring_reasons,
                                },
                            },
                        )
                    )

    return sorted(plans, key=lambda item: item.scheduled_at)


def generate_content_ideas(niche: NicheConfig, count: int) -> List[ContentIdea]:
    if count <= 0:
        return []

    candidates = [_build_idea(niche, sequence) for sequence in range(max(count * 2, len(_formats_for(niche))))]
    ranked = sorted(candidates, key=lambda idea: (-idea.score, idea.title, idea.id))
    ideas = []
    for rank, idea in enumerate(ranked[:count], start=1):
        idea.rank = rank
        ideas.append(idea)
    return ideas


def _make_idea(niche: NicheConfig, day_offset: int, index: int) -> ContentIdea:
    return _build_idea(niche, day_offset + index)


def _build_idea(niche: NicheConfig, sequence: int) -> ContentIdea:
    formats = _formats_for(niche)
    content_format, hook, angle, value_proposition, base_score = formats[sequence % len(formats)]
    hypothesis = _hypothesis_for(niche, sequence)
    title = _title_for(niche, content_format, angle, sequence)
    platform_fit = _platform_fit_for(niche, content_format, angle)
    score, scoring_reasons = _score_idea(niche, content_format, angle, value_proposition, base_score, platform_fit)
    return ContentIdea(
        id=_stable_id("idea", niche.id, str(sequence), title),
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
        angle=angle,
        value_proposition=value_proposition,
        platform_fit=platform_fit,
        score=score,
        scoring_reasons=scoring_reasons,
        permission_status="pending" if niche.requires_source_permission else None,
        citations_required=niche.source_mode in {"sourced_original_commentary", "original_review_or_research"},
    )


def _formats_for(niche: NicheConfig) -> List[Tuple[str, str, str, str, float]]:
    return PILLAR_FORMATS.get(
        niche.content_pillar,
        [
            (
                "short",
                "This starts with a problem and ends with a choice.",
                "stakes-first explanation",
                "a compact idea with one clear promise and payoff",
                75.0,
            )
        ],
    )


def _hypothesis_for(niche: NicheConfig, sequence: int) -> str:
    if not niche.hypotheses:
        return "Test retention with a clear hook, payoff, and comment prompt."
    return niche.hypotheses[sequence % len(niche.hypotheses)]


def _title_for(niche: NicheConfig, content_format: str, angle: str, sequence: int) -> str:
    variant = sequence // max(1, len(_formats_for(niche))) + 1
    return f"{niche.name}: {angle.title()} ({content_format}, test {variant})"


def _platform_fit_for(niche: NicheConfig, content_format: str, angle: str) -> Dict[str, str]:
    fit_by_platform = {
        "tiktok": "strong hook and comment loop",
        "instagram_reels": "save/share value with concise payoff",
        "youtube_shorts": "searchable premise and retention-focused ending",
    }
    if niche.content_pillar == "affiliate_decision_help":
        fit_by_platform["instagram_reels"] = "saveable buyer shortcut"
        fit_by_platform["youtube_shorts"] = "clear problem-solution search intent"
    if niche.content_pillar == "authorized_streamer_commentary":
        fit_by_platform["tiktok"] = "stakes are clear before the clip"
    return {platform: f"{fit_by_platform.get(platform, 'short-form compatible')} via {angle}/{content_format}" for platform in niche.platforms}


def _score_idea(
    niche: NicheConfig,
    content_format: str,
    angle: str,
    value_proposition: str,
    base_score: float,
    platform_fit: Dict[str, str],
) -> Tuple[float, List[str]]:
    score = base_score
    reasons = [f"base {content_format} format score {base_score:.0f}"]

    if len(platform_fit) >= 3:
        score += 4.0
        reasons.append("works across all configured short-form platforms")
    elif platform_fit:
        score += 2.0
        reasons.append("fits configured platform mix")

    if niche.monetization_routes:
        score += min(6.0, 1.5 * len(niche.monetization_routes))
        reasons.append("connected to monetization routes")

    if niche.creative_rules:
        score += 2.0
        reasons.append("grounded in niche creative rules")

    if "comment" in angle or "comment" in value_proposition:
        score += 3.0
        reasons.append("invites measurable audience response")

    if "save" in value_proposition or "buy" in value_proposition:
        score += 3.0
        reasons.append("has save or purchase intent")

    if niche.requires_source_permission:
        score -= 8.0
        reasons.append("discounted until source permission is granted")

    if niche.risk_level == "high":
        score -= 5.0
        reasons.append("discounted for high-risk review burden")
    elif niche.risk_level == "low":
        score += 2.0
        reasons.append("low policy risk")

    return round(score, 2), reasons


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
