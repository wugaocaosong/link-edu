<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { gsap } from 'gsap';

const props = defineProps({ sceneElement: { type: Object, default: null } });
const emit = defineEmits(['opened', 'finished']);
const bag = ref(null);
let resizeObserver;
let timeline;
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
  const scale = Math.max(imageRect.width / sourceWidth, imageRect.height / sourceHeight);
  const renderedWidth = sourceWidth * scale;
  const renderedHeight = sourceHeight * scale;
  const cropLeft = (imageRect.width - renderedWidth) / 2;
  const cropTop = (imageRect.height - renderedHeight) / 2;
  bag.value.style.left = `${imageRect.left - sceneRect.left + cropLeft + SOURCE.left * scale}px`;
  bag.value.style.top = `${imageRect.top - sceneRect.top + cropTop + SOURCE.top * scale}px`;
  bag.value.style.width = `${SOURCE.bagWidth * scale}px`;
  bag.value.style.height = `${SOURCE.bagHeight * scale}px`;
}

function openArchive() {
  if (phase.value !== 'idle') return;
  const rect = bag.value?.getBoundingClientRect();
  if (!rect) return;
  const scale = Math.min(window.innerWidth * 0.68 / rect.width, window.innerHeight * 0.68 / rect.height);
  const flyX = window.innerWidth / 2 - (rect.left + rect.width / 2);
  const flyY = window.innerHeight / 2 - (rect.top + rect.height / 2);
  const thread = bag.value.querySelector('.archive-cover-thread');
  gsap.set(thread, { clipPath: 'inset(0% 0% 100% 0%)', transformOrigin: '50% 0%', scaleY: 1, x: 0, y: 0, rotation: 0 });
  phase.value = 'rising';
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const riseDuration = reducedMotion ? 0.25 : 1.8;
  const liftDuration = reducedMotion ? 0.3 : 2.6;
  const openDuration = reducedMotion ? 0.35 : 1.5;
  const threadDuration = reducedMotion ? 0.3 : 3.95;
  const holdDuration = reducedMotion ? 0.2 : 2;

  timeline = gsap.timeline({
    onComplete() {
      phase.value = 'finished';
      gsap.to(bag.value, { opacity: 0, duration: reducedMotion ? 0.1 : 0.9, ease: 'power1.inOut', onComplete: () => emit('finished') });
    },
  });
  timeline
    .to(bag.value, {
      y: -window.innerHeight * 0.055, z: 100, scale: 1.12, rotationX: 12,
      duration: riseDuration, ease: 'power2.inOut', force3D: true,
    })
    .call(() => { phase.value = 'lifting'; })
    .to(bag.value, {
      x: flyX, y: flyY, z: 180, scale, rotationX: 56,
      duration: liftDuration, ease: 'power3.inOut', force3D: true,
    })
    .call(() => { phase.value = 'untying'; })
    .addLabel('unwind')
    .to(bag.value, { rotationX: 0, duration: openDuration, ease: 'power2.inOut' }, 'unwind')
    .to(thread, { clipPath: 'inset(0% 0% 0% 0%)', duration: reducedMotion ? 0.1 : 0.95, ease: 'power1.inOut' }, 'unwind+=0.1')
    .to(thread, { scaleY: 1.65, x: 3, y: 5, duration: reducedMotion ? 0.1 : 1.35, ease: 'power2.inOut' }, 'unwind+=0.8')
    .to(thread, { scaleY: 2.5, x: -8, y: 18, rotation: -9, duration: reducedMotion ? 0.1 : 1.7, ease: 'power2.out' }, 'unwind+=2.15')
    .call(() => { phase.value = 'opened'; }, null, `unwind+=${threadDuration}`)
    .to({}, { duration: holdDuration })
    .call(() => { emit('opened'); });
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
  timeline?.kill();
  gsap.killTweensOf(bag.value);
});
</script>

<template>
  <button ref="bag" type="button" class="archive-cover-bag" :class="`is-${phase}`" aria-label="打开档案袋" :aria-disabled="phase !== 'idle'" @click="openArchive" @keydown="onKeydown">
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

.archive-cover-bag.is-rising,
.archive-cover-bag.is-lifting,
.archive-cover-bag.is-untying,
.archive-cover-bag.is-opened {
  z-index: 6;
  filter: drop-shadow(0 18px 28px #24170c77);
  transform-style: preserve-3d;
}

.archive-cover-bag.is-untying { cursor: default; }

.archive-cover-bag > .archive-cover-thread {
  position:absolute;left:35.6475%;top:8.8578%;width:4.8064%;height:8.1585%;
  opacity:0;clip-path:inset(0% 0% 100% 0%);transform-origin:50% 0%;
  pointer-events:none;user-select:none;
}
.archive-cover-bag.is-untying > .archive-cover-thread,
.archive-cover-bag.is-opened > .archive-cover-thread { opacity:1; }
@media (prefers-reduced-motion: reduce) {
  .archive-cover-bag,
  .archive-cover-thread { transition: none; }
}
</style>
