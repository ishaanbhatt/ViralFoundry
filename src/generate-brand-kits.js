import { mkdir, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { fromRoot, readJson, slugify, writeJson, writeText } from "./lib/fs-utils.js";
import { markdownList } from "./lib/text.js";

function requireField(value, message) {
  if (value === undefined || value === null || value === "") {
    throw new Error(message);
  }
}

function normalizeBrandKit(kit, sourceVersion) {
  requireField(kit.name, "Brand kit is missing name");
  requireField(kit.positioning, `${kit.name}: missing positioning`);
  requireField(kit.audience, `${kit.name}: missing audience`);
  requireField(kit.voice, `${kit.name}: missing voice`);
  requireField(kit.visualTokens, `${kit.name}: missing visual tokens`);
  requireField(kit.typography, `${kit.name}: missing typography`);
  requireField(kit.assets, `${kit.name}: missing asset placeholders`);
  requireField(kit.compliance, `${kit.name}: missing compliance notes`);
  requireField(kit.provenance, `${kit.name}: missing provenance`);

  const slug = slugify(kit.id ?? kit.name);
  requireField(slug, `${kit.name}: could not derive slug`);

  return {
    slug,
    name: kit.name,
    positioning: kit.positioning,
    audience: kit.audience,
    voice: kit.voice,
    visualTokens: kit.visualTokens,
    typography: kit.typography,
    assets: kit.assets,
    compliance: kit.compliance,
    provenance: {
      ...kit.provenance,
      sourceVersion
    }
  };
}

function summaryForKit(kit) {
  const voiceTraits = Array.isArray(kit.voice.traits) ? kit.voice.traits.join(", ") : "unspecified";
  const disclosures = Array.isArray(kit.compliance.disclosures) ? kit.compliance.disclosures : [];
  const assetLines = Object.entries(kit.assets)
    .filter(([, value]) => typeof value === "string")
    .map(([key, value]) => `${key}: ${value}`);

  return [
    `## ${kit.name}`,
    "",
    `Slug: \`${kit.slug}\``,
    "",
    `Positioning: ${kit.positioning}`,
    "",
    `Primary audience: ${kit.audience.primary}`,
    "",
    `Voice: ${voiceTraits}`,
    "",
    "### Visual Tokens",
    "",
    markdownList(Object.entries(kit.visualTokens.palette).map(([key, value]) => `${key}: ${value}`)),
    "",
    "### Typography",
    "",
    markdownList([
      `Primary font: ${kit.typography.primaryFont}`,
      `Title: ${kit.typography.title}`,
      `Body: ${kit.typography.body}`,
      `Caption: ${kit.typography.caption}`
    ]),
    "",
    "### Asset Placeholders",
    "",
    markdownList(assetLines),
    "",
    "### Compliance Notes",
    "",
    markdownList(disclosures),
    ""
  ].join("\n");
}

export async function generateBrandKits() {
  const input = await readJson(fromRoot("content", "brand-kits.json"));
  const sourceVersion = input.version ?? "unversioned";
  const kits = (input.brandKits ?? [])
    .map((kit) => normalizeBrandKit(kit, sourceVersion))
    .sort((a, b) => a.slug.localeCompare(b.slug));

  if (kits.length === 0) {
    throw new Error("content/brand-kits.json must include at least one brand kit");
  }

  const duplicateSlug = kits.find((kit, index) => kits.findIndex((candidate) => candidate.slug === kit.slug) !== index);
  if (duplicateSlug) {
    throw new Error(`Duplicate brand kit slug: ${duplicateSlug.slug}`);
  }

  await rm(fromRoot("output", "brand-kits"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "brand-kits"), { recursive: true });

  const entries = [];
  for (const kit of kits) {
    const artifactPath = `output/brand-kits/${kit.slug}.brand-kit.json`;
    await writeJson(fromRoot(artifactPath), kit);
    entries.push({
      slug: kit.slug,
      name: kit.name,
      positioning: kit.positioning,
      mode: kit.provenance.mode,
      artifactPath
    });
  }

  const index = {
    source: "content/brand-kits.json",
    sourceVersion,
    mode: "local_dry_run",
    count: entries.length,
    entries
  };

  await writeJson(fromRoot("output", "brand-kits", "index.json"), index);
  await writeText(
    fromRoot("output", "brand-kits", "brand-kit-summary.md"),
    `# Brand Kits\n\nSource: ${index.source}\nMode: ${index.mode}\n\n${kits.map(summaryForKit).join("\n")}`
  );

  return index;
}

if (fileURLToPath(import.meta.url) === process.argv[1]) {
  const result = await generateBrandKits();
  console.log(`Generated ${result.count} local brand kit artifact(s).`);
}
