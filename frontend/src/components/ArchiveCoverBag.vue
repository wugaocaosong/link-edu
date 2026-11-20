<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';

const props = defineProps({ sceneElement: { type: Object, default: null } });
const emit = defineEmits(['play-video']);
const bag = ref(null);
let resizeObserver;
const phase = ref('idle');
const SOURCE = { width: 1672, height: 941, left: 562, top: 253, bagWidth: 749, bagHeight: 429 };

function placeBag() {
  const scene = props.sceneElement;
  if (!scene || !bag.value) return;

  const sceneRect = scene.getBoundingClientRect();
  const background = scene.querySelector(':scope > img');
  const imageRect = background?.getBoundingClientRect();
  if (!imageRect?.width || !imageRect?.height) return;

  // Match the centered object-fit: cover transform used by the background.
  const sourceWidth = background.naturalWidth || SOURCE.width;
  const sourceHeight = background.naturalHeight || SOURCE.height;
  const pixelRatio = sourceWidth / SOURCE.width;
  const imageScale = Math.max(imageRect.width / sourceWidth, imageRect.height / sourceHeight);
  const scale = imageScale * pixelRatio;
  const renderedWidth = SOURCE.width * scale;
  const renderedHeight = SOURCE.height * scale;
  const cropLeft = (imageRect.width - renderedWidth) / 2;
  const cropTop = (imageRect.height - renderedHeight) / 2;
  bag.value.style.left = `${imageRect.left - sceneRect.left + cropLeft + SOURCE.left * scale}px`;
  bag.value.style.top = `${imageRect.top - sceneRect.top + cropTop + SOURCE.top * scale}px`;
  bag.value.style.width = `${SOURCE.bagWidth * scale}px`;
  bag.value.style.height = `${SOURCE.bagHeight * scale}px`;
}

function openArchive() {
  if (phase.value !== 'idle') return;
  phase.value = 'playing';
  emit('play-video');
}

function onKeydown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    openArchive();
  }
}

onMounted(() => {
  resizeObserver = new ResizeObserver(placeBag);
  if (props.sceneElement) resizeObserver.observe(props.sceneElement);
  placeBag();
});

watch(() => props.sceneElement, (scene, previous) => {
  if (previous) resizeObserver?.unobserve(previous);
  if (scene) resizeObserver?.observe(scene);
  placeBag();
});

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
});
</script>

<template>
  <button ref="bag" type="button" class="archive-cover-bag" :class="`is-${phase}`" aria-label="播放档案袋打开过程" :aria-disabled="phase !== 'idle'" @click="openArchive" @keydown="onKeydown">
    <img src="/assets/archive-cover-object-clean.png" alt="" draggable="false" />
    <img class="archive-cover-thread" src="/assets/archive-cover-thread.png" alt="" draggable="false" aria-hidden="true" />
  </button>
</template>

<style scoped>
.archive-cover-bag {
  position: absolute;
  z-index: 1;
  pointer-events: auto;
  cursor: pointer;
  padding: 0;
  border: 0;
  background: transparent;
  appearance: none;
  transform-style: preserve-3d;
  transform-origin: center 82%;
  transition: filter 220ms ease;
  -webkit-tap-highlight-color: transparent;
}

.archive-cover-bag > img:first-child {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: fill;
  pointer-events: none;
  user-select: none;
}

.archive-cover-bag:hover,
.archive-cover-bag:focus-visible {
  /* Alpha-based shadows illuminate only the cutout perimeter; the paper stays untouched. */
  filter: drop-shadow(0 0 2px #ffd18a)
    drop-shadow(0 0 8px #ffd18acc);
}

.archive-cover-bag:focus-visible {
  outline: none;
}

.archive-cover-bag.is-playing {
  z-index: 6;
  opacity: 0;
  pointer-events: none;
}

.archive-cover-bag > .archive-cover-thread {
  position:absolute;left:35.6475%;top:8.8578%;width:4.8064%;height:8.1585%;
  opacity:1;clip-path:none;transform-origin:50% 0%;
  pointer-events:none;user-select:none;
}
@media (prefers-reduced-motion: reduce) {
  .archive-cover-bag,
  .archive-cover-thread { transition: none; }
}
</style>
