import { access, readdir, stat } from "node:fs/promises";
import path from "node:path";
import { fromRoot, readJson } from "./lib/fs-utils.js";

const requiredPackageKeys = [
  "creativeBrief",
  "script",
  "designBrief",
  "platformVariants",
  "storyboard",
  "shotList",
  "motionPlan",
  "audioPlan",
  "captions",
  "metadata",
  "assets",
  "qaChecklist",
  "renderPlan"
];

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function assertRelativePathInside(value, prefix, message) {
  assert(typeof value === "string", `${message}: path must be a string`);
  assert(!path.isAbsolute(value), `${message}: path must be relative`);
  const normalized = path.normalize(value);
  assert(!normalized.startsWith(".."), `${message}: path must stay inside project root`);
  assert(normalized === value, `${message}: path must be normalized`);
  assert(normalized.startsWith(`${prefix}/`), `${message}: path must be under ${prefix}`);
}

async function validatePackage(item) {
  const draftPackage = await readJson(fromRoot("drafts", item.slug, "package.json"));
  for (const key of requiredPackageKeys) {
    assert(draftPackage[key], `${item.slug}: missing ${key}`);
  }

  assert(draftPackage.storyboard.length > 0, `${item.slug}: storyboard is empty`);
  assert(draftPackage.shotList.length === draftPackage.storyboard.length, `${item.slug}: shot list does not match storyboard scenes`);
  assert(draftPackage.motionPlan.length === draftPackage.storyboard.length, `${item.slug}: motion plan does not match storyboard scenes`);
  assert(
    draftPackage.captions.length === draftPackage.storyboard.length,
    `${item.slug}: captions do not match storyboard scenes`
  );
  assert(draftPackage.script.voiceover.length > 80, `${item.slug}: voiceover is too short`);
  assert(draftPackage.designBrief.colorTokens.accent, `${item.slug}: missing design color tokens`);
  assert(draftPackage.designBrief.motion, `${item.slug}: missing motion design brief`);
  assert(draftPackage.audioPlan.finalVoice, `${item.slug}: missing audio plan`);
  assert(draftPackage.platformVariants.length > 0, `${item.slug}: missing platform variants`);
  assert(draftPackage.renderPlan.output.endsWith(".mp4"), `${item.slug}: render output must be an MP4`);
  assert(draftPackage.renderPlan.thumbnail.endsWith(".png"), `${item.slug}: render thumbnail must be a PNG`);
  assert(draftPackage.renderPlan.previewFrame.endsWith(".png"), `${item.slug}: render preview frame must be a PNG`);

  await access(fromRoot("drafts", item.slug, "script.md"));
  await access(fromRoot("drafts", item.slug, "design-brief.json"));
  await access(fromRoot("drafts", item.slug, "storyboard.json"));
  await access(fromRoot("drafts", item.slug, "shot-list.json"));
  await access(fromRoot("drafts", item.slug, "motion-plan.json"));
  await access(fromRoot("drafts", item.slug, "audio-plan.json"));
  await access(fromRoot("drafts", item.slug, "metadata.json"));
  await access(fromRoot("drafts", item.slug, "platform-variants.json"));
  await access(fromRoot("drafts", item.slug, "render-plan.json"));
  await access(fromRoot("drafts", item.slug, "captions.srt"));
  await access(fromRoot("drafts", item.slug, "production-notes.md"));

  const videoPath = fromRoot(draftPackage.renderPlan.output);
  const videoStat = await stat(videoPath);
  assert(videoStat.size > 100_000, `${item.slug}: rendered MP4 is unexpectedly small`);

  const thumbnailPath = fromRoot(draftPackage.renderPlan.thumbnail);
  const thumbnailStat = await stat(thumbnailPath);
  assert(thumbnailStat.size > 20_000, `${item.slug}: thumbnail is unexpectedly small`);

  const previewFramePath = fromRoot(draftPackage.renderPlan.previewFrame);
  const previewStat = await stat(previewFramePath);
  assert(previewStat.size > 20_000, `${item.slug}: preview frame is unexpectedly small`);

  const manifest = await readJson(fromRoot("output", "manifests", `${item.slug}.render.json`));
  assert(manifest.bytes === videoStat.size, `${item.slug}: manifest byte count is stale`);
  assert(manifest.thumbnailBytes === thumbnailStat.size, `${item.slug}: manifest thumbnail byte count is stale`);
  assert(manifest.previewFrameBytes === previewStat.size, `${item.slug}: manifest preview frame byte count is stale`);
  assert(manifest.designTheme === draftPackage.designBrief.theme, `${item.slug}: manifest design theme is stale`);

  const quality = await readJson(fromRoot("output", "quality", `${item.slug}.quality.json`));
  assert(quality.score >= 90, `${item.slug}: quality score is below publish-prep threshold`);
  assert(quality.recommendation === "approved_for_publish_prep", `${item.slug}: quality recommendation is not approved`);

  const publishPayloads = await readdir(fromRoot("output", "publish", item.slug));
  const expectedPayloads = draftPackage.platformVariants.length;
  assert(
    publishPayloads.filter((file) => file.endsWith(".publish.json")).length === expectedPayloads,
    `${item.slug}: publish payload count does not match platform variants`
  );

  const providerJob = await readJson(fromRoot("output", "provider-jobs", `${item.slug}.provider-job.json`));
  assert(providerJob.provider.mode === "dry_run", `${item.slug}: provider job must stay in dry-run mode`);
  assert(providerJob.response.status === "contract_ready", `${item.slug}: provider job contract is not ready`);
  assert(providerJob.response.submitted === false, `${item.slug}: dry-run provider job must not be submitted`);
  assert(providerJob.provenance.renderSource === "local_render_fallback", `${item.slug}: provider provenance is unclear`);

  return {
    slug: item.slug,
    videoPath,
    bytes: videoStat.size,
    thumbnailPath,
    previewFramePath,
    scenes: draftPackage.storyboard.length
  };
}

const index = await readJson(fromRoot("drafts", "index.json"));
assert(index.count === index.packages.length, "draft index count mismatch");
await access(fromRoot("content", "design-system.json"));
const brandKitInput = await readJson(fromRoot("content", "brand-kits.json"));
assert(Array.isArray(brandKitInput.brandKits) && brandKitInput.brandKits.length > 0, "brand kit input is empty");
const brandKitIndex = await readJson(fromRoot("output", "brand-kits", "index.json"));
assert(brandKitIndex.mode === "local_dry_run", "brand kits must stay in local dry-run mode");
assert(brandKitIndex.count === brandKitIndex.entries.length, "brand kit index count mismatch");
assert(brandKitIndex.count === brandKitInput.brandKits.length, "brand kit output count mismatch");
assert(
  brandKitIndex.entries.every((entry) => {
    assertRelativePathInside(entry.artifactPath, "output/brand-kits", `${entry.slug}: brand kit artifact`);
    return entry.artifactPath.endsWith(".brand-kit.json");
  }),
  "brand kit entries must point to JSON artifacts"
);
await access(fromRoot("output", "brand-kits", "brand-kit-summary.md"));
for (const entry of brandKitIndex.entries) {
  const brandKit = await readJson(fromRoot(entry.artifactPath));
  assert(brandKit.name === entry.name, `${entry.slug}: brand kit artifact name mismatch`);
  assert(brandKit.positioning, `${entry.slug}: missing brand positioning`);
  assert(brandKit.audience?.primary, `${entry.slug}: missing primary audience`);
  assert(brandKit.voice?.traits?.length > 0, `${entry.slug}: missing voice traits`);
  assert(brandKit.visualTokens?.palette?.accent, `${entry.slug}: missing accent color`);
  assert(brandKit.typography?.primaryFont, `${entry.slug}: missing primary font`);
  assert(brandKit.assets?.logoPlaceholder, `${entry.slug}: missing logo placeholder`);
  assert(brandKit.compliance?.disclosures?.length > 0, `${entry.slug}: missing compliance disclosures`);
  assert(brandKit.provenance?.mode === "local_dry_run", `${entry.slug}: unclear brand kit provenance`);
}
await access(fromRoot("output", "review", "index.html"));
const qualityIndex = await readJson(fromRoot("output", "quality", "index.json"));
assert(qualityIndex.count === index.count, "quality index count mismatch");
assert(qualityIndex.averageScore >= 90, "average quality score is below threshold");
const providerIndex = await readJson(fromRoot("output", "provider-jobs", "index.json"));
assert(providerIndex.mode === "dry_run", "provider jobs must stay in dry-run mode");
assert(providerIndex.count === index.count, "provider job count mismatch");
assert(providerIndex.entries.every((entry) => entry.submitted === false), "dry-run provider jobs must not be submitted");
await access(fromRoot("output", "provider-jobs", "provider-plan.md"));
const publishIndex = await readJson(fromRoot("output", "publish", "index.json"));
assert(publishIndex.mode === "dry_run", "publish prep must stay in dry-run mode");
assert(publishIndex.entries.length >= index.count, "publish index does not include enough payloads");
await access(fromRoot("output", "publish", "publish-plan.md"));
const publishLedger = await readJson(fromRoot("output", "publish-ledger", "index.json"));
assert(publishLedger.mode === "dry_run", "publish ledger must stay in dry-run mode");
assert(publishLedger.count === publishIndex.entries.length, "publish ledger count mismatch");
assert(publishLedger.submittedCount === 0, "dry-run publish ledger must not contain submitted uploads");
assert(
  publishLedger.entries.every((entry) => entry.upload.status === "not_submitted" && entry.upload.platformPostId === null),
  "dry-run publish ledger entries must not have platform upload IDs"
);
assert(
  publishLedger.entries.every((entry) => entry.approval.status === "human_approval_required"),
  "publish ledger entries must require human approval"
);
assert(
  publishLedger.entries.every((entry) => /^[A-Z0-9_]+$/.test(entry.requiredCredential)),
  "publish ledger credentials must be environment-variable safe"
);
await access(fromRoot("output", "publish-ledger", "publish-ledger.md"));
const approvalQueue = await readJson(fromRoot("output", "approvals", "index.json"));
assert(approvalQueue.mode === "dry_run", "approval queue must stay in dry-run mode");
assert(approvalQueue.count === publishLedger.count, "approval queue count mismatch");
assert(approvalQueue.pendingReviewCount === approvalQueue.count, "approval queue entries must be pending review");
assert(approvalQueue.liveUploadReadyCount === 0, "dry-run approval queue must not mark uploads ready");
assert(
  approvalQueue.items.every((item) => item.status === "awaiting_human_approval" && item.approvalState.approved === false),
  "approval queue items must require manual approval"
);
assert(
  approvalQueue.items.every((item) => item.releaseDecision.canProceedToLiveUpload === false),
  "approval queue must keep live upload disabled"
);
assert(
  approvalQueue.items.every((item) => item.reviewChecklist.length >= 5 && item.reviewBoardPath === "output/review/index.html"),
  "approval queue items must include review checklist and review board path"
);
await access(fromRoot("output", "approvals", "approval-queue.md"));
const operationsReport = await readJson(fromRoot("output", "operations", "run-report.json"));
assert(operationsReport.summary.drafts === index.count, "operations report draft count mismatch");
assert(operationsReport.summary.brandKits === brandKitIndex.count, "operations report brand kit count mismatch");
assert(operationsReport.summary.providerJobs === providerIndex.count, "operations report provider job count mismatch");
assert(operationsReport.summary.publishPayloads === publishIndex.entries.length, "operations report publish count mismatch");
assert(operationsReport.summary.publishLedgerEntries === publishLedger.count, "operations report publish ledger count mismatch");
assert(operationsReport.summary.approvalQueueItems === approvalQueue.count, "operations report approval queue count mismatch");
await access(fromRoot("output", "operations", "content-calendar.md"));

const results = [];
for (const item of index.packages) {
  results.push(await validatePackage(item));
}

console.log(`Validated ${results.length} draft package(s) and MP4 render(s).`);
for (const result of results) {
  console.log(`- ${result.slug}: ${result.scenes} scenes, ${result.bytes} bytes, ${result.videoPath}`);
}
