import { mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { fromRoot, readJson, writeJson } from "./lib/fs-utils.js";

const GATES = [
  {
    id: "creative_complete",
    weight: 18,
    check: (pkg) => Boolean(pkg.creativeBrief.title && pkg.creativeBrief.objective && pkg.script.voiceover),
    pass: "Creative brief and script are complete.",
    fail: "Creative brief or script is incomplete."
  },
  {
    id: "storyboard_timed",
    weight: 14,
    check: (pkg) => pkg.storyboard.length > 0 && pkg.storyboard.every((scene) => scene.durationSeconds >= 4),
    pass: "Storyboard has timed scenes with usable durations.",
    fail: "Storyboard timing is missing or too short."
  },
  {
    id: "design_covered",
    weight: 16,
    check: (pkg) => Boolean(pkg.designBrief.colorTokens && pkg.designBrief.motion && pkg.shotList.length === pkg.storyboard.length),
    pass: "Visual, motion, and shot-list decisions are represented.",
    fail: "Design coverage is incomplete."
  },
  {
    id: "platform_variants",
    weight: 12,
    check: (pkg) => pkg.platformVariants.length > 0 && pkg.platformVariants.every((variant) => variant.aspectRatio === "9:16"),
    pass: "Platform variants are present and vertical-first.",
    fail: "Platform variants are missing or incompatible."
  },
  {
    id: "caption_ready",
    weight: 12,
    check: (pkg) => pkg.captions.length === pkg.storyboard.length && pkg.srt.includes("-->"),
    pass: "Captions and sidecar SRT are ready.",
    fail: "Captions or SRT are incomplete."
  },
  {
    id: "render_ready",
    weight: 18,
    check: (_pkg, manifest) => manifest.bytes > 100_000 && manifest.thumbnailBytes > 20_000 && manifest.previewFrameBytes > 20_000,
    pass: "MP4, thumbnail, and preview frame exist.",
    fail: "Rendered assets are missing or too small."
  },
  {
    id: "publish_boundaries",
    weight: 10,
    check: (pkg) => pkg.assets.missingForPublish.includes("platform_credentials") && pkg.assets.missingForPublish.includes("final_voiceover"),
    pass: "Publish blockers are explicit.",
    fail: "Publish blockers are not explicit enough."
  }
];

function evaluateGate(gate, draftPackage, manifest) {
  const passed = gate.check(draftPackage, manifest);
  return {
    id: gate.id,
    passed,
    weight: gate.weight,
    points: passed ? gate.weight : 0,
    note: passed ? gate.pass : gate.fail
  };
}

function recommendationFor(score) {
  if (score >= 90) return "approved_for_publish_prep";
  if (score >= 75) return "needs_light_review";
  return "revise_before_publish_prep";
}

export async function scoreQuality() {
  const index = await readJson(fromRoot("drafts", "index.json"));
  await rm(fromRoot("output", "quality"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "quality"), { recursive: true });

  const reports = [];
  for (const item of index.packages) {
    const draftPackage = await readJson(fromRoot("drafts", item.slug, "package.json"));
    const manifest = await readJson(fromRoot("output", "manifests", `${item.slug}.render.json`));
    const gates = GATES.map((gate) => evaluateGate(gate, draftPackage, manifest));
    const score = gates.reduce((sum, gate) => sum + gate.points, 0);
    const report = {
      slug: item.slug,
      title: draftPackage.creativeBrief.title,
      score,
      recommendation: recommendationFor(score),
      gates,
      reviewedAssets: {
        package: path.relative(fromRoot(), fromRoot("drafts", item.slug, "package.json")),
        video: path.relative(fromRoot(), manifest.outputPath),
        thumbnail: path.relative(fromRoot(), manifest.thumbnailPath),
        previewFrame: path.relative(fromRoot(), manifest.previewFramePath)
      },
      generatedAt: new Date().toISOString()
    };
    await writeJson(fromRoot("output", "quality", `${item.slug}.quality.json`), report);
    reports.push(report);
  }

  const indexReport = {
    generatedAt: new Date().toISOString(),
    count: reports.length,
    averageScore: Math.round(reports.reduce((sum, report) => sum + report.score, 0) / reports.length),
    approvedCount: reports.filter((report) => report.recommendation === "approved_for_publish_prep").length,
    reports: reports.map((report) => ({
      slug: report.slug,
      title: report.title,
      score: report.score,
      recommendation: report.recommendation
    }))
  };
  await writeJson(fromRoot("output", "quality", "index.json"), indexReport);
  return indexReport;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const result = await scoreQuality();
  console.log(`Scored ${result.count} package(s). Average score: ${result.averageScore}.`);
}
