import { generateDrafts } from "./generate-drafts.js";
import { generateReviewBoard } from "./generate-review.js";
import { renderVideos } from "./render-videos.js";

const packages = await generateDrafts();
console.log(`Phase 1 complete: generated ${packages.length} draft package(s).`);

const renders = await renderVideos();
console.log(`Phase 2 complete: rendered ${renders.length} MP4 video(s).`);

const review = await generateReviewBoard();
console.log(`Design review complete: ${review.reviewPath}`);
