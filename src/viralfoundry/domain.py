from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class LifecycleState(str, Enum):
    DRAFT_IDEA = "DRAFT_IDEA"
    SCRIPT_READY = "SCRIPT_READY"
    RENDER_READY = "RENDER_READY"
    NEEDS_OWNER_REVIEW = "NEEDS_OWNER_REVIEW"
    APPROVED_FOR_PUBLISH = "APPROVED_FOR_PUBLISH"
    SCHEDULED = "SCHEDULED"
    PUBLISHED = "PUBLISHED"
    METRICS_COLLECTING = "METRICS_COLLECTING"
    LEARNING_APPLIED = "LEARNING_APPLIED"
    BLOCKED_BY_POLICY = "BLOCKED_BY_POLICY"
    FAILED = "FAILED"


class PolicyStatus(str, Enum):
    PASS = "pass"
    REVIEW = "review"
    BLOCK = "block"


@dataclass
class NicheConfig:
    id: str
    name: str
    content_pillar: str
    source_mode: str
    risk_level: str
    daily_posts: int
    account_count: int
    duration_seconds: int
    platforms: List[str]
    uses_ai_generated_media: bool
    requires_source_permission: bool
    autonomous_publish: bool
    monetization_routes: List[str]
    hypotheses: List[str]
    creative_rules: List[str]
    blocked_topics: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NicheConfig":
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            content_pillar=str(data["content_pillar"]),
            source_mode=str(data["source_mode"]),
            risk_level=str(data["risk_level"]),
            daily_posts=int(data["daily_posts"]),
            account_count=int(data.get("account_count", 1)),
            duration_seconds=int(data["duration_seconds"]),
            platforms=list(data["platforms"]),
            uses_ai_generated_media=bool(data.get("uses_ai_generated_media", False)),
            requires_source_permission=bool(data.get("requires_source_permission", False)),
            autonomous_publish=bool(data.get("autonomous_publish", False)),
            monetization_routes=list(data.get("monetization_routes", [])),
            hypotheses=list(data.get("hypotheses", [])),
            creative_rules=list(data.get("creative_rules", [])),
            blocked_topics=list(data.get("blocked_topics", [])),
        )


@dataclass
class ContentIdea:
    id: str
    niche_id: str
    title: str
    hook: str
    format: str
    hypothesis: str
    target_audience: str
    source_mode: str
    risk_level: str
    monetization_routes: List[str]
    uses_ai_generated_media: bool
    requires_source_permission: bool
    permission_status: Optional[str] = None
    citations_required: bool = False
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PolicyDecision:
    status: PolicyStatus
    owner_approval_required: bool
    ai_disclosure_required: bool
    findings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class ScriptSegment:
    label: str
    start_second: int
    end_second: int
    narration: str
    on_screen_text: str
    visual_prompt: str


@dataclass
class ScriptDraft:
    provider: str
    model: str
    prompt: str
    title: str
    hook: str
    script_text: str
    segments: List[ScriptSegment]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class VoiceSpec:
    provider: str
    voice_name: str
    language: str
    pace: str
    estimated_seconds: int
    script_checksum: str


@dataclass
class AssetProvenance:
    asset_id: str
    asset_type: str
    source_type: str
    provider: str
    prompt_or_source: str
    license_status: str
    owner_permission_status: str
    ai_generated: bool
    checksum: str


@dataclass
class RenderManifest:
    provider: str
    platform: str
    aspect_ratio: str
    resolution: str
    duration_seconds: int
    fps: int
    caption_style: str
    safe_margin_percent: int
    timeline: List[Dict[str, Any]]
    required_assets: List[str]


@dataclass
class DraftPackage:
    id: str
    post_plan_id: str
    content_id: str
    niche_id: str
    platform: str
    scheduled_at: str
    lifecycle_state: LifecycleState
    script: ScriptDraft
    caption_variants: List[Dict[str, Any]]
    voice: VoiceSpec
    render_manifest: RenderManifest
    provenance: List[AssetProvenance]
    policy: PolicyDecision

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["lifecycle_state"] = self.lifecycle_state.value
        data["policy"] = self.policy.to_dict()
        return data


@dataclass
class PostPlan:
    id: str
    content_id: str
    platform: str
    scheduled_at: str
    niche_id: str
    title: str
    hook: str
    caption: str
    hashtags: List[str]
    duration_seconds: int
    lifecycle_state: LifecycleState
    policy: PolicyDecision
    render_spec: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["lifecycle_state"] = self.lifecycle_state.value
        data["policy"] = self.policy.to_dict()
        return data


@dataclass
class MetricSnapshot:
    publish_job_id: str
    platform: str
    captured_at: str
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    avg_view_duration_seconds: float
    duration_seconds: int
    followers_delta: int = 0
    revenue_cents: int = 0
    negative_feedback: int = 0


@dataclass
class PerformanceScore:
    publish_job_id: str
    platform: str
    score: float
    confidence: float
    interpretation: str
    features: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
