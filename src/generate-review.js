import { mkdir, stat } from "node:fs/promises";
import path from "node:path";
import { fromRoot, readJson, writeText } from "./lib/fs-utils.js";

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function rel(filePath) {
  return path.relative(fromRoot("output", "review"), filePath).replace(/\\/g, "/");
}

async function fileSize(filePath) {
  const info = await stat(filePath);
  return `${Math.round(info.size / 1024)} KB`;
}

function platformTags(variants) {
  return variants
    .map((variant) => `<span class="tag">${escapeHtml(variant.platform)}</span>`)
    .join("");
}

function checklist(items) {
  return items.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function packageCard({ draftPackage, manifest, videoSize, thumbnailSize }) {
  const thumbnailSrc = rel(manifest.thumbnailPath);
  const videoSrc = rel(manifest.outputPath);
  return `
    <article class="package">
      <header class="package__header">
        <div>
          <p class="eyebrow">${escapeHtml(draftPackage.designBrief.theme)} / ${draftPackage.storyboard.length} scenes</p>
          <h2>${escapeHtml(draftPackage.creativeBrief.title)}</h2>
          <p>${escapeHtml(draftPackage.creativeBrief.objective)}</p>
        </div>
        <div class="status">Draft ready</div>
      </header>
      <div class="media-grid">
        <img src="${thumbnailSrc}" alt="${escapeHtml(draftPackage.creativeBrief.title)} thumbnail">
        <video src="${videoSrc}" controls preload="metadata"></video>
      </div>
      <div class="meta-grid">
        <section>
          <h3>Design Intent</h3>
          <p>${escapeHtml(draftPackage.designBrief.designIntent)}</p>
        </section>
        <section>
          <h3>Platforms</h3>
          <div class="tags">${platformTags(draftPackage.platformVariants)}</div>
        </section>
        <section>
          <h3>Render</h3>
          <p>${manifest.durationSeconds}s / ${videoSize} MP4 / ${thumbnailSize} thumbnail</p>
        </section>
        <section>
          <h3>Missing For Publish</h3>
          <p>${escapeHtml(draftPackage.assets.missingForPublish.join(", "))}</p>
        </section>
      </div>
      <details>
        <summary>QA checklist</summary>
        <ul>${checklist(draftPackage.qaChecklist)}</ul>
      </details>
    </article>
  `;
}

export async function generateReviewBoard() {
  const index = await readJson(fromRoot("drafts", "index.json"));
  const cards = [];

  for (const item of index.packages) {
    const draftPackage = await readJson(fromRoot("drafts", item.slug, "package.json"));
    const manifest = await readJson(fromRoot("output", "manifests", `${item.slug}.render.json`));
    cards.push(
      packageCard({
        draftPackage,
        manifest,
        videoSize: await fileSize(manifest.outputPath),
        thumbnailSize: await fileSize(manifest.thumbnailPath)
      })
    );
  }

  const html = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Local Video Draft Review</title>
    <style>
      :root {
        color-scheme: light;
        font-family: Arial, Helvetica, sans-serif;
        background: #f5f7fb;
        color: #111827;
      }
      * { box-sizing: border-box; }
      body { margin: 0; }
      header.hero {
        padding: 40px 32px 24px;
        background: #0f172a;
        color: #f8fafc;
      }
      .hero h1 {
        margin: 0 0 10px;
        font-size: clamp(32px, 5vw, 56px);
        line-height: 1;
      }
      .hero p {
        margin: 0;
        max-width: 760px;
        color: #cbd5e1;
        font-size: 18px;
        line-height: 1.5;
      }
      main {
        display: grid;
        gap: 24px;
        max-width: 1180px;
        margin: 0 auto;
        padding: 28px 20px 48px;
      }
      .package {
        background: #ffffff;
        border: 1px solid #dbe3ef;
        border-radius: 8px;
        padding: 22px;
      }
      .package__header {
        display: flex;
        justify-content: space-between;
        gap: 24px;
        align-items: flex-start;
      }
      h2, h3, p { margin-top: 0; }
      h2 { margin-bottom: 8px; font-size: 28px; line-height: 1.1; }
      h3 { margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0; color: #475569; }
      .eyebrow { margin-bottom: 8px; color: #2563eb; font-size: 13px; font-weight: 700; text-transform: uppercase; }
      .status {
        flex: 0 0 auto;
        border: 1px solid #86efac;
        background: #dcfce7;
        color: #166534;
        padding: 8px 10px;
        border-radius: 6px;
        font-size: 13px;
        font-weight: 700;
      }
      .media-grid {
        display: grid;
        grid-template-columns: minmax(180px, 260px) minmax(260px, 1fr);
        gap: 18px;
        margin: 18px 0;
        align-items: start;
      }
      img, video {
        width: 100%;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        background: #111827;
      }
      video { aspect-ratio: 9 / 16; max-height: 640px; }
      .meta-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 16px;
      }
      .meta-grid section {
        border-top: 1px solid #e2e8f0;
        padding-top: 12px;
      }
      .tags { display: flex; flex-wrap: wrap; gap: 8px; }
      .tag {
        display: inline-flex;
        border: 1px solid #bfdbfe;
        color: #1e3a8a;
        background: #eff6ff;
        border-radius: 6px;
        padding: 5px 8px;
        font-size: 13px;
      }
      details { margin-top: 16px; }
      summary { cursor: pointer; font-weight: 700; }
      li { margin-bottom: 6px; }
      @media (max-width: 820px) {
        .package__header, .media-grid, .meta-grid { grid-template-columns: 1fr; display: grid; }
        .status { width: fit-content; }
      }
    </style>
  </head>
  <body>
    <header class="hero">
      <h1>Draft Review Board</h1>
      <p>Generated packages, rendered MP4s, thumbnails, platform variants, and QA state in one local design review surface.</p>
    </header>
    <main>${cards.join("\n")}</main>
  </body>
</html>`;

  const reviewPath = fromRoot("output", "review", "index.html");
  await mkdir(path.dirname(reviewPath), { recursive: true });
  await writeText(reviewPath, html);
  return { reviewPath, count: cards.length };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const result = await generateReviewBoard();
  console.log(`Generated review board for ${result.count} package(s): ${result.reviewPath}`);
}
