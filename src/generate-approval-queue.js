import { mkdir, rm } from "node:fs/promises";
import { fromRoot, readJson, writeJson, writeText } from "./lib/fs-utils.js";
import { markdownList } from "./lib/text.js";

function reviewChecklistFor(entry, payload) {
  const checklist = [
    "Watch the local MP4 in the review board.",
    "Confirm title, caption, and thumbnail match the target platform.",
    "Check for copyright, claims, brand-safety, and factual accuracy issues.",
    "Confirm final voiceover is ready before live publishing.",
    "Confirm platform credentials and account destination before upload."
  ];

  if (payload.readiness.blockers.length > 0) {
    checklist.push(`Resolve publish blockers: ${payload.readiness.blockers.join(", ")}.`);
  }

  if (entry.approval.blockers.length > 0) {
    checklist.push(`Clear approval blockers: ${entry.approval.blockers.join(", ")}.`);
  }

  return [...new Set(checklist)];
}

function priorityFor(qualityScore, blockerCount) {
  if (blockerCount > 2) return "blocked";
  if (qualityScore >= 95) return "ready_for_review";
  return "review_carefully";
}

function queueLine(item) {
  return `${item.slug} / ${item.platform}: ${item.status}, ${item.priority}, ${item.qualityScore}/100, blockers: ${item.blockers.join(", ")}`;
}

export async function generateApprovalQueue() {
  const draftIndex = await readJson(fromRoot("drafts", "index.json"));
  const qualityIndex = await readJson(fromRoot("output", "quality", "index.json"));
  const publishLedger = await readJson(fromRoot("output", "publish-ledger", "index.json"));
  await rm(fromRoot("output", "approvals"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "approvals"), { recursive: true });

  const items = [];
  for (const entry of publishLedger.entries) {
    const draft = draftIndex.packages.find((item) => item.slug === entry.slug);
    const quality = qualityIndex.reports.find((report) => report.slug === entry.slug);
    const payload = await readJson(fromRoot(entry.payloadPath));
    const blockers = [...new Set([...entry.approval.blockers, ...payload.readiness.blockers])];

    items.push({
      id: entry.id,
      slug: entry.slug,
      title: draft.title,
      platform: entry.platform,
      status: "awaiting_human_approval",
      priority: priorityFor(payload.readiness.qualityScore, blockers.length),
      qualityScore: payload.readiness.qualityScore,
      qualityRecommendation: quality.recommendation,
      packagePath: `drafts/${entry.slug}/package.json`,
      reviewBoardPath: "output/review/index.html",
      videoPath: payload.videoPath,
      thumbnailPath: payload.thumbnailPath,
      publishPayloadPath: entry.payloadPath,
      ledgerEntryId: entry.id,
      idempotencyKey: entry.idempotencyKey,
      requiredCredential: entry.requiredCredential,
      blockers,
      reviewChecklist: reviewChecklistFor(entry, payload),
      approvalState: {
        approved: false,
        approvedBy: null,
        approvedAt: null,
        approvalSource: "manual_review_required"
      },
      releaseDecision: {
        canProceedToLiveUpload: false,
        reason: "Dry-run approval queue only; live upload clients, credentials, and explicit human approval are not configured."
      }
    });
  }

  const queue = {
    generatedAt: new Date().toISOString(),
    mode: "dry_run",
    count: items.length,
    pendingReviewCount: items.filter((item) => item.status === "awaiting_human_approval").length,
    liveUploadReadyCount: items.filter((item) => item.releaseDecision.canProceedToLiveUpload).length,
    platforms: [...new Set(items.map((item) => item.platform))].sort(),
    items,
    nextApprovalSteps: [
      "Review every queued MP4, thumbnail, caption, and platform payload.",
      "Resolve final voiceover, credential, copyright, and brand-safety blockers.",
      "Record reviewer identity and timestamp in a persistent approval store before live upload exists.",
      "Keep live upload disabled until platform clients can consume approved queue items idempotently."
    ]
  };

  await writeJson(fromRoot("output", "approvals", "index.json"), queue);
  await writeText(
    fromRoot("output", "approvals", "approval-queue.md"),
    `# Approval Queue\n\nMode: ${queue.mode}\n\nLive-upload ready: ${queue.liveUploadReadyCount}/${queue.count}\n\n## Queue\n\n${markdownList(items.map(queueLine))}\n\n## Next Approval Steps\n\n${markdownList(queue.nextApprovalSteps)}\n`
  );
  return queue;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const queue = await generateApprovalQueue();
  console.log(`Generated ${queue.count} approval queue item${queue.count === 1 ? "" : "s"}.`);
}
