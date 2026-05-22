import { generateDrafts } from "./generate-drafts.js";
import { generateOperations } from "./generate-operations.js";
import { generatePublishLedger } from "./generate-publish-ledger.js";
import { generateProviderJobs } from "./generate-provider-jobs.js";
import { generateReviewBoard } from "./generate-review.js";
import { preparePublish } from "./prepare-publish.js";
import { renderVideos } from "./render-videos.js";
import { scoreQuality } from "./score-quality.js";

const packages = await generateDrafts();
console.log(`Phase 1 complete: generated ${packages.length} draft package(s).`);

const renders = await renderVideos();
console.log(`Phase 2 complete: rendered ${renders.length} MP4 video(s).`);

const review = await generateReviewBoard();
console.log(`Design review complete: ${review.reviewPath}`);

const quality = await scoreQuality();
console.log(`Phase 3 complete: scored ${quality.count} package(s), average ${quality.averageScore}.`);

const providerJobs = await generateProviderJobs();
console.log(`Provider dry run complete: generated ${providerJobs.count} job contract(s).`);

const publish = await preparePublish();
console.log(`Phase 4 complete: prepared ${publish.entries.length} dry-run publish payload(s).`);

const publishLedger = await generatePublishLedger();
console.log(`Publish ledger complete: recorded ${publishLedger.count} dry-run ledger entries.`);

const operations = await generateOperations();
console.log(`Phase 5 complete: operations report covers ${operations.summary.drafts} draft(s).`);
