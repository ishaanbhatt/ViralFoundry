import { rm } from "node:fs/promises";
import { fromRoot, readJson, slugify, writeJson, writeText } from "./lib/fs-utils.js";
import { designBriefFor, loadDesignSystem, pickTheme, platformVariants } from "./lib/design-system.js";
import { markdownList, secondsToSrtTime, sentenceCase } from "./lib/text.js";

const DEFAULT_SIZE = { width: 1080, height: 1920, fps: 30 };

function buildScenes(brief) {
  const duration = Number(brief.durationSeconds || 36);
  const takeaways = brief.takeaways?.length ? brief.takeaways : [brief.objective];
  const introDuration = Math.max(5, Math.round(duration * 0.2));
  const closeDuration = Math.max(5, Math.round(duration * 0.18));
  const middleDuration = Math.max(6, duration - introDuration - closeDuration);
  const perTakeaway = Math.max(5, Math.floor(middleDuration / takeaways.length));

  const scenes = [
    {
      id: "hook",
      durationSeconds: introDuration,
      layout: "hook",
      title: brief.title,
      body: sentenceCase(brief.objective),
      visualDirection: "Bold title slate with a clear product-risk framing.",
      motionCue: "fast title resolve",
      caption: brief.objective
    },
    ...takeaways.map((takeaway, index) => ({
      id: `takeaway-${index + 1}`,
      durationSeconds: perTakeaway,
      layout: index === takeaways.length - 1 ? "proof" : "explain",
      title: `Point ${index + 1}`,
      body: takeaway,
      visualDirection: "Large readable text, subtle motion, and a progress cue.",
      motionCue: index === takeaways.length - 1 ? "proof card hold" : "steady point reveal",
      caption: takeaway
    })),
    {
      id: "close",
      durationSeconds: closeDuration,
      layout: "close",
      title: "What this unlocks",
      body: "When the MP4 is real, publishing is just the next integration layer.",
      visualDirection: "Final decision-oriented slate with a direct closing line.",
      motionCue: "calm final lockup",
      caption: "When the MP4 is real, publishing is just the next integration layer."
    }
  ];

  const total = scenes.reduce((sum, scene) => sum + scene.durationSeconds, 0);
  if (total !== duration) {
    scenes[scenes.length - 1].durationSeconds += duration - total;
  }

  return scenes;
}

function buildSrt(captions) {
  let cursor = 0;
  return captions
    .map((caption, index) => {
      const start = cursor;
      const end = cursor + caption.durationSeconds;
      cursor = end;
      return `${index + 1}\n${secondsToSrtTime(start)} --> ${secondsToSrtTime(end)}\n${caption.text}\n`;
    })
    .join("\n");
}

function buildPackage(brief, index, designSystem) {
  const slug = slugify(brief.slug || brief.title);
  const scenes = buildScenes(brief);
  const theme = pickTheme(designSystem, index);
  const designBrief = designBriefFor(brief, designSystem, theme);
  const variants = platformVariants(brief, designSystem);
  const voiceover = scenes
    .map((scene) => `${scene.title}. ${scene.caption}`)
    .join("\n\n");
  const captions = scenes.map((scene) => ({
    sceneId: scene.id,
    text: scene.caption,
    durationSeconds: scene.durationSeconds
  }));
  const storyboard = scenes.map((scene, sceneIndex) => ({
    ...scene,
    sceneNumber: sceneIndex + 1,
    layoutSpec: designSystem.visual.layouts[scene.layout],
    palette: {
      background: theme.background,
      surface: theme.surface,
      foreground: theme.foreground,
      muted: theme.muted,
      accent: theme.accent,
      secondary: theme.secondary
    }
  }));

  return {
    slug,
    creativeBrief: {
      title: brief.title,
      audience: brief.audience,
      objective: brief.objective,
      tone: brief.tone || "clear and practical",
      platforms: brief.platforms || ["Short-form video"],
      durationSeconds: scenes.reduce((sum, scene) => sum + scene.durationSeconds, 0)
    },
    script: {
      voiceover,
      onScreenText: scenes.map((scene) => ({
        sceneId: scene.id,
        title: scene.title,
        body: scene.body
      }))
    },
    designBrief,
    platformVariants: variants,
    storyboard,
    shotList: storyboard.map((scene) => ({
      sceneId: scene.id,
      shotType: scene.layout,
      composition: scene.visualDirection,
      motion: scene.motionCue,
      textPriority: scene.sceneNumber === 1 ? "hook" : scene.sceneNumber === storyboard.length ? "close" : "support"
    })),
    motionPlan: storyboard.map((scene) => ({
      sceneId: scene.id,
      cue: scene.motionCue,
      transitionSeconds: designSystem.motion.defaultTransitionSeconds,
      style: designSystem.motion.sceneStyles[scene.layout]
    })),
    audioPlan: {
      guideTrack: designSystem.audio.placeholder,
      finalVoice: designSystem.audio.targetVoice,
      mixNotes: designSystem.audio.mixNotes,
      scriptSource: "script.voiceover"
    },
    captions,
    srt: buildSrt(captions),
    metadata: {
      title: brief.title,
      description: `${brief.objective}\n\nKey points:\n${markdownList(brief.takeaways || [])}`,
      platforms: brief.platforms || [],
      hashtags: ["#videopipeline", "#automation", "#contentops"],
      status: "draft"
    },
    assets: {
      required: ["design_system", "font", "voiceover_placeholder", "platform_profiles"],
      generated: ["animated_text_slates", "guide_audio_bed", "thumbnail", "preview_frame", "sidecar_captions"],
      missingForPublish: ["final_voiceover", "brand_pack", "platform_credentials"]
    },
    qaChecklist: [
      "Script has a hook, supporting points, and close.",
      "Storyboard contains one or more timed scenes.",
      "Captions are present for each scene.",
      "Metadata includes platform targets.",
      "Design brief covers visual, motion, audio, caption, and platform decisions.",
      "Renderer can create a local MP4, thumbnail, and preview frame from this package."
    ],
    renderPlan: {
      size: DEFAULT_SIZE,
      output: `output/videos/${slug}.mp4`,
      thumbnail: `output/thumbnails/${slug}.png`,
      previewFrame: `output/previews/${slug}.png`,
      format: "mp4",
      renderStyle: "vertical text-led motion slates",
      designSource: "package.designBrief"
    }
  };
}

export async function generateDrafts() {
  const briefs = await readJson(fromRoot("content", "briefs.json"));
  const designSystem = await loadDesignSystem();
  await rm(fromRoot("drafts"), { recursive: true, force: true });

  const packages = briefs.map((brief, index) => buildPackage(brief, index, designSystem));

  for (const draftPackage of packages) {
    const draftDir = fromRoot("drafts", draftPackage.slug);
    await writeJson(`${draftDir}/package.json`, draftPackage);
    await writeJson(`${draftDir}/design-brief.json`, draftPackage.designBrief);
    await writeJson(`${draftDir}/storyboard.json`, draftPackage.storyboard);
    await writeJson(`${draftDir}/shot-list.json`, draftPackage.shotList);
    await writeJson(`${draftDir}/motion-plan.json`, draftPackage.motionPlan);
    await writeJson(`${draftDir}/audio-plan.json`, draftPackage.audioPlan);
    await writeJson(`${draftDir}/metadata.json`, draftPackage.metadata);
    await writeJson(`${draftDir}/platform-variants.json`, draftPackage.platformVariants);
    await writeJson(`${draftDir}/render-plan.json`, draftPackage.renderPlan);
    await writeText(`${draftDir}/captions.srt`, draftPackage.srt);
    await writeText(
      `${draftDir}/script.md`,
      `# ${draftPackage.creativeBrief.title}\n\n## Voiceover\n\n${draftPackage.script.voiceover}\n\n## QA Checklist\n\n${markdownList(draftPackage.qaChecklist)}\n`
    );
    await writeText(
      `${draftDir}/production-notes.md`,
      `# Production Notes\n\n## Design Intent\n\n${draftPackage.designBrief.designIntent}\n\n## Theme\n\n${draftPackage.designBrief.theme}\n\n## Platform Variants\n\n${markdownList(draftPackage.platformVariants.map((variant) => `${variant.platform}: ${variant.captionStyle}`))}\n\n## Missing For Publish\n\n${markdownList(draftPackage.assets.missingForPublish)}\n`
    );
  }

  await writeJson(fromRoot("drafts", "index.json"), {
    generatedAt: new Date().toISOString(),
    count: packages.length,
    packages: packages.map((pkg) => ({
      slug: pkg.slug,
      title: pkg.creativeBrief.title,
      durationSeconds: pkg.creativeBrief.durationSeconds,
      renderOutput: pkg.renderPlan.output
    }))
  });

  return packages;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const packages = await generateDrafts();
  console.log(`Generated ${packages.length} draft package(s).`);
}
