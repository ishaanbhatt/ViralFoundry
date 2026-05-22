import ffmpeg from "@ffmpeg-installer/ffmpeg";
import { mkdir, readdir, rm, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { spawn } from "node:child_process";
import { fromRoot, readJson, writeJson } from "./lib/fs-utils.js";
import { wrapText } from "./lib/text.js";

const FONT = "/System/Library/Fonts/Supplemental/Arial.ttf";

function ffmpegEscape(value) {
  return String(value)
    .replace(/\\/g, "\\\\")
    .replace(/:/g, "\\:")
    .replace(/'/g, "\\'")
    .replace(/\[/g, "\\[")
    .replace(/\]/g, "\\]")
    .replace(/,/g, "\\,");
}

function drawText({ text, y, size, color = "ffffff", alpha = 1 }) {
  return [
    "drawtext=",
    `fontfile='${FONT}'`,
    `text='${ffmpegEscape(text)}'`,
    `fontsize=${size}`,
    `fontcolor=${color}@${alpha}`,
    "x=(w-text_w)/2",
    `y=${y}`,
    "line_spacing=14"
  ].join(":");
}

function drawBox({ x, y, w, h, color, alpha = 1 }) {
  return `drawbox=x=${x}:y=${y}:w=${w}:h=${h}:color=${color}@${alpha}:t=fill`;
}

function sceneFilter(scene, sceneIndex, totalScenes, size) {
  const titleLines = wrapText(scene.title, 23).slice(0, 3).join("\n");
  const bodyLines = wrapText(scene.body, 32).slice(0, 6).join("\n");
  const palette = scene.palette;
  const layout = scene.layoutSpec || { titleSize: 64, bodySize: 44, titleY: "h*0.2", bodyY: "h*0.42" };
  const progressWidth = Math.round(size.width * ((sceneIndex + 1) / totalScenes));
  const surfaceY = Math.round(size.height * 0.14);
  const surfaceHeight = Math.round(size.height * 0.7);

  return [
    `color=c=#${palette.background}:s=${size.width}x${size.height}:d=${scene.durationSeconds}`,
    `format=yuv420p`,
    drawBox({ x: 82, y: 92, w: 12, h: size.height - 184, color: palette.accent, alpha: 0.86 }),
    drawBox({ x: 120, y: surfaceY, w: size.width - 240, h: surfaceHeight, color: palette.surface, alpha: 0.28 }),
    drawText({ text: titleLines, y: layout.titleY, size: layout.titleSize, color: palette.foreground }),
    drawText({ text: bodyLines, y: layout.bodyY, size: layout.bodySize, color: palette.foreground, alpha: 0.92 }),
    drawText({ text: scene.layout.toUpperCase(), y: 116, size: 28, color: palette.muted, alpha: 0.9 }),
    drawText({ text: `${sceneIndex + 1}/${totalScenes}`, y: "h-190", size: 34, color: palette.accent }),
    `drawbox=x=120:y=h-120:w=${size.width - 240}:h=10:color=${palette.foreground}@0.16:t=fill`,
    `drawbox=x=120:y=h-120:w=${progressWidth - 120}:h=10:color=${palette.accent}@0.95:t=fill`,
    "fade=t=in:st=0:d=0.3",
    `fade=t=out:st=${Math.max(0, scene.durationSeconds - 0.35)}:d=0.35`
  ].join(",");
}

function runFfmpeg(args) {
  return new Promise((resolve, reject) => {
    const child = spawn(ffmpeg.path, args, { stdio: ["ignore", "pipe", "pipe"] });
    let stderr = "";
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg exited with ${code}\n${stderr}`));
    });
  });
}

async function renderScene(scene, sceneIndex, totalScenes, size, tempDir) {
  const scenePath = path.join(tempDir, `${String(sceneIndex).padStart(3, "0")}.mp4`);
  const filter = sceneFilter(scene, sceneIndex, totalScenes, size);
  const tone = 320 + sceneIndex * 55;

  await runFfmpeg([
    "-y",
    "-f",
    "lavfi",
    "-i",
    filter,
    "-f",
    "lavfi",
    "-i",
    `sine=frequency=${tone}:duration=${scene.durationSeconds}:sample_rate=44100`,
    "-shortest",
    "-r",
    String(size.fps),
    "-c:v",
    "libx264",
    "-pix_fmt",
    "yuv420p",
    "-c:a",
    "aac",
    "-b:a",
    "96k",
    scenePath
  ]);

  return scenePath;
}

async function renderStill(inputPath, outputPath, offsetSeconds) {
  await mkdir(path.dirname(outputPath), { recursive: true });
  await runFfmpeg([
    "-y",
    "-ss",
    String(offsetSeconds),
    "-i",
    inputPath,
    "-frames:v",
    "1",
    outputPath
  ]);
}

async function concatScenes(scenePaths, outputPath, tempDir) {
  const listPath = path.join(tempDir, "concat.txt");
  await writeFile(listPath, scenePaths.map((filePath) => `file '${filePath.replace(/'/g, "'\\''")}'`).join("\n"));
  await mkdir(path.dirname(outputPath), { recursive: true });
  await runFfmpeg(["-y", "-f", "concat", "-safe", "0", "-i", listPath, "-c", "copy", outputPath]);
}

export async function renderVideos() {
  const index = await readJson(fromRoot("drafts", "index.json"));
  await rm(fromRoot("output", "videos"), { recursive: true, force: true });
  await rm(fromRoot("output", "manifests"), { recursive: true, force: true });
  await rm(fromRoot("output", "thumbnails"), { recursive: true, force: true });
  await rm(fromRoot("output", "previews"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "videos"), { recursive: true });
  await mkdir(fromRoot("output", "manifests"), { recursive: true });
  await mkdir(fromRoot("output", "thumbnails"), { recursive: true });
  await mkdir(fromRoot("output", "previews"), { recursive: true });
  await rm(fromRoot("tmp", "render"), { recursive: true, force: true });

  const results = [];

  for (const item of index.packages) {
    const draftPackage = await readJson(fromRoot("drafts", item.slug, "package.json"));
    const size = draftPackage.renderPlan.size;
    const tempDir = fromRoot("tmp", "render", item.slug);
    await mkdir(tempDir, { recursive: true });

    const scenePaths = [];
    for (let sceneIndex = 0; sceneIndex < draftPackage.storyboard.length; sceneIndex += 1) {
      scenePaths.push(
        await renderScene(
          draftPackage.storyboard[sceneIndex],
          sceneIndex,
          draftPackage.storyboard.length,
          size,
          tempDir
        )
      );
    }

    const outputPath = fromRoot(draftPackage.renderPlan.output);
    await concatScenes(scenePaths, outputPath, tempDir);
    const thumbnailPath = fromRoot(draftPackage.renderPlan.thumbnail);
    const previewPath = fromRoot(draftPackage.renderPlan.previewFrame);
    await renderStill(outputPath, thumbnailPath, 1);
    await renderStill(outputPath, previewPath, Math.min(3, Math.max(1, draftPackage.creativeBrief.durationSeconds / 4)));
    const fileStat = await stat(outputPath);
    const thumbnailStat = await stat(thumbnailPath);
    const previewStat = await stat(previewPath);
    const manifest = {
      slug: item.slug,
      outputPath,
      bytes: fileStat.size,
      thumbnailPath,
      thumbnailBytes: thumbnailStat.size,
      previewFramePath: previewPath,
      previewFrameBytes: previewStat.size,
      scenes: draftPackage.storyboard.length,
      durationSeconds: draftPackage.creativeBrief.durationSeconds,
      designTheme: draftPackage.designBrief.theme,
      platforms: draftPackage.platformVariants.map((variant) => variant.platform),
      renderedAt: new Date().toISOString(),
      ffmpegPath: ffmpeg.path
    };
    await writeJson(fromRoot("output", "manifests", `${item.slug}.render.json`), manifest);
    results.push(manifest);
  }

  return results;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const draftDirExists = await readdir(fromRoot("drafts")).then(() => true).catch(() => false);
  if (!draftDirExists) {
    throw new Error("No drafts found. Run npm run generate first.");
  }

  const results = await renderVideos();
  for (const result of results) {
    console.log(`Rendered ${result.outputPath} (${result.bytes} bytes).`);
  }
}
