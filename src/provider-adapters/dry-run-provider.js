import path from "node:path";
import { fromRoot } from "../lib/fs-utils.js";

export const DRY_RUN_PROVIDER = {
  id: "dry-run-video-provider",
  mode: "dry_run",
  displayName: "Dry Run Video Provider",
  capabilities: ["text_to_video", "image_reference", "caption_reference", "local_render_fallback"]
};

function relativeRoot(filePath) {
  return path.relative(fromRoot(), fromRoot(filePath));
}

export function buildProviderRequest({ draftPackage, manifest, qualityReport }) {
  return {
    provider: DRY_RUN_PROVIDER.id,
    mode: DRY_RUN_PROVIDER.mode,
    slug: draftPackage.slug,
    title: draftPackage.creativeBrief.title,
    objective: draftPackage.creativeBrief.objective,
    durationSeconds: draftPackage.creativeBrief.durationSeconds,
    aspectRatios: [...new Set(draftPackage.platformVariants.map((variant) => variant.aspectRatio))],
    prompt: {
      voiceover: draftPackage.script.voiceover,
      visualDirection: draftPackage.storyboard.map((scene) => ({
        sceneId: scene.id,
        durationSeconds: scene.durationSeconds,
        title: scene.title,
        body: scene.body,
        motionCue: scene.motionCue,
        visualDirection: scene.visualDirection
      })),
      designTheme: draftPackage.designBrief.theme,
      colorTokens: draftPackage.designBrief.colorTokens,
      audioDirection: draftPackage.audioPlan.finalVoice
    },
    references: {
      localRender: relativeRoot(manifest.outputPath),
      thumbnail: relativeRoot(manifest.thumbnailPath),
      previewFrame: relativeRoot(manifest.previewFramePath),
      captions: `drafts/${draftPackage.slug}/captions.srt`,
      package: `drafts/${draftPackage.slug}/package.json`
    },
    qualityGate: {
      score: qualityReport.score,
      recommendation: qualityReport.recommendation
    }
  };
}

export function submitDryRunProviderJob(request) {
  return {
    provider: DRY_RUN_PROVIDER.id,
    providerJobId: `dryrun_${request.slug}`,
    mode: DRY_RUN_PROVIDER.mode,
    status: "contract_ready",
    submitted: false,
    billable: false,
    cost: {
      estimatedUsd: 0,
      currency: "USD",
      billingStatus: "dry_run_not_billable"
    },
    outputContract: {
      expectedVideoUrl: null,
      expectedStoragePath: `provider-output/${request.slug}/final.mp4`,
      expectedThumbnailUrl: null,
      callbackEvent: "video.render.completed"
    },
    liveIntegrationRequirements: [
      "provider_api_key",
      "provider_job_status_polling",
      "storage_bucket",
      "callback_endpoint",
      "usage_and_cost_ledger"
    ],
    errors: []
  };
}
