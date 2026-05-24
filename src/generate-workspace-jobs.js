import { mkdir, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { fromRoot, readJson, writeJson, writeText } from "./lib/fs-utils.js";
import { markdownList } from "./lib/text.js";

function requireUnique(values, label) {
  const seen = new Set();
  const duplicates = new Set();
  for (const value of values) {
    if (seen.has(value)) duplicates.add(value);
    seen.add(value);
  }
  if (duplicates.size > 0) {
    throw new Error(`${label} must be unique. Duplicate value(s): ${[...duplicates].join(", ")}`);
  }
}

function groupBySlug(items) {
  return items.reduce((groups, item) => {
    if (!groups.has(item.slug)) groups.set(item.slug, []);
    groups.get(item.slug).push(item);
    return groups;
  }, new Map());
}

function requireDefaultBrandKit(workspace, brandKitIndex) {
  if (!workspace.defaultBrandKitSlug) {
    throw new Error("content/workspace.json must define defaultBrandKitSlug.");
  }

  const matches = brandKitIndex.entries.filter((entry) => entry.slug === workspace.defaultBrandKitSlug);
  if (matches.length !== 1) {
    throw new Error(
      `Default brand kit '${workspace.defaultBrandKitSlug}' must resolve to exactly one generated brand kit; found ${matches.length}.`
    );
  }
  return matches[0];
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function collectBlockers({ publishPayloads, ledgerEntries, approvalItems }) {
  return unique([
    ...publishPayloads.flatMap((payload) => payload.readiness?.blockers || []),
    ...ledgerEntries.flatMap((entry) => entry.approval?.blockers || []),
    ...approvalItems.flatMap((item) => item.blockers || [])
  ]);
}

function deriveCurrentStatus({ quality, providerJob, publishPayloads, ledgerEntries, approvalItems, blockers }) {
  if (approvalItems.some((item) => item.releaseDecision?.canProceedToLiveUpload === true)) {
    return "approved_for_live_upload";
  }
  if (approvalItems.some((item) => item.status === "awaiting_human_approval")) {
    return "awaiting_human_approval";
  }
  if (blockers.length > 0) {
    return "blocked";
  }
  if (quality?.recommendation !== "approved_for_publish_prep") {
    return "quality_review_needed";
  }
  if (providerJob?.response?.status !== "contract_ready") {
    return "provider_contract_needed";
  }
  if (publishPayloads.some((payload) => payload.readiness?.status !== "asset_ready_credentials_needed")) {
    return "publish_payload_review_needed";
  }
  if (ledgerEntries.some((entry) => entry.upload?.status !== "not_submitted")) {
    return "ledger_review_needed";
  }
  return "ready_for_operator_review";
}

function deriveNextAction({ blockers, approvalItems }) {
  if (blockers.includes("human_approval")) {
    return "Review the local MP4, thumbnail, captions, and platform payloads, then record explicit human approval.";
  }
  if (blockers.includes("final_voiceover")) {
    return "Replace the guide audio with final voiceover before any live publishing attempt.";
  }
  if (blockers.includes("brand_pack")) {
    return "Attach or confirm the final brand pack for this workspace before publication.";
  }
  if (blockers.includes("platform_credentials")) {
    return "Configure the required platform credentials and verify the destination account.";
  }
  if (approvalItems.length > 0) {
    return "Confirm approval queue state and keep live upload disabled until the release decision is true.";
  }
  return "Review the job bundle and decide whether to move it into the next integration phase.";
}

function summaryLine(job) {
  return `${job.slug}: ${job.currentStatus}, ${job.quality.score}/100, blockers: ${job.operator.blockers.join(", ") || "none"}, next: ${job.operator.nextAction}`;
}

function localAssetPath(value) {
  if (!value) return null;
  if (!path.isAbsolute(value)) return value;
  return path.relative(fromRoot(), value);
}

function buildJob({
  workspace,
  draft,
  draftPackage,
  manifest,
  quality,
  providerSummary,
  providerJob,
  publishPayloads,
  publishIndexEntries,
  ledgerEntries,
  approvalItems,
  operationsEntry,
  brandKitEntry
}) {
  const blockers = collectBlockers({ publishPayloads, ledgerEntries, approvalItems });
  const currentStatus = deriveCurrentStatus({
    quality,
    providerJob,
    publishPayloads,
    ledgerEntries,
    approvalItems,
    blockers
  });

  return {
    generatedAt: new Date().toISOString(),
    id: `${workspace.id}:${draft.slug}`,
    slug: draft.slug,
    title: draft.title,
    workspace: {
      id: workspace.id,
      name: workspace.name,
      plan: workspace.plan,
      owner: workspace.owner
    },
    brandKit: {
      slug: brandKitEntry.slug,
      name: brandKitEntry.name,
      artifactPath: brandKitEntry.artifactPath
    },
    currentStatus,
    statusSignals: {
      qualityRecommendation: quality.recommendation,
      providerStatus: providerJob.response?.status || providerSummary?.status || "unknown",
      providerSubmitted: providerJob.response?.submitted === true,
      publishStatuses: unique(publishPayloads.map((payload) => payload.readiness?.status)),
      ledgerUploadStatuses: unique(ledgerEntries.map((entry) => entry.upload?.status)),
      approvalStatuses: unique(approvalItems.map((item) => item.status))
    },
    package: {
      title: draftPackage.creativeBrief.title,
      objective: draftPackage.creativeBrief.objective,
      durationSeconds: draftPackage.creativeBrief.durationSeconds,
      platforms: draftPackage.creativeBrief.platforms
    },
    paths: {
      packagePath: `drafts/${draft.slug}/package.json`,
      videoPath: localAssetPath(draft.renderOutput || manifest.outputPath),
      thumbnailPath: localAssetPath(manifest.thumbnailPath || quality.reviewedAssets?.thumbnail),
      previewFramePath: localAssetPath(manifest.previewFramePath || quality.reviewedAssets?.previewFrame),
      manifestPath: `output/manifests/${draft.slug}.render.json`,
      qualityReportPath: `output/quality/${draft.slug}.quality.json`,
      providerJobPath: providerSummary?.jobPath || `output/provider-jobs/${draft.slug}.provider-job.json`,
      publishPayloadPaths: publishIndexEntries.map((entry) => entry.payload),
      reviewBoardPath: approvalItems[0]?.reviewBoardPath || "output/review/index.html"
    },
    quality: {
      score: quality.score,
      recommendation: quality.recommendation,
      reportPath: `output/quality/${draft.slug}.quality.json`
    },
    providerJob: {
      provider: providerJob.provider,
      status: providerJob.response?.status || providerSummary?.status || "unknown",
      submitted: providerJob.response?.submitted === true,
      billable: providerJob.response?.billable === true,
      cost: providerJob.response?.cost || providerSummary?.cost || null,
      path: providerSummary?.jobPath || `output/provider-jobs/${draft.slug}.provider-job.json`
    },
    publishing: {
      payloads: publishPayloads.map((payload, index) => ({
        platform: payload.platform,
        status: payload.readiness?.status || "unknown",
        path: publishIndexEntries[index]?.payload || null,
        idempotencyKey: payload.integrationContract?.idempotencyKey || null,
        requiredCredential: payload.integrationContract?.requiredCredential || null,
        blockers: payload.readiness?.blockers || []
      })),
      ledgerIds: ledgerEntries.map((entry) => entry.id),
      ledgerEntries: ledgerEntries.map((entry) => ({
        id: entry.id,
        platform: entry.platform,
        uploadStatus: entry.upload?.status || "unknown",
        approvalStatus: entry.approval?.status || "unknown",
        payloadPath: entry.payloadPath,
        requiredCredential: entry.requiredCredential
      })),
      approvalItemIds: approvalItems.map((item) => item.id),
      approvalItems: approvalItems.map((item) => ({
        id: item.id,
        platform: item.platform,
        status: item.status,
        priority: item.priority,
        canProceedToLiveUpload: item.releaseDecision?.canProceedToLiveUpload === true
      }))
    },
    operations: operationsEntry || null,
    operator: {
      blockers,
      nextAction: deriveNextAction({ blockers, approvalItems }),
      reviewChecklist: unique(approvalItems.flatMap((item) => item.reviewChecklist || []))
    },
    provenance: {
      mode: "local_dry_run",
      externalCalls: false,
      sources: [
        "content/workspace.json",
        "drafts/index.json",
        "output/brand-kits/index.json",
        "output/quality/index.json",
        "output/provider-jobs/index.json",
        "output/publish/index.json",
        "output/publish-ledger/index.json",
        "output/approvals/index.json"
      ]
    }
  };
}

export async function generateWorkspaceJobs() {
  const workspace = await readJson(fromRoot("content", "workspace.json"));
  const draftIndex = await readJson(fromRoot("drafts", "index.json"));
  const brandKitIndex = await readJson(fromRoot("output", "brand-kits", "index.json"));
  const qualityIndex = await readJson(fromRoot("output", "quality", "index.json"));
  const providerIndex = await readJson(fromRoot("output", "provider-jobs", "index.json"));
  const publishIndex = await readJson(fromRoot("output", "publish", "index.json"));
  const publishLedger = await readJson(fromRoot("output", "publish-ledger", "index.json"));
  const approvalQueue = await readJson(fromRoot("output", "approvals", "index.json"));

  requireUnique(draftIndex.packages.map((item) => item.slug), "Draft package slugs");
  const brandKitEntry = requireDefaultBrandKit(workspace, brandKitIndex);
  await readJson(fromRoot(brandKitEntry.artifactPath));

  const publishBySlug = groupBySlug(publishIndex.entries);
  const ledgerBySlug = groupBySlug(publishLedger.entries);
  const approvalsBySlug = groupBySlug(approvalQueue.items);

  await rm(fromRoot("output", "workspace"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "workspace", "jobs"), { recursive: true });

  const jobs = [];
  for (const draft of draftIndex.packages) {
    const draftPackage = await readJson(fromRoot("drafts", draft.slug, "package.json"));
    const manifest = await readJson(fromRoot("output", "manifests", `${draft.slug}.render.json`));
    const quality = await readJson(fromRoot("output", "quality", `${draft.slug}.quality.json`));
    const providerSummary = providerIndex.entries.find((entry) => entry.slug === draft.slug);
    const providerJobPath = providerSummary?.jobPath || `output/provider-jobs/${draft.slug}.provider-job.json`;
    const providerJob = await readJson(fromRoot(providerJobPath));
    const publishIndexEntries = publishBySlug.get(draft.slug) || [];
    const publishPayloads = [];
    for (const entry of publishIndexEntries) {
      publishPayloads.push(await readJson(fromRoot(entry.payload)));
    }

    const job = buildJob({
      workspace,
      draft,
      draftPackage,
      manifest,
      quality,
      providerSummary,
      providerJob,
      publishPayloads,
      publishIndexEntries,
      ledgerEntries: ledgerBySlug.get(draft.slug) || [],
      approvalItems: approvalsBySlug.get(draft.slug) || [],
      operationsEntry: null,
      brandKitEntry
    });

    jobs.push(job);
    await writeJson(fromRoot("output", "workspace", "jobs", `${draft.slug}.job.json`), job);
  }

  const index = {
    generatedAt: new Date().toISOString(),
    mode: workspace.plan.mode,
    workspace: {
      id: workspace.id,
      name: workspace.name,
      owner: workspace.owner,
      defaultBrandKitSlug: workspace.defaultBrandKitSlug,
      defaultBrandKitPath: brandKitEntry.artifactPath,
      plan: workspace.plan,
      permissions: workspace.permissions,
      entitlements: workspace.entitlements
    },
    counts: {
      jobs: jobs.length,
      publishPayloads: publishIndex.entries.length,
      ledgerEntries: publishLedger.count,
      approvalItems: approvalQueue.count,
      blockedJobs: jobs.filter((job) => job.operator.blockers.length > 0).length
    },
    jobs: jobs.map((job) => ({
      slug: job.slug,
      title: job.title,
      currentStatus: job.currentStatus,
      qualityScore: job.quality.score,
      jobPath: `output/workspace/jobs/${job.slug}.job.json`,
      packagePath: job.paths.packagePath,
      videoPath: job.paths.videoPath,
      thumbnailPath: job.paths.thumbnailPath,
      previewFramePath: job.paths.previewFramePath,
      qualityReportPath: job.paths.qualityReportPath,
      providerJobPath: job.paths.providerJobPath,
      publishPayloadPaths: job.paths.publishPayloadPaths,
      ledgerIds: job.publishing.ledgerIds,
      approvalItemIds: job.publishing.approvalItemIds,
      blockers: job.operator.blockers,
      nextOperatorAction: job.operator.nextAction
    })),
    provenance: {
      mode: "local_dry_run",
      externalCalls: false,
      workspaceSource: "content/workspace.json"
    }
  };

  await writeJson(fromRoot("output", "workspace", "index.json"), index);
  await writeText(
    fromRoot("output", "workspace", "workspace-summary.md"),
    `# ${workspace.name}\n\nMode: ${index.mode}\nWorkspace ID: ${workspace.id}\nDefault brand kit: ${workspace.defaultBrandKitSlug}\n\n## Counts\n\n${markdownList([
      `Jobs: ${index.counts.jobs}`,
      `Publish payloads: ${index.counts.publishPayloads}`,
      `Ledger entries: ${index.counts.ledgerEntries}`,
      `Approval items: ${index.counts.approvalItems}`,
      `Blocked jobs: ${index.counts.blockedJobs}`
    ])}\n\n## Jobs\n\n${markdownList(jobs.map(summaryLine))}\n\n## Dry-Run Boundaries\n\n${markdownList(workspace.provenance.notes)}\n`
  );

  return index;
}

if (fileURLToPath(import.meta.url) === process.argv[1]) {
  const index = await generateWorkspaceJobs();
  console.log(`Generated workspace registry for ${index.counts.jobs} job(s).`);
}
