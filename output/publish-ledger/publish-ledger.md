# Publish Ledger

Mode: dry_run

## Entries

- why-local-rendering-changes-the-product-risk / YouTube Shorts: not_submitted, human_approval_required, post id pending
- why-local-rendering-changes-the-product-risk / TikTok: not_submitted, human_approval_required, post id pending
- why-local-rendering-changes-the-product-risk / LinkedIn: not_submitted, human_approval_required, post id pending
- the-minimum-useful-video-factory / YouTube Shorts: not_submitted, human_approval_required, post id pending
- the-minimum-useful-video-factory / Instagram Reels: not_submitted, human_approval_required, post id pending

## Live Publishing Requirements

- Load platform credentials from the runtime environment.
- Require human approval before the first upload attempt.
- Persist returned platform IDs and canonical URLs.
- Record retry attempts, retry timing, and terminal upload errors.
- Keep idempotency keys stable across retries.
