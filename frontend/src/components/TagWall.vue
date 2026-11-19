<script setup>
import { computed, ref, nextTick } from 'vue'
import { fetchProfile } from '../services/dashboard'
const props = defineProps(['owner','greeting','weekly','course','feedback','growth','entries','status'])
defineEmits(['panel','resume','retry'])
const presets = [
  ['weekly','本周训练',.08,.12,'#fff0a9'], ['course','继续训练',.51,.08,'#d8efe0'],
  ['feedback','课堂反馈',.91,.22,'#fbd7d2'], ['growth','成长轨迹',.25,.78,'#d6e9f7'],
  ['entries','快捷入口',.72,.84,'#eadaf5']
]
if (matchMedia('(max-width:700px)').matches) {
  const positions = [[0,.04],[1,.06],[0,.42],[1,.46],[.25,.96]]
  presets.forEach((note,i) => { [note[2],note[3]] = positions[i] })
}
const key = 'link-wall-v1:' + props.owner
let stored = {}
try { stored = JSON.parse(localStorage.getItem(key)) || {} } catch {}
const skies = {original:'杏墙初照',spring:'春燕衔樱',summer:'青柠长夏',autumn:'枫糖午后',winter:'雪松来信',rain:'听雨青窗'}
const decals = {sprout:{name:'盆里冒芽',level:1},bird:{name:'衔笔青鸟',level:3},fox:{name:'月牙眠狐',level:6}}
const asset = name => '/assets/desk/wall/' + name + '.webp'
const weather = ref(Object.hasOwn(skies,stored.weather) ? stored.weather : 'original')
const hidden = ref(Array.isArray(stored.hidden) ? stored.hidden : [])
const defaults = presets.map(([id,title,x,y,color]) => ({id,title,x,y,color}))
const notes = ref(defaults.filter(n=>!hidden.value.includes(n.id)).map(n=>({...n})))
const dialog = ref(null), tab = ref(''), level = ref(1), levelError = ref(false)
const target = computed(()=>notes.value.find(n=>n.id===selected.value))
const draft = ref({size:235,color:'#fff0bf'})
const limit = (v,min,max,initial) => Number.isFinite(v) ? Math.min(max,Math.max(min,v)) : initial
async function openTools(kind,n){
  tab.value=kind
  if(n) selected.value=n.id
  if(!dialog.value.open) dialog.value.showModal()
  if(kind==='decor'){
    try {level.value=Number((await fetchProfile()).level)||1;levelError.value=false}
    catch {levelError.value=true}
  }
}
function remove(){
  if(!target.value)return
  if(defaults.some(n=>n.id===selected.value))hidden.value.push(selected.value)
  notes.value=notes.value.filter(n=>n.id!==selected.value)
  dialog.value.close();save()
}
function restore(){
  notes.value.push(...defaults.filter(n=>hidden.value.includes(n.id)).map(n=>({...n})))
  hidden.value=[];save()
}
function paste(kind){
  if(!decals[kind] || level.value<decals[kind].level)return
  const id='decal-'+crypto.randomUUID()
  notes.value.push({id,kind,title:decals[kind].name,x:.5,y:.5,size:135,opacity:1,angle:0})
  dialog.value.close();selected.value=id;save()
}
function ink(color){
  const [r,g,b]=color.slice(1).match(/../g).map(v=>parseInt(v,16))
  return .299*r+.587*g+.114*b<125?'#fffaf2':'#382e27'
}
if (Array.isArray(stored.notes)) {
  for (const item of stored.notes) {
    if (!item || !Number.isFinite(item.x) || !Number.isFinite(item.y)) continue
    const original = notes.value.find(n => n.id === item.id)
    const point = {x:clamp(item.x), y:clamp(item.y)}
    if (original) Object.assign(original, point)
    else if (typeof item.id==='string' && item.id.startsWith('memo-') && typeof item.text === 'string')
      notes.value.push({id:item.id,title:'我的便签',color:/^#[0-9a-f]{6}$/i.test(item.color)?item.color:'#fff0bf',size:limit(item.size,140,420,235),text:item.text,...point})
    else if (typeof item.id==='string' && item.id.startsWith('decal-') && Object.hasOwn(decals,item.kind))
      notes.value.push({id:item.id,kind:item.kind,title:decals[item.kind].name,size:limit(item.size,45,360,135),opacity:limit(item.opacity,.1,1,1),angle:limit(item.angle,-360,360,0),...point})
  }
}
const board = ref(null), selected = ref(''), storageError = ref(false)
let drag
function clamp(value){ return Math.max(0,Math.min(1,value)) }
function save(){
  try { if(props.owner != null) localStorage.setItem(key,JSON.stringify({notes:notes.value,hidden:hidden.value,weather:weather.value})); storageError.value=false }
  catch {storageError.value=true}
}
async function add(){
  const id = 'memo-' + crypto.randomUUID()
  const offset = (notes.value.length % 5)*.04
  notes.value.push({id,title:'我的便签',text:'',...draft.value,x:.35+offset,y:.35+offset})
  selected.value=id;dialog.value.close()
  save();await nextTick();document.getElementById(id)?.focus()
}
function begin(e,n){
  if (e.button!==0 || drag) return
  const card=e.currentTarget.parentElement
  drag={id:e.pointerId,x:e.clientX,y:e.clientY,startX:n.x,startY:n.y,
    width:Math.max(1,board.value.clientWidth-card.offsetWidth),height:Math.max(1,board.value.clientHeight-card.offsetHeight)}
  selected.value=n.id;e.currentTarget.setPointerCapture(e.pointerId)
}
function move(e,n){
  if(drag?.id!==e.pointerId)return
  n.x=clamp(drag.startX+(e.clientX-drag.x)/drag.width)
  n.y=clamp(drag.startY+(e.clientY-drag.y)/drag.height)
}
function startCorner(e,n){
  if(e.button!==0 || drag)return
  const card=e.currentTarget.parentElement
  const rect=card.getBoundingClientRect()
  const area=board.value.getBoundingClientRect()
  const cx=rect.left+rect.width/2, cy=rect.top+rect.height/2
  const dx=e.clientX-cx, dy=e.clientY-cy
  drag={id:e.pointerId,cx,cy,area,size:card.offsetWidth,ratio:card.offsetHeight/card.offsetWidth,
    radius:Math.max(1,Math.hypot(dx,dy)),direction:Math.atan2(dy,dx),angle:n.angle || 0}
  e.currentTarget.setPointerCapture(e.pointerId)
}
function transformCorner(e,n){
  if(drag?.id!==e.pointerId || !drag.area)return
  const dx=e.clientX-drag.cx, dy=e.clientY-drag.cy
  const {area,ratio}=drag
  n.size=limit(drag.size*Math.hypot(dx,dy)/drag.radius,45,Math.min(360,area.width*.9),135)
  n.angle=(drag.angle+(Math.atan2(dy,dx)-drag.direction)*180/Math.PI)%360
  n.x=clamp((drag.cx-area.left-n.size/2)/Math.max(1,area.width-n.size))
  const height=n.size*ratio
  n.y=clamp((drag.cy-area.top-height/2)/Math.max(1,area.height-height))
}
function keyCorner(e,n){
  if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))return
  e.preventDefault()
  if(e.key==='ArrowLeft'||e.key==='ArrowRight')n.angle=((n.angle||0)+(e.key==='ArrowLeft'?-5:5))%360
  else n.size=limit(n.size+(e.key==='ArrowUp'?5:-5),45,360,135)
  save()
}
function end(e){if(drag?.id===e.pointerId){drag=null;save()}}
function nudge(e,n){
  const delta={ArrowLeft:[-.025,0],ArrowRight:[.025,0],ArrowUp:[0,-.025],ArrowDown:[0,.025]}[e.key]
  if(!delta)return
  e.preventDefault();n.x=clamp(n.x+delta[0]);n.y=clamp(n.y+delta[1]);selected.value=n.id;save()
}
</script>
<template>
<section class="tag-wall" aria-label="标签墙" :style="{backgroundImage:weather==='original'?undefined:'url('+asset(weather)+')'}">
  <header class="wall-tools"><h1>{{ greeting }}</h1><button @click="openTools('new')">＋ 新增便签</button><button @click="openTools('decor')">✧ 装饰小墙</button></header>
  <div class="wall-scroll"><div ref="board" class="pin-area">
    <article v-for="n in notes" :key="n.id" class="wall-paper" :class="{raised:selected===n.id, decal:n.kind, memo:'text' in n}" @contextmenu.prevent="openTools('edit',n)" :style="{left:n.x*100+'%',top:n.y*100+'%',translate:(-n.x*100)+'% '+(-n.y*100)+'%','--paper':n.color,'--ink':n.color?ink(n.color):undefined,'--size':n.size+'px',rotate:n.kind?(n.angle||0)+'deg':undefined}" @focusin="selected=n.id" @pointerdown="selected=n.id">
      <button class="pin-handle" :aria-label="'移动'+n.title+'，可用方向键微调'" @pointerdown="begin($event,n)" @pointermove="move($event,n)" @lostpointercapture="end" @keydown="nudge($event,n)"><img v-if="n.kind" :src="asset(n.kind)" :alt="n.title" draggable="false" :style="{opacity:n.opacity}"><template v-else>{{ n.title }}</template></button>
      <template v-if="n.kind && selected===n.id">
        <button v-for="corner in ['nw','ne','sw','se']" :key="corner" class="corner-grip" :class="corner" aria-label="缩放并旋转贴纸，上下调整大小，左右旋转" @pointerdown.stop.prevent="startCorner($event,n)" @pointermove="transformCorner($event,n)" @lostpointercapture="end" @keydown="keyCorner($event,n)"></button>
      </template>
      <button class="paper-options" :aria-label="'设置'+n.title" @click="openTools('edit',n)">⋯</button>
      <textarea v-if="'text' in n" :id="n.id" v-model="n.text" aria-label="便签正文" placeholder="记下一个想法…" maxlength="3000" @input="save"></textarea>
      <template v-else-if="n.kind"></template>
      <template v-else-if="n.id==='entries'"><router-link v-for="item in entries" :key="item.title" :to="item.route || '/courses'">{{ item.title }} ↗</router-link></template>
      <template v-else-if="status!=='ready'"><p>{{ status==='error'?'数据加载失败':'正在整理记录…' }}</p><button v-if="status==='error'" @click="$emit('retry')">重新加载</button></template>
      <template v-else-if="n.id==='weekly'"><strong>{{ weekly.sessions }} <small>次</small></strong><p>累计 {{ weekly.total_minutes }} 分钟</p><button @click="$emit('panel','weekly')">训练日志 ↗</button></template>
      <template v-else-if="n.id==='course'"><b>{{ course?.course_title || '模拟课堂' }}</b><progress v-if="course" :value="course.progress_percent" max="100" aria-label="课程进度"/><button v-if="course" @click="$emit('resume')">继续训练 ↗</button><router-link v-else to="/training">开始新训练 ↗</router-link></template>
      <template v-else-if="n.id==='feedback'"><strong v-if="feedback">{{ feedback.overall_score }} <small>分</small></strong><p v-else>完成训练后查看反馈</p><button v-if="feedback" @click="$emit('panel','feedback')">查看评课 ↗</button><router-link v-else to="/ai-review">打开档案袋 ↗</router-link></template>
      <template v-else><div v-if="growth.length" class="pin-chart" :aria-label="'历史得分 '+growth.join('、')"><i v-for="(score,i) in growth.slice(-12)" :key="i" :style="{height:score+'%'}" :title="String(score)"></i></div><p v-else>等待第一次训练记录</p><button @click="$emit('panel','growth')">查看轨迹 ↗</button></template>
    </article>
  </div></div>
  <dialog ref="dialog" class="wall-dialog" aria-labelledby="wall-dialog-title" @click="e=>{if(e.target===dialog)dialog.close()}">
    <section><header><h2 id="wall-dialog-title">{{ tab==='decor'?'装饰小墙':tab==='new'?'新增便签':target?.title }}</h2><button aria-label="关闭" @click="dialog.close()">×</button></header>
    <template v-if="tab==='decor'">
      <h3>窗外的天气</h3><div class="sky-picker"><button v-for="(label,id) in skies" :key="id" :aria-pressed="weather===id" @click="weather=id;save()"><img :src="id==='original'?'/assets/desk/tag-wall.png':asset(id)" alt="">{{ label }}</button></div>
      <h3>涂鸦册 <small>Lv.{{ level }}</small></h3><p v-if="levelError" role="status">等级暂未同步，重新打开可重试。</p>
      <div class="decal-picker"><button v-for="(d,id) in decals" :key="id" :disabled="level<d.level" @click="paste(id)"><img :src="asset(id)" alt="">{{ d.name }}<small>Lv.{{ d.level }} 解锁</small></button></div>
      <button v-if="hidden.length" @click="restore">恢复数据便签</button>
    </template>
    <template v-else-if="tab==='new'">
      <label>纸色<input type="color" v-model="draft.color"></label><label>大小 · {{ draft.size }} px<input type="range" min="140" max="420" v-model.number="draft.size"></label>
      <button class="wall-primary" @click="add">贴上便签</button>
    </template>
    <template v-else-if="target">
      <label v-if="'text' in target">纸色<input type="color" v-model="target.color" @input="save"></label>
      <label v-if="'text' in target">大小 · {{ target.size }} px<input type="range" :min="target.kind?45:140" :max="target.kind?360:420" v-model.number="target.size" @input="save"></label>
      <label v-if="target.kind">不透明度 · {{ Math.round(target.opacity*100) }}%<input type="number" min="10" max="100" :value="Math.round(target.opacity*100)" @change="target.opacity=limit($event.target.valueAsNumber/100,.1,1,target.opacity);$event.target.value=Math.round(target.opacity*100);save()"></label>
      <button @click="remove">从墙上删除</button>
    </template></section>
  </dialog>
  <p v-if="storageError" role="status">浏览器暂时无法保存便签</p>
  <router-link class="wall-down" to="/courses" aria-label="向下前往办公桌"><img src="/assets/desk/wood-arrow.webp" alt=""></router-link>
</section>
</template>
<style scoped>
.tag-wall {position:relative;height:100%;min-height:0;isolation:isolate;overflow:hidden;background:#e9a779 url('/assets/desk/tag-wall.png') center/cover;color:#3d3029}
.wall-tools {position:absolute;left:4%;top:7%;z-index:2;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.wall-tools h1 {margin:0;font:700 clamp(20px,2.1vw,34px)/1.1 "Songti SC",SimSun,serif;color:#44271e;text-shadow:0 1px #fff1d9}
.wall-tools button {border:1px solid #eed0a5;border-radius:22px;background:#44382e;color:#fff2d9;padding:8px 15px}
.wall-scroll {position:absolute;inset:18% 6% 10%;overflow:auto;padding:9px;scrollbar-width:thin}
.pin-area {position:relative;height:100%;min-height:330px}
.wall-paper {position:absolute;width:clamp(154px,18vw,242px);background:linear-gradient(155deg,#fff5,transparent 65%),var(--paper);padding:15px 16px 14px;box-shadow:1px 5px 7px #512d243b,0 1px 1px #533b3444;color:#39332e;border-radius:2px 3px 9px 2px;display:grid;gap:7px;rotate:-1deg}
.wall-paper:nth-child(even){rotate:1deg}
.wall-paper.raised {z-index:1}
.wall-paper::before {content:"";position:absolute;top:3px;left:48%;width:8px;height:8px;border-radius:50%;background:radial-gradient(circle at 35% 20%,#fff0c6,#a76144 50%,#703b2a);box-shadow:1px 2px 2px #0004;pointer-events:none}
.wall-paper .pin-handle {touch-action:none;cursor:grab;user-select:none;text-align:left;font-weight:700;font-size:17px;border-bottom:1px dashed #60544855;padding:5px 0;color:#403730}
.wall-paper .pin-handle:active {cursor:grabbing}
.wall-paper button,.wall-paper a {background:transparent;border:none;color:#504033;text-align:left;padding:2px 0;font-size:13px;text-decoration:none}
.wall-paper a:hover,.wall-paper button:not(.pin-handle):hover{text-decoration:underline}
.wall-paper strong {font:600 32px/1.1 Georgia,serif}.wall-paper small,.wall-paper p {font-size:13px;margin:0}
.wall-paper textarea {resize:none;border:0;color:inherit;background:transparent;width:100%;height:76px;font:inherit;line-height:1.6}
.wall-paper progress {width:100%;height:7px;accent-color:#3d786d}
.pin-chart {display:flex;align-items:flex-end;height:45px;gap:4px}.pin-chart i{flex:1;background:#537a9b;border-radius:3px 3px 0 0}
.wall-down {position:absolute;bottom:1%;left:50%;translate:-50%;width:clamp(44px,5vw,74px);display:grid;place-items:center;aspect-ratio:1}
.wall-down img {width:100%;rotate:-90deg;filter:drop-shadow(0 3px 3px #42251788)}
@media(max-width:700px){.wall-tools{top:68px;left:16px}.wall-scroll{inset:122px 8px 55px}.pin-area{min-height:630px}.wall-paper{width:44%;padding:14px 10px}}

.wall-paper {width:min(30%,320px);min-height:146px;align-content:start;padding:19px 21px;color:var(--ink);gap:9px}
.wall-paper strong{font-size:40px}.wall-paper .pin-handle{font-size:20px;padding-right:24px;color:inherit}
.wall-paper.memo {width:min(var(--size),98%);min-height:0}.wall-paper.memo textarea{height:clamp(60px,calc(var(--size)*.49),210px)}
.wall-paper .paper-options{position:absolute;right:6px;top:11px;width:29px;height:29px;text-align:center;border-radius:50%;color:inherit}
.wall-paper.decal{width:min(var(--size),90%);min-height:0;display:block;padding:0;background:none;box-shadow:none;rotate:0}
.wall-paper.decal::before{display:none}.wall-paper.decal .pin-handle{display:block;width:100%;padding:0;border:0}.decal img{display:block;width:100%;user-select:none}
.decal .paper-options{background:#fff3da;opacity:0}.decal:is(:focus-within,:hover) .paper-options{opacity:1}
.wall-dialog{width:min(420px,94vw);max-height:82dvh;overflow:auto;padding:0;border:1px solid #caa786;border-radius:18px;color:#392d28;background:#fff6e8;box-shadow:0 18px 64px #301b2350}
.wall-dialog::backdrop{background:#38231b50}.wall-dialog section{padding:18px}.wall-dialog header,.wall-dialog label{display:flex;align-items:center;justify-content:space-between;gap:12px}
.wall-dialog h2,.wall-dialog h3{margin:0}.wall-dialog h2{font-size:20px}.wall-dialog h3{font-size:15px;margin:16px 0 8px}
.wall-dialog small{font-weight:400;font-size:11px}.wall-dialog button{color:inherit;background:#fffaf1;border:1px solid #bfa68d;border-radius:9px;padding:6px 10px}
.wall-dialog label{margin:18px 0}.wall-dialog input{max-width:55%;accent-color:#74583c}
.sky-picker,.decal-picker{display:grid;grid-template-columns:repeat(3,1fr);gap:6px}
.wall-dialog .sky-picker button,.wall-dialog .decal-picker button{padding:4px;font-size:12px}
.sky-picker img{display:block;width:100%;height:38px;object-fit:cover;border-radius:5px}.decal-picker img{display:block;width:100%;height:50px;object-fit:contain}.decal-picker small{display:block}
.sky-picker [aria-pressed=true]{outline:2px solid #74583c}.decal-picker :disabled{opacity:.52;cursor:default}
@media(max-width:700px){.wall-paper:not(.memo,.decal){width:47%;min-height:138px;padding:15px 10px}.wall-tools{gap:5px}.wall-tools h1{font-size:18px}.wall-tools button{padding:6px 8px}.pin-area{min-height:720px}}

.wall-paper.decal.raised{outline:1px dashed #594937aa}
.wall-paper .corner-grip{position:absolute;z-index:2;width:24px;height:24px;padding:0;touch-action:none;cursor:crosshair;translate:-50% -50%;display:grid;place-items:center}
.corner-grip::after{content:"";width:10px;height:10px;border:1px solid #5e4230;background:#fff9da;border-radius:50%;box-shadow:0 1px 3px #49362950}
.corner-grip.nw,.corner-grip.sw{left:0}.corner-grip.ne,.corner-grip.se{left:100%}
.corner-grip.nw,.corner-grip.ne{top:0}.corner-grip.sw,.corner-grip.se{top:100%}
</style>
