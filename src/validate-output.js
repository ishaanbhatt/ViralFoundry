import { access, readdir, stat } from "node:fs/promises";
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
await access(fromRoot("output", "review", "index.html"));
const qualityIndex = await readJson(fromRoot("output", "quality", "index.json"));
assert(qualityIndex.count === index.count, "quality index count mismatch");
assert(qualityIndex.averageScore >= 90, "average quality score is below threshold");
const publishIndex = await readJson(fromRoot("output", "publish", "index.json"));
assert(publishIndex.mode === "dry_run", "publish prep must stay in dry-run mode");
assert(publishIndex.entries.length >= index.count, "publish index does not include enough payloads");
await access(fromRoot("output", "publish", "publish-plan.md"));
const operationsReport = await readJson(fromRoot("output", "operations", "run-report.json"));
assert(operationsReport.summary.drafts === index.count, "operations report draft count mismatch");
assert(operationsReport.summary.publishPayloads === publishIndex.entries.length, "operations report publish count mismatch");
await access(fromRoot("output", "operations", "content-calendar.md"));

const results = [];
for (const item of index.packages) {
  results.push(await validatePackage(item));
}

console.log(`Validated ${results.length} draft package(s) and MP4 render(s).`);
for (const result of results) {
  console.log(`- ${result.slug}: ${result.scenes} scenes, ${result.bytes} bytes, ${result.videoPath}`);
}
