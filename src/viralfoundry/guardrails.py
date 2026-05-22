from __future__ import annotations

from .domain import ContentIdea, PolicyDecision, PolicyStatus


BLOCKED_SOURCE_MODES = {"unauthorized_clip", "scraped_repost", "unknown_license"}
HIGH_RISK_WORDS = {
    "guaranteed income",
    "cure",
    "diagnose",
    "election fraud",
    "underage",
    "dox",
    "leaked address",
}


def evaluate_idea(idea: ContentIdea) -> PolicyDecision:
    findings = []
    owner_review = False

    if idea.source_mode in BLOCKED_SOURCE_MODES:
        findings.append("Source mode is not monetization-safe or rights-safe.")

    if idea.requires_source_permission and idea.permission_status != "granted":
        findings.append("Source permission is required before this can publish publicly.")
        owner_review = True

    if idea.risk_level == "high":
        findings.append("High-risk niche requires owner approval before publishing.")
        owner_review = True

    text = " ".join([idea.title, idea.hook, idea.hypothesis]).lower()
    matched_risks = sorted(word for word in HIGH_RISK_WORDS if word in text)
    if matched_risks:
        findings.append("Sensitive or restricted claims detected: " + ", ".join(matched_risks))
        owner_review = True

    ai_disclosure_required = idea.uses_ai_generated_media

    if idea.source_mode in BLOCKED_SOURCE_MODES:
        return PolicyDecision(
            status=PolicyStatus.BLOCK,
            owner_approval_required=True,
            ai_disclosure_required=ai_disclosure_required,
            findings=findings,
        )

    if findings or owner_review:
        return PolicyDecision(
            status=PolicyStatus.REVIEW,
            owner_approval_required=True,
            ai_disclosure_required=ai_disclosure_required,
            findings=findings or ["Owner review required by campaign settings."],
        )

    return PolicyDecision(
        status=PolicyStatus.PASS,
        owner_approval_required=False,
        ai_disclosure_required=ai_disclosure_required,
        findings=["No blocking policy findings."],
    )

