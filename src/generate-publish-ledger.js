import { mkdir, rm } from "node:fs/promises";
import { fromRoot, readJson, slugify, writeJson, writeText } from "./lib/fs-utils.js";
import { markdownList } from "./lib/text.js";

function ledgerEntryId(entry) {
  return `${entry.slug}-${slugify(entry.platform)}`;
}

function buildLedgerEntry(entry, payload) {
  const blockers = [...new Set(["human_approval", ...payload.readiness.blockers])];
  return {
    id: ledgerEntryId(entry),
    slug: entry.slug,
    platform: entry.platform,
    mode: "dry_run",
    payloadPath: entry.payload,
    idempotencyKey: payload.integrationContract.idempotencyKey,
    requiredCredential: payload.integrationContract.requiredCredential,
    providerJobPath: payload.providerJobPath,
    assetProvenance: payload.assetProvenance,
    upload: {
      status: "not_submitted",
      platformPostId: null,
      platformUrl: null,
      attempts: 0,
      lastAttemptAt: null,
      nextRetryAt: null,
      retryable: false,
      errors: []
    },
    approval: {
      status: "human_approval_required",
      approvedBy: null,
      approvedAt: null,
      blockers
    }
  };
}

function ledgerLine(entry) {
  return `${entry.slug} / ${entry.platform}: ${entry.upload.status}, ${entry.approval.status}, post id ${entry.upload.platformPostId ?? "pending"}`;
}

export async function generatePublishLedger() {
  const publishIndex = await readJson(fromRoot("output", "publish", "index.json"));
  await rm(fromRoot("output", "publish-ledger"), { recursive: true, force: true });
  await mkdir(fromRoot("output", "publish-ledger"), { recursive: true });

  const entries = [];
  for (const entry of publishIndex.entries) {
    const payload = await readJson(fromRoot(entry.payload));
    entries.push(buildLedgerEntry(entry, payload));
  }

  const ledger = {
    generatedAt: new Date().toISOString(),
    mode: "dry_run",
    count: entries.length,
    submittedCount: entries.filter((entry) => entry.upload.status !== "not_submitted").length,
    pendingApprovalCount: entries.filter((entry) => entry.approval.status === "human_approval_required").length,
    entries,
    livePublishingRequirements: [
      "Load platform credentials from the runtime environment.",
      "Require human approval before the first upload attempt.",
      "Persist returned platform IDs and canonical URLs.",
      "Record retry attempts, retry timing, and terminal upload errors.",
      "Keep idempotency keys stable across retries."
    ]
  };

  await writeJson(fromRoot("output", "publish-ledger", "index.json"), ledger);
  await writeText(
    fromRoot("output", "publish-ledger", "publish-ledger.md"),
    `# Publish Ledger\n\nMode: ${ledger.mode}\n\n## Entries\n\n${markdownList(entries.map(ledgerLine))}\n\n## Live Publishing Requirements\n\n${markdownList(ledger.livePublishingRequirements)}\n`
  );
  return ledger;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const ledger = await generatePublishLedger();
  console.log(`Generated ${ledger.count} dry-run publish ledger entr${ledger.count === 1 ? "y" : "ies"}.`);
}
