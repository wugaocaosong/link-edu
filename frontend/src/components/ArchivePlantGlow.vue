<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

const props = defineProps({ sceneElement: { type: Object, default: null } });
const overlay = ref(null);
let resizeObserver;

function placeOverlay() {
  const scene = props.sceneElement;
  if (!scene || !overlay.value) return;
  const sceneRect = scene.getBoundingClientRect();
  const background = scene.querySelector(':scope > .archive-scene-base');
  const imageRect = background?.getBoundingClientRect();
  if (!imageRect?.width || !imageRect?.height) return;

  // Keep the source-pixel SVG exactly aligned with the centered object-fit: cover image.
  const sourceWidth = background.naturalWidth || 1672;
  const sourceHeight = background.naturalHeight || 941;
  const designWidth = 1672;
  const designHeight = 941;
  const pixelRatio = sourceWidth / designWidth;
  const imageScale = Math.max(imageRect.width / sourceWidth, imageRect.height / sourceHeight);
  const scale = imageScale * pixelRatio;
  overlay.value.style.left = `${imageRect.left - sceneRect.left + (imageRect.width - designWidth * scale) / 2}px`;
  overlay.value.style.top = `${imageRect.top - sceneRect.top + (imageRect.height - designHeight * scale) / 2}px`;
  overlay.value.style.width = `${designWidth * scale}px`;
  overlay.value.style.height = `${designHeight * scale}px`;
}

onMounted(() => {
  resizeObserver = new ResizeObserver(placeOverlay);
  if (props.sceneElement) resizeObserver.observe(props.sceneElement);
  placeOverlay();
});

watch(() => props.sceneElement, (scene, previous) => {
  if (previous) resizeObserver?.unobserve(previous);
  if (scene) resizeObserver?.observe(scene);
  placeOverlay();
});

onBeforeUnmount(() => resizeObserver?.disconnect());
</script>

<template>
  <svg ref="overlay" class="archive-plant-glow" viewBox="0 0 1672 941" aria-hidden="true">
    <defs>
      <filter id="archive-plant-glow-blur" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="4" />
      </filter>
    </defs>
    <!-- Trace only the visible outside edge: foliage, pot silhouette, and the saucer's exposed rim. -->
    <g class="archive-plant-contour">
      <path class="archive-plant-halo" filter="url(#archive-plant-glow-blur)" d="M 42,0 C 48,14 57,21 69,25 C 77,12 89,9 101,15 C 112,4 127,7 137,19 C 150,8 164,11 176,24 C 189,13 204,14 216,26 C 231,15 246,19 259,32 C 273,20 289,23 302,38 C 317,27 332,30 344,45 C 360,35 376,41 389,57 C 404,48 418,54 429,70 C 441,86 435,100 424,111 C 438,127 435,141 423,152 C 435,167 432,181 420,191 C 432,206 427,219 415,230 C 401,226 385,208 373,192 C 367,210 353,221 340,218 C 326,215 315,198 307,184 C 300,204 286,217 272,218 C 256,216 245,196 237,181 C 230,199 217,212 204,211 C 190,210 178,193 169,177 C 162,196 151,207 138,208 C 123,207 113,191 106,176 C 98,195 87,207 76,207 C 63,203 56,188 52,177 C 43,198 39,220 39,240 C 36,267 44,295 57,316 C 43,311 29,297 20,281 C 12,266 12,249 5,237 C -3,226 -1,212 9,201 C 0,192 1,180 9,169 C 0,158 1,146 11,136 C 2,126 3,112 13,102 C 4,91 6,78 18,68 C 9,58 12,46 23,39 C 16,30 18,18 31,13 C 25,6 31,0 42,0" />
      <path class="archive-plant-edge" d="M 42,0 C 48,14 57,21 69,25 C 77,12 89,9 101,15 C 112,4 127,7 137,19 C 150,8 164,11 176,24 C 189,13 204,14 216,26 C 231,15 246,19 259,32 C 273,20 289,23 302,38 C 317,27 332,30 344,45 C 360,35 376,41 389,57 C 404,48 418,54 429,70 C 441,86 435,100 424,111 C 438,127 435,141 423,152 C 435,167 432,181 420,191 C 432,206 427,219 415,230 C 401,226 385,208 373,192 C 367,210 353,221 340,218 C 326,215 315,198 307,184 C 300,204 286,217 272,218 C 256,216 245,196 237,181 C 230,199 217,212 204,211 C 190,210 178,193 169,177 C 162,196 151,207 138,208 C 123,207 113,191 106,176 C 98,195 87,207 76,207 C 63,203 56,188 52,177 C 43,198 39,220 39,240 C 36,267 44,295 57,316 C 43,311 29,297 20,281 C 12,266 12,249 5,237 C -3,226 -1,212 9,201 C 0,192 1,180 9,169 C 0,158 1,146 11,136 C 2,126 3,112 13,102 C 4,91 6,78 18,68 C 9,58 12,46 23,39 C 16,30 18,18 31,13 C 25,6 31,0 42,0" />
      <path class="archive-plant-halo" filter="url(#archive-plant-glow-blur)" d="M 109,207 C 128,211 151,213 174,213 C 220,213 265,209 310,205 M 109,207 C 99,214 93,225 94,240 C 97,270 101,303 107,332 C 111,350 120,359 140,364 C 174,372 241,371 272,364 C 288,360 297,350 301,332 C 307,301 310,270 311,238 C 312,224 307,213 300,206" />
      <path class="archive-plant-edge" d="M 109,207 C 128,211 151,213 174,213 C 220,213 265,209 310,205 M 109,207 C 99,214 93,225 94,240 C 97,270 101,303 107,332 C 111,350 120,359 140,364 C 174,372 241,371 272,364 C 288,360 297,350 301,332 C 307,301 310,270 311,238 C 312,224 307,213 300,206" />
      <path class="archive-plant-halo" filter="url(#archive-plant-glow-blur)" d="M 111,318 C 100,326 84,332 72,342 C 63,350 67,360 80,369 C 105,385 156,389 211,388 C 267,387 318,377 340,361 C 353,352 353,344 341,338 C 331,332 319,328 312,319" />
      <path class="archive-plant-edge" d="M 111,318 C 100,326 84,332 72,342 C 63,350 67,360 80,369 C 105,385 156,389 211,388 C 267,387 318,377 340,361 C 353,352 353,344 341,338 C 331,332 319,328 312,319" />
      <path class="archive-plant-hit" d="M 42,0 C 47,15 56,23 69,25 C 77,13 89,10 101,15 C 112,4 126,7 137,19 C 149,8 164,11 176,24 C 188,13 203,14 216,26 C 230,15 245,18 259,32 C 272,20 288,23 302,38 C 315,27 331,30 344,45 C 359,35 375,40 389,57 C 403,48 418,54 429,69 C 441,85 435,99 424,111 C 438,126 435,140 423,152 C 435,166 432,180 420,191 C 431,205 427,219 415,230 C 402,226 387,210 373,192 C 366,210 353,220 340,218 C 326,215 315,199 307,184 C 299,204 286,217 272,218 C 256,216 245,196 237,181 C 230,199 217,212 204,211 C 190,210 178,193 169,177 C 162,196 151,207 138,208 C 123,207 113,191 106,176 C 98,195 87,207 76,207 C 64,204 57,190 52,177 C 43,198 39,220 39,240 C 36,269 45,298 57,316 C 42,311 29,297 20,281 C 12,266 13,248 5,237 C -3,226 -1,212 9,201 C 0,192 1,180 9,169 C 0,158 1,146 11,136 C 2,126 3,112 13,102 C 4,91 6,78 18,68 C 9,58 12,46 23,39 C 16,30 18,18 31,13 C 25,6 31,0 42,0 Z M 109,207 C 128,211 151,213 174,213 C 220,213 265,209 310,205 C 318,237 313,296 301,332 C 297,350 288,360 272,364 C 241,371 174,372 140,364 C 120,359 111,350 107,332 C 101,303 97,270 94,240 C 93,225 99,214 109,207 Z M 111,318 C 100,326 84,332 72,342 C 63,350 67,360 80,369 C 105,385 156,389 211,388 C 267,387 318,377 340,361 C 353,352 353,344 341,338 C 331,332 319,328 312,319 C 305,322 296,326 282,330 C 249,340 188,344 145,335 C 130,332 119,327 111,318 Z" />
    </g>
  </svg>
</template>

<style scoped>
.archive-plant-glow {
  position: absolute;
  z-index: 1;
  overflow: visible;
  pointer-events: none;
}

.archive-plant-halo,
.archive-plant-edge {
  fill: none;
  stroke: #ffd18a;
  stroke-linejoin: round;
  stroke-linecap: round;
  opacity: 0;
  transition: opacity 220ms ease;
  pointer-events: none;
}

.archive-plant-halo { stroke-width: 5; }
.archive-plant-edge { stroke-width: 1.5; }

.archive-plant-contour:hover .archive-plant-halo,
.archive-plant-contour:focus-within .archive-plant-halo { opacity: .58; }
.archive-plant-contour:hover .archive-plant-edge,
.archive-plant-contour:focus-within .archive-plant-edge { opacity: .9; }

.archive-plant-hit {
  fill: transparent;
  stroke: transparent;
  pointer-events: visibleFill;
  cursor: default;
}

@media (prefers-reduced-motion: reduce) {
  .archive-plant-halo,
  .archive-plant-edge { transition: none; }
}
</style>
