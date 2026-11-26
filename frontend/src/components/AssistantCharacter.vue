<script setup>
import { computed } from 'vue'
import DigitalHuman from './DigitalHuman.vue'

const props = defineProps({
  pose: String, role: String, quiet: Boolean, animated: { type: Boolean, default: true },
  look: { type: Number, default: 0 }, lookY: { type: Number, default: 0 }, level: Number,
})
const pose = computed(() => props.animated && !props.quiet ? props.pose : '')
const marks = { notes: '？', thinking: '💡', sleep: 'z', startled: '!', encourage: '✦' }
</script>

<template>
  <span class="assistant-character" :data-character-pose="pose"
    :style="{ '--look': animated ? look : 0 }" aria-hidden="true">
    <span class="assistant-body">
      <DigitalHuman :class="{ 'assistant-writing-sprite': pose === 'notes' }" :pose="pose" :role="role"
        :look="look" :look-y="lookY" :level="level" :quiet="quiet" :animated="animated" />
      <i v-if="role === 'examiner'" class="assistant-glasses"></i>
      <svg v-if="pose === 'notes'" class="assistant-notebook" viewBox="0 0 64 36">
        <path d="M4 14 29 14 55 13 62 25 33 31 3 28Z" fill="#543466" stroke="#392344" stroke-width="1.5"/>
        <path d="M5 15 29 15 55 14 61 24 33 29 4 27Z" fill="#c6adba"/>
        <path d="M8 13Q20 11 30 14L33 28Q20 24 4 26Z" fill="#fff1d7" stroke="#aa839e" stroke-linejoin="round"/>
        <path d="M30 14Q42 11 54 12L61 24Q47 24 33 28Z" fill="#fff7e6" stroke="#aa839e" stroke-linejoin="round"/>
        <path d="M30 14Q31 21 33 28" fill="none" stroke="#98718c"/>
        <path d="M11 16Q19 15 27 17M10 19Q19 18 28 20M9 22Q19 21 29 23M35 17Q43 15 52 15M36 20Q45 18 54 18M37 23Q46 21 56 21"
          fill="none" stroke="#c6a9b9" stroke-width=".8"/>
        <path d="M14 29 20 31 25 30 29 31 29 34Q25 37 20 35L14 34Z"
          fill="#f6bd9c" stroke="#784755" stroke-linejoin="round"/>
        <path d="M57 27Q61 26 60 21L57 16 53 19 55 23 52 27Z"
          fill="#9871c1" stroke="#513364" stroke-width="1.25" stroke-linejoin="round"/>
        <g class="assistant-notebook__writing-arm">
          <path d="m56 21-5 1-3-4 4-3 5 2Z" fill="#f4dff7" stroke="#65477f" stroke-width=".9"/>
          <path d="m43 19 7-12 2 1-7 12-3 2Z" fill="#8453ab" stroke="#593777" stroke-width=".8"/>
          <path d="m42 22 1-3 2 1Z" fill="#51304a"/>
          <path d="M47 13Q48 11 51 12L54 14 53 17 50 19 47 18 46 16Z"
            fill="#f6bd9c" stroke="#784755"/>
          <path d="m48 15 2 1" fill="none" stroke="#bd7d69" stroke-linecap="round"/>
        </g>
      </svg>
      <span v-if="pose === 'cheer'" class="assistant-clap">👏</span>
    </span>
    <span v-if="marks[pose]" :class="['assistant-mark', 'assistant-mark--' + pose]"><svg v-if="pose === 'notes'" class="assistant-question" viewBox="0 0 16 16">
      <path d="M5 5a3 3 0 0 1 6 0c0 2-3 2.3-3 4.2" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>
      <circle cx="8" cy="12.3" r="1.05" fill="currentColor"/>
    </svg><template v-else>{{ marks[pose] }}</template></span>
    <span v-if="pose === 'cheer'" class="assistant-confetti">
      <i v-for="index in 9" :key="index" :style="{ '--piece': index }"></i>
    </span>
  </span>
</template>

<style scoped>
.assistant-character { position:relative; display:block; width:100%; height:100%; pointer-events:none; container-type:inline-size; }
.assistant-body { position:absolute; inset:0; transform-origin:50% 86%; transition:transform .18s ease-out; }
.assistant-mark {
  display:grid; place-items:center; position:absolute; top:-5%; right:1%; min-width:1.4em; height:1.4em;
  border-radius:50%; background:#493057; color:#fff1ff; font-size:clamp(12px, 27cqw, 21px); font-weight:700;
  box-shadow:0 2px 6px #1d102740; animation:assistant-pop .28s cubic-bezier(.2,.8,.24,1.3) both;
}
.assistant-mark--sleep { top:-4%; right:0; background:#483458; animation:assistant-doze 3s ease-in-out infinite; }
.assistant-mark--encourage { background:#784d8b; color:#ffe4a7; }
.assistant-mark--thinking { background:#543a60; animation:assistant-light 1.8s ease-in-out infinite; }
.assistant-mark--notes {
  top:calc(50% - 47cqw); right:1%; left:auto;
  translate:0 -25%; width:1.4em;
}
.assistant-question { display:block; width:75%; height:75%; }
/* Hide the resting arms of the base sprite below the shoulders during writing. */
.assistant-writing-sprite {
  clip-path:polygon(
    0 0,100% 0,100% calc(50% + 12cqw),
    63% calc(50% + 12cqw),63% calc(50% + 28cqw),
    100% calc(50% + 28cqw),100% 100%,0 100%,
    0 calc(50% + 28cqw),37% calc(50% + 28cqw),
    37% calc(50% + 12cqw),0 calc(50% + 12cqw)
  );
}
.assistant-notebook {
  position:absolute; left:50%; top:calc(50% + 13cqw);
  width:47cqw; height:auto; overflow:visible;
  transform:translate(-50%,-50%);
}
.assistant-notebook__writing-arm {
  transform-origin:55px 20px;
  animation:assistant-scribble .42s ease-in-out infinite alternate;
}
.assistant-glasses {
  position:absolute; top:34%; left:34%; width:32%; height:2px; background:#3a2338;
}
.assistant-glasses::before,.assistant-glasses::after { content:""; position:absolute; top:-2px; width:46%; height:clamp(4px, 11cqw, 9px); border:1px solid #3a2338; border-radius:2px 2px 4px 4px; background:#e2d1fb3d; }
.assistant-glasses::before { left:-1px; }.assistant-glasses::after { right:-1px; }
.assistant-clap { position:absolute; left:35%; top:48%; font-size:34cqw; animation:assistant-clap .34s ease-in-out 6; }
.assistant-confetti { position:absolute; inset:0; }
.assistant-confetti i {
  position:absolute; top:30%; left:48%; width:4px; height:7px; border-radius:1px;
  background:hsl(calc(var(--piece) * 42deg) 86% 73%); animation:assistant-confetti .9s ease-out calc(var(--piece) * 20ms) 2 both;
}
[data-character-pose="curious"] .assistant-body { transform:rotate(calc(var(--look) * 5deg)); }
[data-character-pose="startled"] .assistant-body { transform:rotate(-13deg) scale(1.08); }
[data-character-pose="brace"] .assistant-body { transform:rotate(15deg); }
[data-character-pose="sleep"] .assistant-body { animation:assistant-breathe 3.4s ease-in-out infinite; }
[data-character-pose="encourage"] .assistant-body { animation:assistant-encourage .65s ease-in-out 3; }
[data-character-pose="cheer"] .assistant-body { animation:assistant-encourage .42s ease-in-out 4; }
@keyframes assistant-pop { from { opacity:0; transform:translateY(5px) scale(.65); } }
@keyframes assistant-breathe { 50% { transform:rotate(-7deg) scaleY(.91); } }
@keyframes assistant-doze { 45%,70% { transform:translate(3px,-6px); } }
@keyframes assistant-light { 50% { box-shadow:0 0 12px #ffd893a0; } }
@keyframes assistant-scribble { to { transform:rotate(-3deg); } }
@keyframes assistant-clap { 50% { transform:rotate(-12deg) scale(.78); } }
@keyframes assistant-confetti {
  from { opacity:1; transform:rotate(calc(var(--piece) * 40deg)) translateY(-3px); }
  to { opacity:0; transform:rotate(calc(var(--piece) * 40deg)) translateY(-39px) rotate(90deg); }
}
@keyframes assistant-encourage { 48% { transform:translateY(-5px) rotate(5deg); } }
@media (prefers-reduced-motion:reduce) {
  .assistant-notebook__writing-arm { animation:none; }
  [data-character-pose="curious"] .assistant-body { transform:none; transition:none; }
  .assistant-confetti i { transform:rotate(calc(var(--piece) * 40deg)) translateY(-28px); }
}
</style>
