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
  const draftIndex = await readJson(fromRoot("drafts", "index.json"));
  const qualityIndex = await readJson(fromRoot("output", "quality", "index.json"));
  const publishIndex = await readJson(fromRoot("output", "publish", "index.json"));
  await rm(fromRoot("output", "operations"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "operations"), { recursive: true });

  const start = new Date();
  const calendar = draftIndex.packages.map((item, index) => {
    const quality = qualityIndex.reports.find((report) => report.slug === item.slug);
    const platforms = publishIndex.entries
      .filter((entry) => entry.slug === item.slug)
      .map((entry) => entry.platform);
    return {
      date: isoDate(addDays(start, index * 2)),
      slug: item.slug,
      title: item.title,
      platforms,
      qualityScore: quality.score,
      status: quality.recommendation === "approved_for_publish_prep" ? "ready_for_final_voiceover" : "review_needed"
    };
  });

  const runReport = {
    generatedAt: new Date().toISOString(),
    summary: {
      drafts: draftIndex.count,
      renderedVideos: draftIndex.count,
      averageQualityScore: qualityIndex.averageScore,
      publishPayloads: publishIndex.entries.length,
      reviewBoard: "output/review/index.html"
    },
    calendar,
    risks: [
      "Publishing remains dry-run until credentials and upload clients are implemented.",
      "Audio is a generated guide track until final voiceover is recorded or synthesized.",
      "Human review is still required before public distribution."
    ]
  };

  await writeJson(fromRoot("output", "operations", "run-report.json"), runReport);
  await writeText(
    fromRoot("output", "operations", "content-calendar.md"),
    `# Content Calendar\n\n${markdownList(calendar.map((entry) => `${entry.date}: ${entry.title} -> ${entry.platforms.join(", ")} (${entry.status}, ${entry.qualityScore}/100)`))}\n`
  );
  return runReport;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const report = await generateOperations();
  console.log(`Generated operations report for ${report.summary.drafts} draft(s).`);
}
