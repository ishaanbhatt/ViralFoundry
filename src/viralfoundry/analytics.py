from __future__ import annotations

from typing import Iterable, List

from .domain import MetricSnapshot, PerformanceScore


def score_snapshot(snapshot: MetricSnapshot, baseline_views: int = 1000, risk_penalty: float = 0.0) -> PerformanceScore:
    views = max(snapshot.views, 1)
    view_velocity = min(snapshot.views / max(baseline_views, 1), 3.0) * 25.0
    engagement_units = snapshot.likes + (2 * snapshot.comments) + (3 * snapshot.shares) + (4 * snapshot.saves)
    engagement_rate = min(engagement_units / views, 0.4) * 100.0
    completion = min(snapshot.avg_view_duration_seconds / max(snapshot.duration_seconds, 1), 1.25) * 30.0
    follower_lift = min(max(snapshot.followers_delta, 0), 50) * 1.5
    revenue = min(snapshot.revenue_cents / 100.0, 50.0)
    negative = min(snapshot.negative_feedback * 2.0, 40.0)

    score = round(view_velocity + engagement_rate + completion + follower_lift + revenue - negative - risk_penalty, 2)
    confidence = _confidence_for(snapshot)
    interpretation = _interpret(score, snapshot)
    features = {
        "view_velocity": round(view_velocity, 2),
        "engagement_rate_component": round(engagement_rate, 2),
        "completion_component": round(completion, 2),
        "follower_lift": round(follower_lift, 2),
        "revenue_component": round(revenue, 2),
        "negative_penalty": round(negative, 2),
        "risk_penalty": risk_penalty,
    }
    return PerformanceScore(
        publish_job_id=snapshot.publish_job_id,
        platform=snapshot.platform,
        score=score,
        confidence=confidence,
        interpretation=interpretation,
        features=features,
    )


def rank_snapshots(snapshots: Iterable[MetricSnapshot]) -> List[PerformanceScore]:
    return sorted((score_snapshot(snapshot) for snapshot in snapshots), key=lambda score: score.score, reverse=True)


def _confidence_for(snapshot: MetricSnapshot) -> float:
    if snapshot.views >= 10000:
        return 0.9
    if snapshot.views >= 3000:
        return 0.75
    if snapshot.views >= 1000:
        return 0.6
    if snapshot.views >= 250:
        return 0.4
    return 0.2


def _interpret(score: float, snapshot: MetricSnapshot) -> str:
    if score >= 95:
        return "Promote this pattern and generate follow-up variants."
    if score >= 65:
        return "Keep testing. The post has a useful signal but needs more variants."
    if snapshot.views < 250:
        return "Too little distribution for a strong conclusion."
    return "Suppress this exact packaging and test a sharper hook or different format."

