<script setup>
import SceneLink from './SceneLink.vue'
import { computed, ref } from 'vue'
import { fetchProfile } from '../services/dashboard'
const props = defineProps(['owner','greeting','weekly','course','feedback','growth','entries','status'])
defineEmits(['panel','resume','retry'])

/* 生成图上的便签是固定的画面，这里只在便签位置叠透明热区：
   功能便签弹出原面板，装饰便签可写入想法。整幅画面即用户生成的设计图。 */
const BOARD = '/assets/desk/wall/user/wall.jpg'
const key = 'link-wall-v2:' + props.owner

// 装饰便签（我的便签）里用户写入的文字，按 id 存本地
let stored = {}
try { stored = JSON.parse(localStorage.getItem(key)) || {} } catch {}
const memos = ref(stored.memos || {})   // { memoTop: '...', memoCat: '...', ... }
const storageError = ref(false)
function save(){
  try { if (props.owner != null) localStorage.setItem(key, JSON.stringify({ memos: memos.value })); storageError.value = false }
  catch { storageError.value = true }
}
function setMemo(id, value){ memos.value[id] = value; save() }

// 顶部小工具（仍可用，折叠在角落，不遮挡画面）
const dialog = ref(null), tool = ref(''), level = ref(1), levelError = ref(false)
async function openTools(kind){
  tool.value = kind
  if (kind === 'decor') {
    try { level.value = Number((await fetchProfile()).level) || 1; levelError.value = false }
    catch { levelError.value = true }
  }
  if (!dialog.value.open) dialog.value.showModal()
}
const skies = { original:'原画墙面' }
const weather = ref('original')
</script>
<template>
<section class="tag-wall" aria-label="标签墙" :style="{backgroundImage:`url(${BOARD})`}">
  <!-- 顶部欢迎与工具：半透明白底，尽量不破坏生成图氛围 -->
  <header class="wall-tools">
    <h1>{{ greeting }}</h1>
    <button type="button" @click="openTools('decor')">✧ 装饰小墙</button>
  </header>

  <!-- 功能便签热区：位置与生成图便签对齐，点击触发原有面板/跳转 -->
  <button type="button" class="hit" data-note="weekly"
    :style="{left:'9.5%',top:'6.4%',width:'14.8%',height:'24.7%'}"
    aria-label="本周训练：查看训练日志" @click="$emit('panel','weekly')"></button>

  <button v-if="course" type="button" class="hit" data-note="course"
    :style="{left:'29.8%',top:'5.5%',width:'16%',height:'22.4%'}"
    aria-label="继续训练" @click="$emit('resume')"></button>
  <router-link v-else to="/training" class="hit" data-note="course"
    :style="{left:'29.8%',top:'5.5%',width:'16%',height:'22.4%'}" aria-label="开始新训练"></router-link>

  <button type="button" class="hit" data-note="feedback"
    :style="{left:'72.6%',top:'12.5%',width:'16%',height:'21.2%'}"
    aria-label="查看课堂反馈" @click="$emit('panel','feedback')"></button>

  <button type="button" class="hit" data-note="growth"
    :style="{left:'16.2%',top:'51.7%',width:'18.3%',height:'20.1%'}"
    aria-label="查看成长轨迹" @click="$emit('panel','growth')"></button>

  <div class="entries-board" data-note="entries"
    :style="{left:'56.4%',top:'52%',width:'21.3%',height:'23.5%'}">
    <router-link v-for="item in entries" :key="item.title" :to="item.route || '/courses'"
      :aria-label="`进入${item.title}`"></router-link>
  </div>

  <!-- 装饰便签：透明输入框叠在生成图便签的文字区域上，可写入/编辑想法 -->
  <textarea class="memo" data-note="memoTop" placeholder="记下一个想法…" maxlength="120"
    :style="{left:'53.6%',top:'10%',width:'15%',height:'9%'}"
    :value="memos.memoTop || ''" @input="setMemo('memoTop', $event.target.value)" aria-label="便签：记下一个想法"></textarea>
  <textarea class="memo" data-note="memoCat" placeholder="记下一个想法…" maxlength="120"
    :style="{left:'27.5%',top:'29.5%',width:'16%',height:'9%'}"
    :value="memos.memoCat || ''" @input="setMemo('memoCat', $event.target.value)" aria-label="便签：记下一个想法"></textarea>
  <textarea class="memo" data-note="memoRight" placeholder="记下一个想法…" maxlength="120"
    :style="{left:'60%',top:'35.5%',width:'16%',height:'9%'}"
    :value="memos.memoRight || ''" @input="setMemo('memoRight', $event.target.value)" aria-label="便签：记下一个想法"></textarea>
  <textarea class="memo" data-note="memoBottom" placeholder="记下一个想法…" maxlength="120"
    :style="{left:'38.5%',top:'66%',width:'16%',height:'9%'}"
    :value="memos.memoBottom || ''" @input="setMemo('memoBottom', $event.target.value)" aria-label="便签：记下一个想法"></textarea>

  <!-- 状态提示（加载/错误）保持无障碍可见，视觉上不遮挡画面 -->
  <p v-if="status!=='ready'" class="wall-status" role="status">
    {{ status==='error' ? '数据加载失败' : '正在整理记录…' }}
    <button v-if="status==='error'" type="button" @click="$emit('retry')">重新加载</button>
  </p>

  <!-- 向下箭头：点击前往办公桌（我的备课桌） -->
  <SceneLink direction="down" class="wall-down" to="/courses" aria-label="向下前往办公桌">
    <span class="wall-down__label">前往办公桌</span>
  </SceneLink>

  <dialog ref="dialog" class="wall-dialog" aria-label="装饰小墙" @click="e=>{if(e.target===dialog)dialog.close()}">
    <section>
      <header><h2>装饰小墙</h2><button type="button" aria-label="关闭" @click="dialog.close()">×</button></header>
      <p class="wall-dialog__note">墙面与便签沿用当前生成图。点便签可查看详情或在「我的便签」上写下想法，改动会自动保存在本机。</p>
      <p v-if="levelError" role="status">等级暂未同步，重新打开可重试。</p>
      <button type="button" class="wall-primary" @click="dialog.close()">知道了</button>
    </section>
  </dialog>
  <p v-if="storageError" role="status" class="wall-status">浏览器暂时无法保存便签</p>
</section>
</template>
<style scoped>
.tag-wall {position:relative;width:100%;height:100%;min-height:0;isolation:isolate;overflow:hidden;background-color:#e9a779;background-position:center center;background-size:cover;background-repeat:no-repeat}
.wall-tools {position:absolute;left:1.4%;top:2%;z-index:2;display:flex;align-items:center;gap:12px}
.wall-tools h1 {margin:0;font:700 clamp(18px,2vw,30px)/1.1 "Songti SC",SimSun,serif;color:#6b4327;text-shadow:0 1px 0 rgba(255,246,224,.65)}
.wall-tools button {border:1px solid rgba(238,208,165,.8);border-radius:22px;background:rgba(68,56,46,.86);color:#fff2d9;padding:7px 13px;font-size:13px}
.wall-tools button:hover {background:rgba(68,56,46,1)}

/* 功能热区：完全透明，保留光标与键盘焦点提示 */
.hit {position:absolute;z-index:2;display:block;padding:0;margin:0;border:0;background:transparent;cursor:pointer;border-radius:8px}
.hit:focus-visible,.hit:hover {outline:2px dashed rgba(126,80,40,.75);outline-offset:-3px;background:rgba(255,255,255,.06)}
.entries-board {position:absolute;z-index:2;display:grid;grid-template-rows:repeat(4,1fr)}
.entries-board a {display:block;cursor:pointer;border-radius:6px}
.entries-board a:hover,.entries-board a:focus-visible {outline:2px dashed rgba(126,80,40,.75);outline-offset:-3px;background:rgba(255,255,255,.08)}

/* 装饰便签：透明输入，文字沿用生成图色调（灰棕） */
.memo {position:absolute;z-index:2;resize:none;border:0;background:transparent;color:#5b4638;font:500 clamp(11px,1.05vw,15px)/1.4 "Microsoft YaHei",sans-serif;padding:2px;overflow:hidden;outline:none}
.memo::placeholder {color:transparent}
.memo:hover,.memo:focus {background:rgba(255,251,238,.34);border-radius:4px}
.memo:focus-visible {outline:2px dashed rgba(126,80,40,.75);outline-offset:-2px}

.wall-status {position:absolute;left:50%;top:3%;translate:-50%;z-index:3;margin:0;padding:6px 14px;border-radius:16px;background:rgba(68,56,46,.85);color:#fff3df;font-size:13px}
.wall-status button {margin-left:8px;background:none;border:1px solid #fff3df88;border-radius:10px;color:inherit;padding:2px 8px}

/* 向下箭头：贴合生成图底部箭头位置 */
.wall-down {position:absolute;z-index:3;left:47.5%;bottom:1.2%;translate:-50%;display:flex;flex-direction:column;align-items:center;gap:2px;width:clamp(52px,6vw,88px);color:#fff3df;text-decoration:none}
.wall-down__label {font-size:12px;padding:2px 9px;border-radius:14px;background:rgba(68,56,46,.78);white-space:nowrap;opacity:0;transition:opacity .18s}
.wall-down:hover .wall-down__label,.wall-down:focus-visible .wall-down__label {opacity:1}
.wall-down::after {content:"";width:20px;height:20px;border-right:3px solid rgba(68,56,46,.85);border-bottom:3px solid rgba(68,56,46,.85);rotate:45deg;animation:wallBob 1.8s ease-in-out infinite}
.wall-down:hover::after {border-color:#8a4e22}
@keyframes wallBob {0%,100%{transform:translateY(0)}50%{transform:translateY(5px)}}

.wall-dialog {width:min(420px,92vw);border:1px solid #caa786;border-radius:18px;color:#392d28;background:#fff6e8;box-shadow:0 18px 64px #301b2350;padding:0}
.wall-dialog::backdrop {background:#38231b50}
.wall-dialog section {padding:18px}
.wall-dialog header {display:flex;align-items:center;justify-content:space-between}
.wall-dialog h2 {margin:0;font-size:19px}
.wall-dialog button {border:1px solid #bfa68d;background:#fffaf1;border-radius:9px;padding:6px 12px;color:inherit}
.wall-dialog__note {font-size:14px;line-height:1.7;margin:14px 0}
.wall-dialog .wall-primary {display:block;margin:8px 0 0 auto;background:#44382e;color:#fff2d9;border-color:#44382e}

@media (prefers-reduced-motion: reduce) { .wall-down::after { animation:none } }
@media (max-width:700px) {
  .wall-tools h1 {font-size:17px}
  .wall-tools button {font-size:12px;padding:5px 9px}
  .wall-down__label {opacity:1}
}
</style>
