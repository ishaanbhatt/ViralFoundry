import { mkdir, rm } from "node:fs/promises";
import { DRY_RUN_PROVIDER, buildProviderRequest, submitDryRunProviderJob } from "./provider-adapters/dry-run-provider.js";
import { fromRoot, readJson, writeJson, writeText } from "./lib/fs-utils.js";
import { markdownList } from "./lib/text.js";

function jobSummaryLine(entry) {
  return `${entry.slug}: ${entry.status}, ${entry.mode}, ${entry.cost.estimatedUsd} ${entry.cost.currency}`;
}

export async function generateProviderJobs() {
  const index = await readJson(fromRoot("drafts", "index.json"));
  await rm(fromRoot("output", "provider-jobs"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "provider-jobs"), { recursive: true });

  const entries = [];
  for (const item of index.packages) {
    const draftPackage = await readJson(fromRoot("drafts", item.slug, "package.json"));
    const manifest = await readJson(fromRoot("output", "manifests", `${item.slug}.render.json`));
    const qualityReport = await readJson(fromRoot("output", "quality", `${item.slug}.quality.json`));
    const request = buildProviderRequest({ draftPackage, manifest, qualityReport });
    const response = submitDryRunProviderJob(request);
    const job = {
      generatedAt: new Date().toISOString(),
      slug: item.slug,
      title: item.title,
      provider: DRY_RUN_PROVIDER,
      request,
      response,
      provenance: {
        renderSource: "local_render_fallback",
        packagePath: `drafts/${item.slug}/package.json`,
        localRenderPath: request.references.localRender,
        qualityReportPath: `output/quality/${item.slug}.quality.json`
      }
    };

    const jobPath = `output/provider-jobs/${item.slug}.provider-job.json`;
    await writeJson(fromRoot(jobPath), job);
    entries.push({
      slug: item.slug,
      title: item.title,
      provider: DRY_RUN_PROVIDER.id,
      mode: DRY_RUN_PROVIDER.mode,
      status: response.status,
      submitted: response.submitted,
      cost: response.cost,
      jobPath
    });
  }

  const providerIndex = {
    generatedAt: new Date().toISOString(),
    mode: DRY_RUN_PROVIDER.mode,
    provider: DRY_RUN_PROVIDER,
    count: entries.length,
    entries,
    nextIntegrationSteps: [
      "Choose the first live video provider and map its request fields to the dry-run contract.",
      "Add credential loading without changing generated package structure.",
      "Persist provider job IDs, status polling results, output URLs, errors, and final costs.",
      "Keep local MP4s as the fallback render source until provider outputs pass review."
    ]
  };

  await writeJson(fromRoot("output", "provider-jobs", "index.json"), providerIndex);
  await writeText(
    fromRoot("output", "provider-jobs", "provider-plan.md"),
    `# Provider Job Plan\n\nMode: ${providerIndex.mode}\nProvider: ${providerIndex.provider.displayName}\n\n## Jobs\n\n${markdownList(entries.map(jobSummaryLine))}\n\n## Next Integration Steps\n\n${markdownList(providerIndex.nextIntegrationSteps)}\n`
  );
  return providerIndex;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const result = await generateProviderJobs();
  console.log(`Generated ${result.count} dry-run provider job contract(s).`);
}
