import { mkdir, rm } from "node:fs/promises";
import { fromRoot, readJson, writeJson, writeText } from "./lib/fs-utils.js";
import { markdownList } from "./lib/text.js";

function addDays(date, days) {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function isoDate(date) {
  return date.toISOString().slice(0, 10);
}

export async function generateOperations() {
  const brandKitIndex = await readJson(fromRoot("output", "brand-kits", "index.json"));
  const draftIndex = await readJson(fromRoot("drafts", "index.json"));
  const qualityIndex = await readJson(fromRoot("output", "quality", "index.json"));
  const providerIndex = await readJson(fromRoot("output", "provider-jobs", "index.json"));
  const publishIndex = await readJson(fromRoot("output", "publish", "index.json"));
  const publishLedger = await readJson(fromRoot("output", "publish-ledger", "index.json"));
  const approvalQueue = await readJson(fromRoot("output", "approvals", "index.json"));
  const workspaceIndex = await readJson(fromRoot("output", "workspace", "index.json"));
  await rm(fromRoot("output", "operations"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "operations"), { recursive: true });

  const start = new Date();
  const calendar = draftIndex.packages.map((item, index) => {
    const quality = qualityIndex.reports.find((report) => report.slug === item.slug);
    const workspaceJob = workspaceIndex.jobs.find((job) => job.slug === item.slug);
    const platforms = publishIndex.entries
      .filter((entry) => entry.slug === item.slug)
      .map((entry) => entry.platform);
    return {
      date: isoDate(addDays(start, index * 2)),
      slug: item.slug,
      title: item.title,
      platforms,
      qualityScore: quality.score,
      status: workspaceJob?.currentStatus || (quality.recommendation === "approved_for_publish_prep" ? "ready_for_final_voiceover" : "review_needed"),
      nextOperatorAction: workspaceJob?.nextOperatorAction || null,
      blockers: workspaceJob?.blockers || []
    };
  });

  const runReport = {
    generatedAt: new Date().toISOString(),
    summary: {
      drafts: draftIndex.count,
      brandKits: brandKitIndex.count,
      renderedVideos: draftIndex.count,
      averageQualityScore: qualityIndex.averageScore,
      providerJobs: providerIndex.count,
      providerMode: providerIndex.mode,
      publishPayloads: publishIndex.entries.length,
      publishLedgerEntries: publishLedger.count,
      approvalQueueItems: approvalQueue.count,
      workspaceJobs: workspaceIndex.counts.jobs,
      pendingApprovals: publishLedger.pendingApprovalCount,
      liveUploadReady: approvalQueue.liveUploadReadyCount,
      reviewBoard: "output/review/index.html",
      brandKitSummary: "output/brand-kits/brand-kit-summary.md",
      workspaceSummary: "output/workspace/workspace-summary.md"
    },
    calendar,
    risks: [
      "Brand kit artifacts are local registry entries until accounts, workspaces, and persistent brand-kit ownership exist.",
      "Workspace job artifacts are local dry-run records until a database, object storage, auth, and account-scoped permissions exist.",
      "Provider jobs are contract-only dry runs until credentials, polling, storage, and cost ledgers exist.",
      "Publishing remains dry-run until credentials and upload clients are implemented.",
      "Publish ledger entries require human approval before any future live upload attempt.",
      "Approval queue items are manual review tasks, not live upload permissions.",
      "Audio is a generated guide track until final voiceover is recorded or synthesized.",
      "Human review is still required before public distribution."
    ]
  };

  await writeJson(fromRoot("output", "operations", "run-report.json"), runReport);
  await writeText(
    fromRoot("output", "operations", "content-calendar.md"),
    `# Content Calendar\n\n${markdownList(calendar.map((entry) => `${entry.date}: ${entry.title} -> ${entry.platforms.join(", ")} (${entry.status}, ${entry.qualityScore}/100, blockers: ${entry.blockers.join(", ") || "none"})`))}\n`
  );
  return runReport;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const report = await generateOperations();
  console.log(`Generated operations report for ${report.summary.drafts} draft(s).`);
}
