<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  item: { type: Object, required: true },
  active: { type: Boolean, default: false },
});

const emit = defineEmits(["activate", "open"]);
const cardRef = ref(null);
const triggerRef = ref(null);
const offset = ref({ x: 0, y: 0 });
const dragging = ref(false);
const thumbFailed = ref(false);
let gesture = null;
let suppressClick = false;

const cardStyle = computed(() => ({
  left: `${props.item.position.left}%`,
  bottom: `${props.item.position.bottom}%`,
  zIndex: props.active ? 30 : props.item.position.z,
  transform: `translate3d(${offset.value.x}px, ${offset.value.y}px, 0) rotate(${dragging.value ? 0 : props.item.position.rotate}deg)`,
}));

const showCoverPreview = computed(() => !["envelope", "linen"].includes(props.item.position.surface));
const showSheetCover = computed(() => Boolean(props.item.sheetCover));
const previewImage = computed(() => {
  if (props.item.readType === "pdf") return props.item.thumbnail;
  if (props.item.readType === "image") return props.item.boardImage || props.item.thumbnail;
  return "";
});
const showThumbnail = computed(() => Boolean(previewImage.value) && !thumbFailed.value && !showSheetCover.value);
const showFileCover = computed(() => showSheetCover.value || showThumbnail.value);

function pointerDown(event) {
  if (event.button !== 0) return;
  const card = cardRef.value;
  const board = card?.parentElement;
  if (!card || !board) return;
  const rect = card.getBoundingClientRect();
  const boardRect = board.getBoundingClientRect();
  card.setPointerCapture(event.pointerId);
  emit("activate", props.item.id);
  dragging.value = true;
  gesture = {
    pointerId: event.pointerId,
    startX: event.clientX,
    startY: event.clientY,
    originX: offset.value.x,
    originY: offset.value.y,
    minX: boardRect.left + 12 - rect.left,
    maxX: boardRect.right - 12 - rect.right,
    minY: boardRect.top + 12 - rect.top,
    maxY: boardRect.bottom - 12 - rect.bottom,
    moved: false,
  };
}

function pointerMove(event) {
  if (!gesture || gesture.pointerId !== event.pointerId) return;
  const dx = event.clientX - gesture.startX;
  const dy = event.clientY - gesture.startY;
  if (Math.hypot(dx, dy) > 5) gesture.moved = true;
  if (!gesture.moved) return;
  const clamp = (value, min, max) => Math.min(Math.max(value, min), max);
  offset.value = {
    x: gesture.originX + clamp(dx, gesture.minX, gesture.maxX),
    y: gesture.originY + clamp(dy, gesture.minY, gesture.maxY),
  };
}

function pointerUp(event) {
  if (!gesture || gesture.pointerId !== event.pointerId) return;
  suppressClick = gesture.moved;
  gesture = null;
  dragging.value = false;
  cardRef.value?.releasePointerCapture?.(event.pointerId);
  if (suppressClick) window.setTimeout(() => (suppressClick = false), 0);
}

function openCard() {
  if (suppressClick) return;
  triggerRef.value?.focus({ preventScroll: true });
  emit("open", props.item);
}
</script>

<template>
  <div
    ref="cardRef"
    class="draggable-resource-card"
    :class="{
      'is-dragging': dragging,
      'is-recommended': item.recommended,
      'has-file-cover': showFileCover,
      [`surface-${item.position.surface}`]: item.position.surface,
      [`cover-${item.cover}`]: item.cover,
    }"
    :style="cardStyle"
    @click="openCard"
    @pointerdown="pointerDown"
    @pointermove="pointerMove"
    @pointerup="pointerUp"
    @pointercancel="pointerUp"
    @dragstart.prevent
  >
    <button
      ref="triggerRef"
      type="button"
      class="shelf-card-trigger"
      :aria-label="`查看${item.title}`"
    ></button>
    <span class="resource-card-depth">
      <img
        class="shelf-prop-image"
        :src="`/assets/desk/props/${item.position.surface}.webp`"
        alt=""
        aria-hidden="true"
        draggable="false"
      />
      <!-- ① 牛皮纸档案袋：翻盖 + 纽扣 + 标题签 + 推荐黄标 -->
      <template v-if="item.position.surface === 'envelope'">
        <span class="env-flap" aria-hidden="true"></span>
        <span class="env-button" aria-hidden="true"></span>
        <span class="obj-paper">
          <em>{{ item.category }}</em>
          <strong>{{ item.title }}</strong>
          <small>{{ item.source }} · {{ item.year }}</small>
        </span>
        <small v-if="item.recommended" class="obj-tag obj-tag--gold">推荐</small>
      </template>

      <!-- ② 绿色布面笔记本：烫叶纹 + 压印标题 -->
      <template v-else-if="item.position.surface === 'linen'">
        <span class="cloth-leaf" aria-hidden="true"></span>
        <span class="obj-paper obj-paper--cloth">
          <em>{{ item.coverLabel }}</em>
          <strong>{{ item.title }}</strong>
          <small>{{ item.source }} · {{ item.year }}</small>
        </span>
      </template>

      <!-- ③ 翻开的线圈本：左微黄 / 右阴影 + PDF 标 + 彩色索引贴 -->
      <template v-else-if="item.position.surface === 'binder'">
        <span class="spiral" aria-hidden="true"></span>
        <span class="bk-page bk-page--left">
          <em>{{ item.coverLabel }}</em>
          <strong>{{ item.title }}</strong>
          <span class="bk-lines" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
        </span>
        <span class="bk-page bk-page--right" aria-hidden="true">
          <span class="bk-print">
            <em>{{ item.coverLabel }}</em>
            <strong>{{ item.title }}</strong>
          </span>
          <span class="bk-figure"></span>
          <span class="bk-lines"><i></i><i></i><i></i></span>
        </span>
        <span class="obj-tag obj-tag--pdf">{{ item.format.split(' / ')[0] }}</span>
        <span class="index-tabs" aria-hidden="true"><i></i><i></i><i></i></span>
      </template>

      <!-- ④ 摊开的图卡册：左侧文字列表 + 右侧思维导图 -->
      <template v-else-if="item.position.surface === 'folio'">
        <span class="folio-spine" aria-hidden="true"></span>
        <span class="folio-page folio-page--left">
          <b>{{ item.sheetCover?.title || item.title }}</b>
          <span v-for="(line, index) in item.sheetCover?.lines" :key="index" class="folio-line">{{ line }}</span>
          <span v-if="!item.sheetCover?.lines?.length" class="folio-line folio-description">{{ item.description }}</span>
        </span>
        <span class="folio-page folio-page--right" aria-hidden="true">
          <span class="mindmap">
            <i class="mindmap__root">{{ item.id === 'info-knowledge' ? '数据' : '资料' }}</i>
            <i class="mindmap__node n1">{{ item.id === 'info-knowledge' ? '信息' : item.format.split(' / ')[0].split(' · ')[0] }}</i>
            <i class="mindmap__node n2">{{ item.id === 'info-knowledge' ? '知识' : item.category }}</i>
            <i class="mindmap__node n3">{{ item.id === 'info-knowledge' ? '加工' : '查看' }}</i>
            <i class="mindmap__line l1"></i><i class="mindmap__line l2"></i><i class="mindmap__line l3"></i>
          </span>
        </span>
        <small class="obj-tag obj-tag--course">{{ item.category }}</small>
      </template>

      <!-- ⑤ 蓝色活页夹：天蓝封面 + 黑板图案 + 课程资源标签 -->
      <template v-else>
        <span class="folder-clip" aria-hidden="true"></span>
        <span class="chalkboard" aria-hidden="true"><i></i><i></i></span>
        <span class="obj-paper obj-paper--folder">
          <em>{{ item.coverLabel || '课程资源' }}</em>
          <strong>{{ item.title }}</strong>
          <small>{{ item.source }} · {{ item.year }}</small>
        </span>
        <small class="obj-tag obj-tag--course">{{ item.category }}</small>
      </template>
    </span>
  </div>
</template>

<style scoped>
/* ============================================================
   拟物化纸品：5 件物件散落在绿色毛毡桌垫上。
   位置/旋转/拖拽偏移写在内联 transform（脚本控制），
   hover 只用 scale 属性，避免和内联 transform 打架。
   ============================================================ */
.draggable-resource-card {
  position: absolute;
  width: min(18%, 244px);
  min-height: 262px;
  padding: 0;
  border: 0;
  background: transparent;
  color: #2b2118;
  text-align: left;
  touch-action: none;
  user-select: none;
  cursor: grab;
  transform-style: preserve-3d;
}

/* 摊开的两本书要更宽的画布，两页才不会挤成细条（宽度相对 deck 算） */
.draggable-resource-card.surface-binder { width: min(31%, 365px); }
.draggable-resource-card.surface-folder { width: min(17%, 218px); }
.draggable-resource-card.surface-folio { width: min(40%, 470px); min-height: 0; }

.draggable-resource-card.is-dragging {
  cursor: grabbing;
  filter: drop-shadow(0 38px 42px rgba(6, 12, 6, .6));
}

.draggable-resource-card:focus-visible {
  outline: 3px solid #ffe7aa;
  outline-offset: 5px;
  border-radius: 10px;
}

.resource-card-depth {
  position: relative;
  display: block;
  width: 100%;
  height: 100%;
  min-height: inherit;
}

/* 共享：物件上的纸质标签 / 小色签 ================================== */
.obj-paper {
  position: absolute;
  display: grid;
  align-content: center;
  gap: 6px;
}

.obj-paper em {
  font-size: 9px;
  font-style: normal;
  font-weight: 700;
  letter-spacing: .14em;
  text-transform: uppercase;
  opacity: .7;
}

.obj-paper strong {
  font-family: "Songti SC", "Noto Serif CJK SC", "STSong", serif;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.42;
}

.obj-paper small {
  font-size: 9px;
  opacity: .62;
}

.obj-tag {
  position: absolute;
  z-index: 6;
  display: inline-block;
  padding: 4px 9px;
  border-radius: 4px;
  font-size: 10px;
  font-style: normal;
  font-weight: 800;
  letter-spacing: .05em;
  white-space: nowrap;
  box-shadow: 1px 2px 0 rgba(60, 30, 10, .3);
}

.obj-tag--gold {
  left: 12px;
  bottom: 14px;
  color: #4a2f14;
  background: linear-gradient(150deg, #efd6a1, #d2ad76);
  border: 1px solid rgba(120, 70, 20, .38);
  transform: rotate(-4deg);
}

.obj-tag--pdf {
  right: -8px;
  top: 14px;
  color: #fff;
  background: linear-gradient(155deg, #a17c8d, #79576b);
  border: 1px solid rgba(90, 20, 10, .4);
  transform: rotate(3deg);
}

.obj-tag--course {
  left: 14px;
  bottom: 14px;
  color: #23405c;
  background: linear-gradient(150deg, #e5d5db, #cbb4c7);
  border: 1px solid rgba(40, 90, 140, .35);
  transform: rotate(-2deg);
}

/* ① 牛皮纸档案袋 ================================================== */
.surface-envelope .resource-card-depth {
  border-radius: 5px 5px 9px 9px;
  background:
    linear-gradient(112deg, rgba(255, 245, 216, .5), transparent 42%),
    repeating-linear-gradient(94deg, rgba(120, 74, 30, .045) 0 1px, transparent 1px 4px),
    linear-gradient(165deg, #eacb9d, #d8ae76 60%, #c99a61);
  box-shadow:
    inset 0 0 0 1px rgba(120, 74, 30, .28),
    inset 0 10px 18px rgba(255, 244, 214, .28),
    3px 5px 0 -1px #a97e4d,
    7px 12px 0 -3px #e3c69b,
    -12px 19px 24px #30201780;
}

/* 翻盖：顶部的三角折片 */
.env-flap {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 92px;
  z-index: 3;
  border-radius: 5px 5px 46% 46% / 5px 5px 22% 22%;
  background:
    linear-gradient(160deg, #f4dcb2, #e2bd8b 72%, #d6ac78);
  box-shadow: 0 4px 6px rgba(94, 56, 20, .32), inset 0 -2px 3px rgba(120, 74, 30, .16);
  clip-path: polygon(0 0, 100% 0, 100% 62%, 50% 100%, 0 62%);
}

.env-flap::after {
  content: '';
  position: absolute;
  inset: 0;
  clip-path: polygon(0 62%, 50% 100%, 100% 62%, 100% 68%, 50% 100%, 0 68%);
  background: rgba(92, 56, 22, .2);
}

/* 黄铜纽扣 + 绕线 */
.env-button {
  position: absolute;
  top: 76px;
  left: 50%;
  width: 30px;
  height: 30px;
  z-index: 5;
  transform: translateX(-50%);
  border-radius: 50%;
  background:
    radial-gradient(circle at 40% 34%, #fff0c8 0 6%, #e0a94f 18%, #a8701f 62%, #6f4512 100%);
  box-shadow:
    0 2px 3px rgba(60, 34, 10, .55),
    inset 0 0 0 2px rgba(255, 230, 170, .45),
    inset 0 -3px 5px rgba(70, 40, 10, .4);
}

.env-button::after {
  content: '';
  position: absolute;
  inset: 9px;
  border-radius: 50%;
  border: 1.5px solid rgba(96, 58, 16, .55);
  box-shadow: inset 0 1px 2px rgba(60, 34, 10, .5);
}

.surface-envelope .obj-paper {
  left: 14px;
  right: 14px;
  top: 122px;
  padding: 13px 12px 15px;
  border-radius: 3px;
  background: linear-gradient(152deg, #fffdf3, #f5e9ce);
  box-shadow: 0 1px 0 rgba(90, 56, 22, .14), inset 0 0 0 1px rgba(120, 74, 30, .16);
  transform: rotate(-1deg);
}

/* ② 绿色布面笔记本 ================================================ */
.surface-linen .resource-card-depth {
  border-radius: 6px 12px 10px 6px;
  background:
    linear-gradient(90deg, rgba(20, 34, 18, .5), transparent 14px, rgba(240, 248, 214, .14) 15px, transparent 18px),
    repeating-linear-gradient(112deg, rgba(255, 255, 220, .04) 0 1px, transparent 1px 3px),
    repeating-linear-gradient(22deg, rgba(18, 32, 16, .05) 0 2px, transparent 2px 5px),
    linear-gradient(150deg, #89945f, #687c4e 54%, #4a5e3c);
  box-shadow:
    inset 0 0 0 2px rgba(226, 236, 190, .28),
    inset 5px 0 10px rgba(16, 28, 12, .4),
    3px 5px 0 #2f3f25,
    6px 10px 0 -2px #7c8b57,
    -11px 17px 24px #2f201780;
}

/* 烫金叶片 */
.cloth-leaf {
  position: absolute;
  top: 34px;
  left: 50%;
  width: 70px;
  height: 92px;
  transform: translateX(-50%) rotate(-28deg);
  border-radius: 70% 0 70% 0;
  background:
    repeating-linear-gradient(48deg, transparent 0 9px, rgba(232, 214, 150, .26) 10px 11px),
    linear-gradient(135deg, rgba(236, 220, 158, .32), rgba(180, 160, 96, .12));
  box-shadow: inset 0 0 0 1.5px rgba(238, 220, 154, .5);
}

.cloth-leaf::after {
  content: '';
  position: absolute;
  top: 8%;
  left: 50%;
  width: 1.5px;
  height: 88%;
  background: rgba(238, 220, 154, .5);
  transform: rotate(45deg);
  transform-origin: top center;
}

.surface-linen .obj-paper--cloth {
  left: 14px;
  right: 14px;
  bottom: 22px;
  padding: 12px 10px;
  border-radius: 2px;
  color: #33402a;
  background: linear-gradient(150deg, #f9f1d6, #e7dfb8);
  box-shadow: 0 2px 4px rgba(14, 24, 10, .35), inset 0 0 0 1px rgba(80, 96, 52, .22);
}

/* ③ 翻开的线圈本 ================================================== */
.surface-binder .resource-card-depth {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  padding: 12px 8px;
  border-radius: 6px 9px 9px 6px;
  background: linear-gradient(90deg, #8a7256, #a68b68 4%, #a68b68 96%, #715c44);
  box-shadow:
    3px 5px 0 #5c4a37,
    6px 10px 0 -2px #c9ae8b,
    -10px 16px 24px #30201778;
}

/* 书脊中缝 */
.surface-binder .resource-card-depth::before {
  content: '';
  position: absolute;
  top: 6px;
  bottom: 6px;
  left: 50%;
  width: 16px;
  transform: translateX(-50%);
  z-index: 1;
  pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(66, 48, 30, .34) 40% 60%, transparent);
}

/* 线圈：沿中缝的一排金属圈 */
.spiral {
  position: absolute;
  top: 14px;
  bottom: 14px;
  left: 50%;
  width: 22px;
  z-index: 7;
  transform: translateX(-50%);
  pointer-events: none;
  background: radial-gradient(ellipse at 48% 44%, transparent 0 31%, #59432f 35% 42%, #cfab74 47% 52%, #fff0cb 56%, #9b7750 61%, transparent 66%) center top / 22px 26px repeat-y;
}

.bk-page {
  position: relative;
  display: grid;
  align-content: start;
  gap: 8px;
  min-height: 218px;
  padding: 18px 12px;
  border-radius: 3px 5px 5px 3px;
}

.bk-page--left {
  background:
    linear-gradient(90deg, rgba(140, 110, 70, .12), transparent 22%),
    repeating-linear-gradient(0deg, transparent 0 23px, #b79d752b 24px, transparent 25px),
    #fdf6e4;
  box-shadow: inset -8px 0 12px -8px rgba(96, 70, 40, .3), inset 0 0 0 1px rgba(160, 130, 90, .2);
}

.bk-page--right {
  background:
    linear-gradient(90deg, rgba(96, 70, 40, .22), transparent 30%),
    linear-gradient(#f3ead4, #e9dec4);
  box-shadow: inset 8px 0 14px -8px rgba(70, 48, 26, .45), inset 0 0 0 1px rgba(150, 120, 80, .2);
}

.bk-page em {
  font-size: 9px;
  font-style: normal;
  font-weight: 700;
  letter-spacing: .1em;
  color: #8a5a32;
}

.bk-page strong {
  font-family: "Songti SC", "Noto Serif CJK SC", serif;
  font-size: 14px;
  line-height: 1.44;
  color: #3d2d1f;
}

.bk-lines {
  display: grid;
  gap: 7px;
  margin-top: 6px;
}

.bk-lines i {
  height: 4px;
  border-radius: 2px;
  background: rgba(120, 92, 58, .2);
}

.bk-lines i:nth-child(2) { width: 88%; }
.bk-lines i:nth-child(3) { width: 94%; }
.bk-lines i:nth-child(4) { width: 66%; }

.bk-figure {
  height: 74px;
  margin: 8px 0 4px;
  border-radius: 6px;
  background:
    radial-gradient(circle at 24% 40%, #b08bbf 0 8px, transparent 9px),
    radial-gradient(circle at 72% 28%, #a8bf7e 0 7px, transparent 8px),
    radial-gradient(circle at 60% 74%, #e0b56e 0 9px, transparent 10px),
    repeating-linear-gradient(28deg, transparent 0 12px, rgba(120, 92, 58, .14) 13px 14px);
}

.index-tabs {
  position: absolute;
  top: 40px;
  right: -9px;
  z-index: 5;
  display: grid;
  gap: 5px;
}

.index-tabs i {
  display: block;
  width: 20px;
  height: 12px;
  border-radius: 0 3px 3px 0;
  box-shadow: 1px 1px 2px rgba(50, 30, 15, .3);
}

.index-tabs i:nth-child(1) { background: #b58ac4; }
.index-tabs i:nth-child(2) { background: #e7c267; }
.index-tabs i:nth-child(3) { background: #9dbb76; }

/* ④ 摊开的图卡册 ================================================== */
.surface-folio .resource-card-depth {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  min-height: 185px;
  padding: 10px;
  border-radius: 8px;
  background: linear-gradient(90deg, #7a6248, #b2976f 3%, #b2976f 97%, #6f5942);
  box-shadow:
    4px 6px 0 #4f3f2d,
    8px 13px 0 -2px #cdb28c,
    -9px 13px 20px #35251b70;
}

.folio-spine {
  position: absolute;
  top: 8px;
  bottom: 8px;
  left: 50%;
  width: 18px;
  transform: translateX(-50%);
  z-index: 1;
  pointer-events: none;
  background: linear-gradient(90deg, transparent, rgba(70, 48, 26, .42) 42% 58%, transparent);
}

.folio-page {
  position: relative;
  display: grid;
  align-content: start;
  gap: 7px;
  min-height: 166px;
  padding: 16px 13px;
  border-radius: 3px 5px 5px 3px;
}

.folio-page--left {
  background: linear-gradient(90deg, rgba(140, 110, 70, .14), transparent 20%), #fffbef;
  box-shadow: inset -8px 0 12px -8px rgba(90, 64, 36, .34), inset 0 0 0 1px rgba(160, 130, 90, .22);
}

.folio-page--right {
  background: linear-gradient(90deg, rgba(90, 64, 36, .24), transparent 26%), linear-gradient(#f6eedb, #ece1c8);
  box-shadow: inset 8px 0 14px -8px rgba(70, 48, 26, .5), inset 0 0 0 1px rgba(150, 120, 80, .2);
}

.surface-folio .resource-card-depth {
  font-family: "Microsoft YaHei UI", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  letter-spacing: normal;
}

.surface-folio .obj-tag {
  letter-spacing: normal;
}

.folio-page b {
  font-size: 13px;
  font-weight: 600;
  line-height: 1.4;
  color: #3a2b1e;
  padding-bottom: 6px;
  border-bottom: 1.5px solid rgba(120, 88, 50, .4);
  margin-bottom: 3px;
}

.folio-line {
  font-size: 10px;
  line-height: 1.65;
  color: #5a4632;
}

.folio-description {
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 4;
}

/* 思维导图占位 */
.mindmap {
  position: relative;
  display: block;
  height: 166px;
  margin-top: 6px;
}

.mindmap__root,
.mindmap__node {
  position: absolute;
  display: grid;
  place-items: center;
  border-radius: 999px;
  font-size: 10px;
  font-style: normal;
  font-weight: 600;
  box-shadow: 0 2px 3px rgba(70, 48, 26, .3), inset 0 1px rgba(255, 255, 255, .5);
}

.mindmap__root {
  left: 6px;
  top: 72px;
  width: 54px;
  height: 40px;
  color: #fff;
  background: linear-gradient(#7c9c5c, #57763e);
}

.mindmap__node.n1 { right: 0; top: 14px; width: 58px; height: 32px; color: #5a3a70; background: linear-gradient(#d9c6e6, #bd9fcf); }
.mindmap__node.n2 { right: 0; top: 74px; width: 58px; height: 32px; color: #7a5416; background: linear-gradient(#f2d99b, #ddba68); }
.mindmap__node.n3 { right: 0; top: 122px; width: 58px; height: 32px; color: #2f5a3a; background: linear-gradient(#bcdaa2, #93bc74); }

.mindmap__line {
  position: absolute;
  left: 58px;
  width: max(0px, calc(100% - 113px));
  height: 2px;
  background: rgba(120, 88, 50, .42);
  transform-origin: left center;
}

.mindmap__line.l1 { top: 84px; transform: rotate(-26deg); }
.mindmap__line.l2 { top: 92px; }
.mindmap__line.l3 { top: 100px; transform: rotate(26deg); }

/* ⑤ 蓝色活页夹 ==================================================== */
.surface-folder .resource-card-depth {
  border-radius: 7px 13px 11px 7px;
  background:
    linear-gradient(90deg, rgba(12, 44, 74, .42), transparent 15px, rgba(255, 255, 255, .2) 16px, transparent 19px),
    repeating-linear-gradient(118deg, rgba(255, 255, 255, .05) 0 1px, transparent 1px 4px),
    linear-gradient(155deg, #c1c6ce, #9da9b4 58%, #768592);
  box-shadow:
    inset 0 0 0 1px rgba(30, 74, 110, .3),
    inset 4px 0 8px rgba(18, 54, 88, .3),
    3px 5px 0 #547584,
    6px 10px 0 -2px #eef0db,
    -10px 16px 24px #30201778;
}

/* 顶部的金属活页夹 */
.folder-clip {
  position: absolute;
  top: -6px;
  left: 50%;
  width: 56px;
  height: 26px;
  z-index: 6;
  transform: translateX(-50%);
  border-radius: 5px 5px 3px 3px;
  background: linear-gradient(#f2f4f5, #b9c2c8 55%, #7f8a91);
  box-shadow: 0 3px 4px rgba(20, 40, 60, .4), inset 0 1px rgba(255, 255, 255, .8);
}

.folder-clip::after {
  content: '';
  position: absolute;
  left: 8px;
  right: 8px;
  bottom: 4px;
  height: 3px;
  border-radius: 2px;
  background: rgba(40, 60, 76, .5);
}

/* 黑板图案 */
.chalkboard {
  position: absolute;
  top: 46px;
  left: 50%;
  width: 76%;
  height: 118px;
  transform: translateX(-50%) rotate(-1.5deg);
  border: 6px solid #b98a4e;
  border-radius: 6px;
  background:
    radial-gradient(ellipse at 28% 18%, rgba(255, 255, 255, .08), transparent 40%),
    linear-gradient(150deg, #35513c, #22392b);
  box-shadow: 0 4px 8px rgba(18, 40, 60, .45), inset 0 0 16px rgba(0, 0, 0, .4);
}

.chalkboard i {
  position: absolute;
  left: 18%;
  height: 3px;
  border-radius: 2px;
  background: rgba(240, 248, 236, .5);
}

.chalkboard i:nth-of-type(1) { top: 56px; width: 64%; }
.chalkboard i:nth-of-type(2) { top: 70px; width: 46%; }

.surface-folder .obj-paper--folder {
  left: 12px;
  right: 12px;
  bottom: 18px;
  padding: 10px;
  border-radius: 3px;
  color: #23405c;
  background: linear-gradient(#fbfdff, #e6f1fa);
  box-shadow: 0 2px 4px rgba(18, 48, 74, .3), inset 0 0 0 1px rgba(60, 110, 150, .25);
}

/* 移动端：卡片转普通流，物件缩小、摊开本改单列 ==================== */
.surface-envelope .resource-card-depth::after,
.surface-linen .resource-card-depth::after {
  content: '';
  position: absolute;
  inset: 6px;
  border-radius: inherit;
  border: 1px solid #ffe9b763;
  box-shadow: inset 0 0 0 1px #382a1617;
  pointer-events: none;
}

.surface-linen .obj-paper--cloth {
  border: 1px solid #9c8b5880;
  outline: 1px solid #9c8b5840;
  outline-offset: -5px;
}

.surface-linen .resource-card-depth::before {
  content: '';
  position: absolute;
  right: 17%;
  bottom: -8px;
  width: 11px;
  height: 21px;
  clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 77%, 0 100%);
  background: linear-gradient(90deg, #785b71, #b08da4);
  box-shadow: 0 2px 3px #33252b;
}

.folio-page--left {
  background:
    linear-gradient(90deg, #b2956c24, transparent 24%),
    repeating-linear-gradient(0deg, transparent 0 16px, #9e815312 17px, transparent 18px),
    #fcf5e5;
}

.obj-tag {
  border-radius: 2px 4px 4px 2px;
  box-shadow: -1px 2px 3px #4b2d2549, inset 0 1px #fff2d880;
}

.surface-envelope .resource-card-depth {
  background: linear-gradient(130deg, #f6cca1, #d9a575);
}

.surface-envelope .env-flap { opacity: .24; height: 70px; }
.surface-envelope .env-button { top: 18px; width: 15px; height: 15px; }
.surface-envelope .env-button::after { inset: 4px; }

.surface-envelope .obj-paper,
.surface-linen .obj-paper--cloth {
  top: 23%;
  bottom: auto;
  padding: 14px 10px;
  text-align: center;
  background: linear-gradient(150deg, #fff4e5, #eed7be);
}

.surface-linen .resource-card-depth {
  background:
    linear-gradient(90deg, #253c31a6, transparent 10%, #b4b29c24 11%, transparent 13%),
    linear-gradient(155deg, #718772, #354e42);
}

.surface-linen .cloth-leaf { top: 59%; left: 37%; }
.surface-folder .resource-card-depth { background: linear-gradient(135deg, #d1d6d7, #869ca9); }
.surface-folder .chalkboard {
  inset: 13% 7% 8%;
  width: auto;
  height: auto;
  transform: none;
  border: 1px solid #455158;
  background: linear-gradient(150deg, #565453, #313632);
  box-shadow: inset 0 2px 8px #191c1d80;
}
.surface-folder .chalkboard i { display: none; }
.surface-folder .obj-paper--folder {
  top: 32%;
  bottom: auto;
  left: 13%;
  right: 13%;
  background: linear-gradient(140deg, #fff2e5, #e3cdb8);
  color: #453329;
  text-align: center;
}

.surface-folio .obj-tag--course,
.surface-folder .obj-tag--course {
  background: linear-gradient(145deg, #b58aac, #916788);
  color: #241828;
}

.shelf-prop-image, .bk-print { display: none; }

@media (min-width: 901px) {
  .draggable-resource-card,
  .draggable-resource-card.surface-folio,
  .draggable-resource-card.surface-folder {
    min-height: 0;
  }

  .draggable-resource-card { width: 20%; }
  .draggable-resource-card.surface-binder { width: 31%; }

  /* Keep themed button treatments off the transparent image bounds. */
  .draggable-resource-card:is(:hover, :focus, :active, .is-dragging),
  .draggable-resource-card {
    border: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    outline: none !important;
  }

  .draggable-resource-card:focus-visible .shelf-prop-image {
    filter: drop-shadow(0 0 3px #fff2b3) drop-shadow(0 0 4px #f4d093);
  }
  .draggable-resource-card.surface-folio { width: 43%; }
  .draggable-resource-card.surface-folder { width: 22%; }

  .draggable-resource-card .resource-card-depth {
    display: block;
    height: auto;
    min-height: 0;
    padding: 0;
    border: 0;
    background: none;
    box-shadow: none;
  }

  .draggable-resource-card .resource-card-depth::before,
  .draggable-resource-card .resource-card-depth::after,
  .env-flap, .env-button, .cloth-leaf, .spiral, .bk-figure, .bk-lines,
  .index-tabs, .folio-spine, .folder-clip, .chalkboard {
    display: none;
  }

  .shelf-prop-image {
    display: block;
    width: 100%;
    height: auto;
    pointer-events: none;
    filter: drop-shadow(-5px 10px 7px #38221685);
  }

  .surface-envelope .obj-paper,
  .surface-linen .obj-paper--cloth,
  .surface-folder .obj-paper--folder {
    top: 22.5%;
    left: 17%;
    right: 17%;
    bottom: auto;
    height: 21%;
    box-sizing: border-box;
    padding: 1% 3%;
    gap: 2px;
    border: 0;
    outline: 0;
    box-shadow: none;
    background: none;
    transform: rotate(3deg) skewX(-5deg);
    color: #3b2b24;
  }

  .surface-linen .obj-paper--cloth {
    left: 19%;
    right: 20%;
    transform: rotate(3.5deg) skewX(-5deg);
  }

  .surface-folder .obj-paper--folder {
    top: 28%;
    left: 24%;
    right: 17%;
    height: 23%;
    transform: rotate(7deg) skewX(-9deg);
  }

  .obj-paper strong { font-size: clamp(10px, 1.02cqw, 18px); line-height: 1.25; }
  .obj-paper em, .obj-paper small { font-size: clamp(8px, .7cqw, 12px); letter-spacing: normal; line-height: 1.15; }

  .draggable-resource-card .bk-page,
  .draggable-resource-card .folio-page {
    position: absolute;
    min-height: 0;
    box-shadow: none;
    background: none;
    padding: 0;
  }

  .surface-binder .bk-page--left,
  .surface-binder .bk-page--right {
    top: 16%;
    width: 34%;
    text-align: center;
    color: #473326;
    transform: rotate(2deg) skewX(-4deg);
  }

  .surface-binder .bk-page--left {
    left: 9%;
    padding: 2% 1%;
    background: #fcebd6c2;
    box-shadow: inset 0 0 0 1px #ae8d6960, 0 2px 4px #4a302626;
  }

  .surface-binder .bk-page--right { left: 53%; }
  .surface-binder .bk-print { display: grid; gap: 4px; }
  .surface-binder .bk-page em { letter-spacing: normal; font-size: clamp(8px, .8cqw, 14px); }
  .surface-binder .bk-page strong { font-size: clamp(10px, .98cqw, 17px); }
  .surface-binder .obj-tag--pdf { top: 12%; right: 6%; transform: rotate(5deg); }

  .surface-folio .resource-card-depth {
    transform: skewX(-19deg) rotate(5deg) scaleY(.92);
  }

  .surface-folio .folio-page--left {
    top: 15%;
    left: 13%;
    width: 32%;
    transform: rotate(-2deg);
  }

  .surface-folio .folio-page--right {
    top: 20%;
    left: 54%;
    width: 32%;
    transform: rotate(2deg);
  }

  .surface-folio .folio-page b { font-size: clamp(9px, .93cqw, 15px); }
  .surface-folio .folio-line { font-size: clamp(9px, .82cqw, 14px); }
  .surface-folio .mindmap {
    height: clamp(94px, 10cqw, 180px);
    margin: 0;
  }

  .surface-folio .mindmap__root { top: 44%; }
  .surface-folio .mindmap__node.n1 { top: 5%; }
  .surface-folio .mindmap__node.n2 { top: 42%; }
  .surface-folio .mindmap__node.n3 { top: 76%; }
  .surface-folio .mindmap__line.l1 { top: calc(44% + 12px); }
  .surface-folio .mindmap__line.l2 { top: calc(44% + 20px); }
  .surface-folio .mindmap__line.l3 { top: calc(44% + 28px); }
  .surface-folio .obj-tag--course { left: 10%; bottom: 16%; }
  .surface-folder .obj-tag--course { left: 13%; bottom: 13%; }
  .surface-envelope .obj-tag--gold { left: 12%; bottom: 10%; }
}

@media (max-width: 900px) {
  .draggable-resource-card,
  .draggable-resource-card.surface-binder,
  .draggable-resource-card.surface-folio,
  .draggable-resource-card.surface-folder {
    position: relative;
    inset: auto !important;
    width: 100%;
    min-height: 0;
    height: 320px;
    transform: none !important;
    scale: 1 !important;
    touch-action: manipulation;
  }
}

.shelf-card-trigger {
  position: absolute;
  inset: 0;
  z-index: 10;
  width: 100%;
  border: 0 !important;
  background: transparent !important;
  box-shadow: none !important;
  outline: none;
  cursor: inherit;
}

.shelf-card-trigger:focus-visible + .resource-card-depth {
  filter: drop-shadow(0 0 4px #ffe4a5);
}

.draggable-resource-card:not(.is-dragging):hover {
  filter: brightness(1.025);
}
</style>
