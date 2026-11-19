<script setup>
import { nextTick, onMounted, onBeforeUnmount, ref, watch } from 'vue'
const props = defineProps({ title: String })
const emit = defineEmits(['close'])
const dialog = ref(null)
let previous
watch(() => props.title, async () => { await nextTick(); if (!dialog.value?.contains(document.activeElement)) dialog.value?.querySelector('button')?.focus() })
function close() { emit('close') }
function trap(event) {
  if (event.key !== 'Tab') return
  const items=[...dialog.value.querySelectorAll('button:not(:disabled),a[href],input,select,textarea,summary,[tabindex="0"]')].filter(e=>e.getClientRects().length)
  const first=items[0],last=items.at(-1)
  if(event.shiftKey && (document.activeElement===first || !items.includes(document.activeElement))){event.preventDefault();last?.focus()}
  else if(!event.shiftKey && (document.activeElement===last || !items.includes(document.activeElement))){event.preventDefault();first?.focus()}
}
onMounted(async () => { previous = document.activeElement; await nextTick(); dialog.value.showModal() })
onBeforeUnmount(() => { dialog.value?.close(); if (previous?.isConnected) previous.focus() })
</script>
<template>
  <Teleport to="body">
    <dialog ref="dialog" class="course-modal" aria-labelledby="course-modal-title" @cancel.prevent="close" @keydown="trap" @click="event => { if (event.target === dialog) close() }">
      <section class="course-modal__sheet">
        <header><h2 id="course-modal-title">{{ title }}</h2><button type="button" aria-label="关闭课程弹窗" autofocus @click="close">×</button></header>
        <div class="course-modal__body"><slot /></div>
        <footer v-if="$slots.footer"><slot name="footer" /></footer>
      </section>
    </dialog>
  </Teleport>
</template>
<style>
.course-modal {
  --glass-ink:#fff6ec; --glass-muted:#e2d4d2; --glass-line:#ffebd333; --glass-tint:#ffead312;
  color:var(--glass-ink); color-scheme:dark; width:min(540px,calc(100vw - 28px));
  padding:0; border:1px solid #ffeadd59; border-radius:19px; overflow:hidden;
  background:linear-gradient(135deg,#473946e8,#211e2bec 72%);
  backdrop-filter:blur(24px) saturate(135%); box-shadow:inset 0 1px #ffffff26,0 22px 72px #17102276;
}
.course-modal::backdrop {background:#17101e55}
.course-modal__sheet {display:flex;flex-direction:column;max-height:min(66dvh,510px)}
.course-modal header,.course-modal footer {display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 18px;flex:none}
.course-modal header {border-bottom:1px solid var(--glass-line)}
.course-modal h2 {margin:0;font-size:19px;letter-spacing:.025em;color:inherit}
.course-modal header button {width:34px;height:34px;border:1px solid var(--glass-line);border-radius:50%;background:var(--glass-tint);color:inherit;font-size:21px}
.course-modal__body {overflow:auto;padding:14px 18px;min-height:0;overscroll-behavior:contain;scrollbar-width:thin;font-size:14px}
.course-modal footer {border-top:1px solid var(--glass-line)}
.course-modal button,.course-modal select,.course-modal summary {cursor:pointer}
.course-modal select {font:inherit;max-width:100%;padding:6px 10px;border:1px solid var(--glass-line);border-radius:8px;background:#383242;color:inherit}
.course-modal p,.course-modal pre {white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;line-height:1.65}
.course-modal a {color:inherit;text-underline-offset:3px}
.course-modal :focus-visible {outline:2px solid #dea976;outline-offset:2px}
[data-ui-theme="academy"] .course-modal {--glass-ink:#132b49;--glass-muted:#42566e;--glass-line:#48637d40;--glass-tint:#5a8cbb15;color-scheme:light;background:linear-gradient(135deg,#f2f8fff2,#dce6f2e8);border-color:#ffffffbf}
[data-ui-theme="academy"] .course-modal select {background:#eef5fb}
@media(max-height:500px){.course-modal__sheet{max-height:calc(100dvh - 20px)}}
</style>
