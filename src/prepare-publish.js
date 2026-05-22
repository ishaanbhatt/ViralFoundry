import { mkdir, rm } from "node:fs/promises";
import { fromRoot, readJson, slugify, writeJson, writeText } from "./lib/fs-utils.js";
import { markdownList } from "./lib/text.js";

function buildPayload({ draftPackage, manifest, qualityReport, variant }) {
  return {
    mode: "dry_run",
    platform: variant.platform,
    slug: draftPackage.slug,
    title: variant.title,
    caption: `${draftPackage.metadata.description}\n\n${draftPackage.metadata.hashtags.join(" ")}`,
    videoPath: manifest.outputPath,
    thumbnailPath: manifest.thumbnailPath,
    durationSeconds: manifest.durationSeconds,
    aspectRatio: variant.aspectRatio,
    readiness: {
      qualityRecommendation: qualityReport.recommendation,
      qualityScore: qualityReport.score,
      status: qualityReport.recommendation === "approved_for_publish_prep" ? "asset_ready_credentials_needed" : "needs_review",
      blockers: draftPackage.assets.missingForPublish
    },
    integrationContract: {
      requiredCredential: `${slugify(variant.platform).toUpperCase()}_ACCESS_TOKEN`,
      uploadEndpoint: "not_configured",
      idempotencyKey: `${draftPackage.slug}-${slugify(variant.platform)}`
    }
  };
}

function publishPlanLine(entry) {
  return `- ${entry.slug} / ${entry.platform}: ${entry.status} (${entry.qualityScore}/100)`;
}

export async function preparePublish() {
  const index = await readJson(fromRoot("drafts", "index.json"));
  await rm(fromRoot("output", "publish"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "publish"), { recursive: true });

  const entries = [];
  for (const item of index.packages) {
    const draftPackage = await readJson(fromRoot("drafts", item.slug, "package.json"));
    const manifest = await readJson(fromRoot("output", "manifests", `${item.slug}.render.json`));
    const qualityReport = await readJson(fromRoot("output", "quality", `${item.slug}.quality.json`));
    const publishDir = fromRoot("output", "publish", item.slug);
    await mkdir(publishDir, { recursive: true });

    for (const variant of draftPackage.platformVariants) {
      const payload = buildPayload({ draftPackage, manifest, qualityReport, variant });
      const platformSlug = slugify(variant.platform);
      await writeJson(`${publishDir}/${platformSlug}.publish.json`, payload);
      entries.push({
        slug: item.slug,
        platform: variant.platform,
        status: payload.readiness.status,
        qualityScore: qualityReport.score,
        payload: `output/publish/${item.slug}/${platformSlug}.publish.json`
      });
    }
  }

  const plan = {
    generatedAt: new Date().toISOString(),
    mode: "dry_run",
    entries,
    nextIntegrationSteps: [
      "Replace guide audio with final voiceover.",
      "Add platform credentials as environment variables.",
      "Implement platform upload clients behind the dry-run payload contract.",
      "Record returned platform IDs in a publish ledger."
    ]
  };
  await writeJson(fromRoot("output", "publish", "index.json"), plan);
  await writeText(
    fromRoot("output", "publish", "publish-plan.md"),
    `# Publish Plan\n\nMode: dry_run\n\n## Payloads\n\n${markdownList(entries.map(publishPlanLine))}\n\n## Next Integration Steps\n\n${markdownList(plan.nextIntegrationSteps)}\n`
  );
  return plan;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const plan = await preparePublish();
  console.log(`Prepared ${plan.entries.length} dry-run publish payload(s).`);
}
