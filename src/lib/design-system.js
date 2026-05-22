import { fromRoot, readJson } from "./fs-utils.js";

export async function loadDesignSystem() {
  return readJson(fromRoot("content", "design-system.json"));
}

export function pickTheme(designSystem, index) {
  return designSystem.visual.themes[index % designSystem.visual.themes.length];
}

export function platformVariants(brief, designSystem) {
  const platforms = brief.platforms?.length ? brief.platforms : ["YouTube Shorts"];
  return platforms.map((platform) => {
    const profile = designSystem.platforms[platform] || designSystem.platforms["YouTube Shorts"];
    const title = brief.title.slice(0, profile.titleMaxChars);
    return {
      platform,
      aspectRatio: profile.aspectRatio,
      maxDurationSeconds: profile.maxDurationSeconds,
      title,
      captionStyle: profile.captionStyle,
      publishReadiness: "asset-ready, credentials-needed"
    };
  });
}

export function designBriefFor(brief, designSystem, theme) {
  return {
    brand: designSystem.brand.name,
    positioning: designSystem.brand.positioning,
    voice: designSystem.brand.voice,
    theme: theme.name,
    colorTokens: {
      background: theme.background,
      surface: theme.surface,
      foreground: theme.foreground,
      muted: theme.muted,
      accent: theme.accent,
      secondary: theme.secondary
    },
    typography: {
      font: designSystem.visual.font,
      title: "large, direct, high contrast",
      body: "short lines, scan-friendly, never paragraph-dense"
    },
    composition: {
      aspectRatio: "9:16",
      safeArea: designSystem.visual.safeArea,
      density: "single idea per scene"
    },
    motion: designSystem.motion,
    audio: designSystem.audio,
    captions: designSystem.captions,
    designIntent: `Make ${brief.audience} understand ${brief.objective}`
  };
}
