import { generateDrafts } from "./generate-drafts.js";
import { generateBrandKits } from "./generate-brand-kits.js";
import { generateReviewBoard } from "./generate-review.js";
import { renderVideos } from "./render-videos.js";

const brandKits = await generateBrandKits();
console.log(`Brand kits complete: generated ${brandKits.count} local brand kit artifact(s).`);

const packages = await generateDrafts();
console.log(`Phase 1 complete: generated ${packages.length} draft package(s).`);

const renders = await renderVideos();
console.log(`Phase 2 complete: rendered ${renders.length} MP4 video(s).`);

const review = await generateReviewBoard();
console.log(`Design review complete: ${review.reviewPath}`);
