<script setup>
import SceneLink from './SceneLink.vue'
import { ref } from 'vue'
import { fetchProfile } from '../services/dashboard'
const props = defineProps(['owner','greeting','weekly','course','feedback','growth','entries','status'])
defineEmits(['panel','resume','retry'])

/* 工作台便签墙：每张便签按真实倾斜四边形抠成透明 PNG，叠在干净墙面底图上。
   hover 时便签保持自身倾斜角度浮起放大（不旋转成正的）；透明角落不接收事件；
   层叠顺序按便签实际遮挡关系固定，下面便签浮起时仍被上面便签盖住。 */
const ASSET = '/assets/desk/wall/user/'
const BOARD = ASSET + 'wall-clean2.jpg'
const box = ([l, t, w, h]) => ({ left: l + '%', top: t + '%', width: w + '%', height: h + '%' })

// 便签图片与精确位置（wall.jpg 1135×688 → 百分比）
const noteImg = (name) => ASSET + 'note2-' + name + '.png'
// box: [left%, top%, width%, height%]，来自 make_notes_v4：整张立体便签（纸面+白边）的外接框。
// 便签 PNG 是完整的立体纸片；墙上白边/投影已清理干净，浮起时整张一起动，不留残影。
const POS = {
  weekly:     { box:[8.19,11.92,18.68,22.82], z:6 },
  course:     { box:[31.28,7.27,19.91,19.62], z:1 },
  memoTop:    { box:[52.33,4.22,19.56,22.67], z:3 },
  feedback:   { box:[73.22,17.30,16.21,19.48], z:5 },
  memoCat:    { box:[25.81,28.34,23.08,21.51], z:7 },
  memoRight:  { box:[57.62,31.83,20.00,19.62], z:2 },
  growth:     { box:[14.54,52.47,21.15,20.35], z:4 },
  memoBottom: { box:[35.42,61.92,19.74,21.08], z:8 },
  entries:    { box:[55.77,53.49,20.79,25.00], z:6 },
}

// 输入框精确落在原图「记下一个想法…」提示字位置（相对便签外接框百分比）。
// 逐张测量自原图：标题在 12%–24%，提示字在 37%–52%，分开放置绝不叠字。
const MEMO_POS = {
  memoRight:  { left:'9%',   top:'51%'   },
  memoTop:    { left:'10.4%',top:'42.5%' },
  memoCat:    { left:'7.6%', top:'36.5%' },
  memoBottom: { left:'12.5%',top:'45%'   },
}

const key = 'link-desk-v3:' + props.owner
let stored = {}
try { stored = JSON.parse(localStorage.getItem(key)) || {} } catch {}
const memos = ref(stored.memos || {})
const storageError = ref(false)
function save(){
  try { if (props.owner != null) localStorage.setItem(key, JSON.stringify({ memos: memos.value })); storageError.value = false }
  catch { storageError.value = true }
}
function setMemo(id, value){ memos.value[id] = value; save() }
function focusMemo(e){ const t = e.currentTarget.querySelector('textarea'); if (t) t.focus() }
// 空便签用带原图印刷提示字的图片（与紫便签四行字同一套像素，等比缩放、大小天然一致）；
// 一旦写入文字就换成无字图，改由 textarea 显示输入内容。
const memoImg = (id) => noteImg(id + (memos.value[id] ? '' : '-hint'))

const dialog = ref(null), level = ref(1), levelError = ref(false)
async function openTools(){
  try { level.value = Number((await fetchProfile()).level) || 1; levelError.value = false }
  catch { levelError.value = true }
  if (!dialog.value.open) dialog.value.showModal()
}
</script>
<template>
<section class="tag-wall desk-wall" aria-label="工作台便签墙">
  <div class="desk-wall__board" :style="{backgroundImage:`url(${BOARD})`}">
    <!-- 功能便签：继续训练（被 memoCat 压，层级最低） -->
    <button v-if="course" type="button" class="note hit" data-note="course" :style="[box(POS.course.box),{zIndex:POS.course.z}]"
      aria-label="继续训练" @click="$emit('resume')"><img :src="noteImg('course')" alt="" /></button>
    <router-link v-else to="/training" class="note hit" data-note="course" :style="[box(POS.course.box),{zIndex:POS.course.z}]"
      aria-label="开始新训练"><img :src="noteImg('course')" alt="" /></router-link>

    <!-- 右绿叶便签（被 feedback 和 entries 压） -->
    <div class="note memo-note" data-note="memoRight" :style="[box(POS.memoRight.box),{zIndex:POS.memoRight.z}]" @click="focusMemo($event)">
      <img :src="memoImg('memoRight')" alt="" />
      <textarea class="memo" :style="MEMO_POS.memoRight" maxlength="120"
        :value="memos.memoRight || ''" @input="setMemo('memoRight', $event.target.value)" aria-label="便签：记下一个想法"></textarea>
    </div>

    <!-- 右上我的便签（带花） -->
    <div class="note memo-note" data-note="memoTop" :style="[box(POS.memoTop.box),{zIndex:POS.memoTop.z}]" @click="focusMemo($event)">
      <img :src="memoImg('memoTop')" alt="" />
      <textarea class="memo" :style="MEMO_POS.memoTop" maxlength="120"
        :value="memos.memoTop || ''" @input="setMemo('memoTop', $event.target.value)" aria-label="便签：记下一个想法"></textarea>
    </div>

    <!-- 成长轨迹 -->
    <button type="button" class="note hit" data-note="growth" :style="[box(POS.growth.box),{zIndex:POS.growth.z}]"
      aria-label="查看成长轨迹" @click="$emit('panel','growth')"><img :src="noteImg('growth')" alt="" /></button>

    <!-- 差反馈（压住右绿叶便签）：左上角胶带单独成图，跟便签一起浮起 -->
    <button type="button" class="note hit feedback-note" data-note="feedback" :style="[box(POS.feedback.box),{zIndex:POS.feedback.z}]"
      aria-label="查看课堂反馈" @click="$emit('panel','feedback')">
      <img class="feedback-tape" :src="ASSET+'feedback-tape.png'" alt="" />
      <img :src="noteImg('feedback')" alt="" />
    </button>

    <!-- 快捷入口（压住右绿叶便签底部，四个链接区均分） -->
    <div class="note entries-board" data-note="entries" :style="[box(POS.entries.box),{zIndex:POS.entries.z}]">
      <img :src="noteImg('entries')" alt="" />
      <div class="entries-links">
        <router-link v-for="item in entries" :key="item.title" :to="item.route || '/courses'"
          :aria-label="`进入${item.title}`"></router-link>
      </div>
    </div>

    <!-- 本周训练 -->
    <button type="button" class="note hit" data-note="weekly" :style="[box(POS.weekly.box),{zIndex:POS.weekly.z}]"
      aria-label="本周训练：查看训练日志" @click="$emit('panel','weekly')"><img :src="noteImg('weekly')" alt="" /></button>

    <!-- 中间小猫便签（压住继续训练，层级最高） -->
    <div class="note memo-note" data-note="memoCat" :style="[box(POS.memoCat.box),{zIndex:POS.memoCat.z}]" @click="focusMemo($event)">
      <img :src="memoImg('memoCat')" alt="" />
      <textarea class="memo" :style="MEMO_POS.memoCat" maxlength="120"
        :value="memos.memoCat || ''" @input="setMemo('memoCat', $event.target.value)" aria-label="便签：记下一个想法"></textarea>
    </div>

    <!-- 下中花便签 -->
    <div class="note memo-note" data-note="memoBottom" :style="[box(POS.memoBottom.box),{zIndex:POS.memoBottom.z}]" @click="focusMemo($event)">
      <img :src="memoImg('memoBottom')" alt="" />
      <textarea class="memo" :style="MEMO_POS.memoBottom" maxlength="120"
        :value="memos.memoBottom || ''" @input="setMemo('memoBottom', $event.target.value)" aria-label="便签：记下一个想法"></textarea>
    </div>

    <p v-if="status!=='ready'" class="wall-status" role="status">
      {{ status==='error' ? '数据加载失败' : '正在整理记录…' }}
      <button v-if="status==='error'" type="button" @click="$emit('retry')">重新加载</button>
    </p>

    <!-- 向下箭头：用户提供的木质箭头（旋转为朝下），点击前往办公桌 -->
    <SceneLink direction="down" class="wall-down" to="/courses" aria-label="向下前往办公桌"
      :style="box([43.5,86,7.5,13.5])"><img :src="ASSET+'arrow-down-wood.png'" alt="向下前往办公桌" /></SceneLink>
  </div>

  <header class="wall-tools">
    <h1>{{ greeting }}</h1>
    <button type="button" @click="openTools">✧ 装饰小墙</button>
  </header>

  <dialog ref="dialog" class="wall-dialog" aria-label="装饰小墙" @click="e=>{if(e.target===dialog)dialog.close()}">
    <section>
      <header><h2>装饰小墙</h2><button type="button" aria-label="关闭" @click="dialog.close()">×</button></header>
      <p class="wall-dialog__note">墙面与便签沿用当前生成图。点功能便签查看详情，或在「我的便签」上写下想法，改动会自动保存在本机。</p>
      <p v-if="levelError" role="status">等级暂未同步，重新打开可重试。</p>
      <button type="button" class="wall-primary" @click="dialog.close()">知道了</button>
    </section>
  </dialog>
  <p v-if="storageError" role="status" class="wall-status wall-status--toast">浏览器暂时无法保存便签</p>
</section>
</template>
<style scoped>
.desk-wall {position:relative;width:100%;height:100%;min-height:0;isolation:isolate;overflow:hidden;background:#261c18;display:grid;place-items:center;container-type:size}
:deep(.page-dashboard) .tag-wall {width:100%;height:100%}
.desk-wall__board {position:relative;width:min(100cqw, calc(100cqh * 1135 / 688));height:min(100cqh, calc(100cqw * 688 / 1135));aspect-ratio:1135/688;background-color:#e9a779;background-position:center;background-size:100% 100%;background-repeat:no-repeat;overflow:hidden;container-type:size}
@supports not (width:1cqw){.desk-wall__board{width:100%;height:100%}}

.wall-tools {position:absolute;left:2.4%;top:2.2%;z-index:30;display:flex;align-items:center;gap:12px}
.wall-tools h1 {margin:0;font:700 clamp(18px,2vw,30px)/1.1 "Songti SC",SimSun,serif;color:#6b4327;text-shadow:0 1px 0 rgba(255,246,224,.7)}
.wall-tools button {border:1px solid rgba(238,208,165,.8);border-radius:22px;background:rgba(68,56,46,.86);color:#fff2d9;padding:7px 13px;font-size:13px;cursor:pointer}
.wall-tools button:hover {background:rgba(68,56,46,1)}

/* 便签：整张立体纸片（纸面+白边）作为一张图，墙上无残留，浮起时整体一起动。
   hover 只 scale + translateY，绝不旋转，保持便签自身倾斜角度；不加任何投影滤镜。
   浮起时临时提升 z-index，让这张便签完整显示，不被别的便签压住。 */
.note {position:absolute;display:block;padding:0;margin:0;border:0;transform-origin:center;transition:transform .24s cubic-bezier(.2,.8,.2,1)}
.note > img {display:block;width:100%;height:100%;pointer-events:none}
/* 粉色便签左上角胶带：跨出便签框左上方，与主图同一容器一起浮起 */
.feedback-note {overflow:visible}
.feedback-note > .feedback-tape {position:absolute;left:-13%;top:-17%;width:37%;height:34%;pointer-events:none}
.note:hover,.note:focus-within {transform:scale(1.08) translateY(-9px);z-index:50}
.note:focus-visible {outline:none}
.hit {cursor:pointer;background:transparent}

/* 快捷入口：整张便签浮起，内部四个透明链接均分可点 */
.entries-links {position:absolute;inset:0;display:grid;grid-template-rows:repeat(4,1fr)}
.entries-links a {display:block;cursor:pointer}
.entries-links a:focus-visible {outline:none}

/* 装饰便签输入框：透明无描边。字号与颜色严格对齐紫色便签「我的课程/模拟课堂…」那四行字
   ——那是图片像素，会随便签一起缩放；输入框字号也必须用纯 cqw 跟便签等比缩放，
   绝不能用固定 px 下限（小窗口便签缩到 80px 宽时，固定 8px 会大出一倍）。
   常规体、中性深灰 #565154（不偏棕）、不加粗/不加深。位置在标题下方。
   输入文字与 placeholder 完全同款；有内容时提示自动消失。 */
.memo-note {cursor:text}
.memo {position:absolute;width:80%;height:16%;resize:none;border:0;background:transparent;color:#565154;font:400 .9cqw/1.15 "Songti SC","SimSun",serif;padding:0;overflow:hidden;outline:none;word-break:break-all}
.memo::placeholder {color:#565154;opacity:1}
.memo {-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale;text-rendering:optimizeLegibility}
.memo:hover,.memo:focus,.memo:focus-visible {background:transparent;outline:none;border:0}

.wall-status {position:absolute;left:50%;top:3%;translate:-50%;z-index:20;margin:0;padding:6px 14px;border-radius:16px;background:rgba(68,56,46,.85);color:#fff3df;font-size:13px}
.wall-status button {margin-left:8px;background:none;border:1px solid #fff3df88;border-radius:10px;color:inherit;padding:2px 8px;cursor:pointer}
.wall-status--toast {top:auto;bottom:3%}

/* 向下箭头：木质箭头图片（用户指定素材），hover 时轻微下沉 */
.wall-down {position:absolute;z-index:12;display:block;text-decoration:none;transform-origin:center;transition:transform .22s cubic-bezier(.2,.8,.2,1)}
.wall-down img {display:block;width:100%;height:100%;object-fit:contain;filter:drop-shadow(0 3px 5px rgba(60,30,10,.35))}
.wall-down:hover,.wall-down:focus-visible {transform:translateY(5px);outline:none}

.wall-dialog {width:min(420px,92vw);border:1px solid #caa786;border-radius:18px;color:#392d28;background:#fff6e8;box-shadow:0 18px 64px #301b2350;padding:0}
.wall-dialog::backdrop {background:#38231b50}
.wall-dialog section {padding:18px}
.wall-dialog header {display:flex;align-items:center;justify-content:space-between}
.wall-dialog h2 {margin:0;font-size:19px}
.wall-dialog button {border:1px solid #bfa68d;background:#fffaf1;border-radius:9px;padding:6px 12px;color:inherit;cursor:pointer}
.wall-dialog__note {font-size:14px;line-height:1.7;margin:14px 0}
.wall-dialog .wall-primary {display:block;margin:8px 0 0 auto;background:#44382e;color:#fff2d9;border-color:#44382e}

@media (max-width:700px) {
  .wall-tools h1 {font-size:17px}
  .wall-tools button {font-size:12px;padding:5px 9px}
}
</style>
