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
  const scale = Math.max(imageRect.width / sourceWidth, imageRect.height / sourceHeight);
  overlay.value.style.left = `${imageRect.left - sceneRect.left + (imageRect.width - sourceWidth * scale) / 2}px`;
  overlay.value.style.top = `${imageRect.top - sceneRect.top + (imageRect.height - sourceHeight * scale) / 2}px`;
  overlay.value.style.width = `${sourceWidth * scale}px`;
  overlay.value.style.height = `${sourceHeight * scale}px`;
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
    <path class="archive-plant-halo" filter="url(#archive-plant-glow-blur)" d="M 0,0 L 38,0 Q 44,18 63,27 Q 82,11 99,15 Q 115,2 137,17 Q 157,5 174,21 Q 198,8 216,23 Q 239,11 258,28 Q 283,14 302,32 Q 328,17 344,37 Q 374,24 390,49 Q 416,35 434,64 Q 450,88 432,111 Q 452,136 429,160 Q 445,180 428,201 Q 442,226 424,244 Q 435,263 414,277 Q 397,293 373,278 Q 355,298 334,282 L 311,305 Q 306,327 304,347 Q 301,368 282,376 Q 254,386 223,383 L 132,380 Q 106,378 91,361 Q 82,349 79,330 Q 63,314 50,298 Q 37,278 27,256 Q 16,229 0,214 Z" />
    <path class="archive-plant-edge" d="M 0,0 L 38,0 Q 44,18 63,27 Q 82,11 99,15 Q 115,2 137,17 Q 157,5 174,21 Q 198,8 216,23 Q 239,11 258,28 Q 283,14 302,32 Q 328,17 344,37 Q 374,24 390,49 Q 416,35 434,64 Q 450,88 432,111 Q 452,136 429,160 Q 445,180 428,201 Q 442,226 424,244 Q 435,263 414,277 Q 397,293 373,278 Q 355,298 334,282 L 311,305 Q 306,327 304,347 Q 301,368 282,376 Q 254,386 223,383 L 132,380 Q 106,378 91,361 Q 82,349 79,330 Q 63,314 50,298 Q 37,278 27,256 Q 16,229 0,214 Z" />
    <path class="archive-plant-hit" tabindex="0" role="img" aria-label="盆栽" d="M 0,0 L 38,0 Q 44,18 63,27 Q 82,11 99,15 Q 115,2 137,17 Q 157,5 174,21 Q 198,8 216,23 Q 239,11 258,28 Q 283,14 302,32 Q 328,17 344,37 Q 374,24 390,49 Q 416,35 434,64 Q 450,88 432,111 Q 452,136 429,160 Q 445,180 428,201 Q 442,226 424,244 Q 435,263 414,277 Q 397,293 373,278 Q 355,298 334,282 L 311,305 Q 306,327 304,347 Q 301,368 282,376 Q 254,386 223,383 L 132,380 Q 106,378 91,361 Q 82,349 79,330 Q 63,314 50,298 Q 37,278 27,256 Q 16,229 0,214 Z" />
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
  opacity: 0;
  transition: opacity 220ms ease;
  pointer-events: none;
}

.archive-plant-halo { stroke-width: 8; }
.archive-plant-edge { stroke-width: 2; }

.archive-plant-glow:hover .archive-plant-halo,
.archive-plant-glow:focus-within .archive-plant-halo { opacity: .68; }
.archive-plant-glow:hover .archive-plant-edge,
.archive-plant-glow:focus-within .archive-plant-edge { opacity: .95; }

.archive-plant-hit {
  fill: transparent;
  stroke: transparent;
  pointer-events: visibleFill;
  cursor: pointer;
}

.archive-plant-hit:focus { outline: none; }

@media (prefers-reduced-motion: reduce) {
  .archive-plant-halo,
  .archive-plant-edge { transition: none; }
}
</style>
