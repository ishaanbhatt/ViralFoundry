# Policy Guardrails

## Hard Rules

- Use official platform APIs only.
- Do not automate account creation.
- Do not use private APIs, browser cookies, or scraping to publish.
- Do not bypass rate limits or platform review requirements.
- Do not publish unauthorized streamer clips.
- Do not commercially reuse Reddit stories unless submitted, licensed, public-domain, or rewritten as original fiction.
- Do not use celebrity, creator, or private-person likenesses without permission.
- Do not use copyrighted music unless the platform flow or license allows it.
- Do not generate fake engagement.
- Do not hide synthetic-media or sponsor disclosures.

## Required Metadata

Every asset should eventually carry:

- Source type.
- Source URL or generation prompt.
- License status.
- Creator or owner permission status.
- AI-generated status.
- Sponsor or affiliate disclosure status.
- Music rights.
- Hash or checksum.
- Attribution.

## Publication States

Public publishing should require all of:

- Platform account connected through official OAuth or provider.
- Niche policy configured.
- Asset provenance complete.
- AI disclosure decided.
- Sponsor or affiliate disclosure decided.
- Account cadence under limits.
- Duplicate content check passed.
- Owner approval unless the account and niche are explicitly eligible for autonomy.

## Review Triggers

Require owner review for:

- High-risk niches.
- Streamer clips.
- Medical, financial, political, legal, or news claims.
- Content involving real private people.
- Any source that requires permission.
- Any post with missing provenance.
- Any platform error suggesting spam, copyright, or policy risk.

## Monetization Eligibility

Publishing success is not monetization eligibility.

The system should separately track:

- Publish eligibility.
- Creator rewards or partner program eligibility.
- Ad suitability.
- Brand-safety suitability.
- Affiliate compliance.
- Sponsor disclosure compliance.

## Autonomy Policy

Default mode is draft and review. Fully autonomous public posting should unlock only after:

- At least 30 successful reviewed posts for the account.
- No copyright or policy violations in the last 30 days.
- Metrics collection is working.
- Kill switch is tested.
- Account-specific cadence limits are configured.
- The content lane uses original or licensed assets.

