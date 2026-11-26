<script setup>
import SceneLink from '../components/SceneLink.vue';
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Refresh, Printer, History } from '@vicons/tabler';
import { api } from '../services/api';
import { classroomDestination, formatReportDate, formatReportTime } from '../services/classroomReview.js';
import ClassroomReport from '../components/ClassroomReport.vue';
import ArchiveCoverBag from '../components/ArchiveCoverBag.vue';
import ArchivePlantGlow from '../components/ArchivePlantGlow.vue';
import ModelShowcase from '../components/fx/ModelShowcase.vue';
import '../classroom.css';
import '../classroom-review.css';
const route=useRoute(), router=useRouter();
const room=ref(null), history=ref([]), loading=ref(true), busy=ref(false), error=ref(''), historyError=ref('');
const historyLoading=ref(false);
const archiveSceneElement=ref(null);
const archivePaperOverlay=ref(null);
const archiveOpeningSeenKey='link.archive-opening-seen.v1';
function hasSeenArchiveOpening(){try{return localStorage.getItem(archiveOpeningSeenKey)==='true'}catch{return false}}
const archiveAlreadyOpened=hasSeenArchiveOpening();
const archivePapersVisible=ref(archiveAlreadyOpened);
const archiveBagDone=ref(archiveAlreadyOpened);
const archiveVideoStarted=ref(false), archiveVideoVisible=ref(false), archiveOpeningVideo=ref(null);
let archiveVideoEndTimer=null;
let archiveOverlayResizeObserver=null;
let disposed=false, controller=null, pollTimer=null, requestId=0;
const stateLabel=state=>({completed:'已评课',running:'评课中',insufficient:'数据不足',failed:'生成失败',idle:'待评课'}[state]||'待评课');
const endedHistory=computed(()=>history.value.filter(item=>item.state==='ended'));
const archiveReports=computed(()=>history.value
  .filter(item=>item.state==='ended'&&item.report_state==='completed'&&item.report)
  .sort((a,b)=>new Date(b.created_at||0)-new Date(a.created_at||0))
  .slice(0,5));
const archiveHistoryPlacements=[
  {polygon:'168,389 343,324 405,419 226,510',transform:'rotate(-20 280 400)',x:226,y:385},
  {polygon:'914,264 1090,276 1058,365 898,352',transform:'rotate(8 990 318)',x:928,y:300},
  {polygon:'273,283 389,251 438,322 322,363',transform:'rotate(-15 350 304)',x:322,y:296},
  {polygon:'743,216 940,205 902,281 748,297',transform:'rotate(-4 840 251)',x:770,y:244},
];
// Perspective of the top report sheet, mapped to the 1200×675 background image.
const archiveReportPaperTransform='matrix(0.97 0.08 -0.13 0.94 520 246)';
const selectedId=computed(()=>String(room.value?.session_id||route.query.classroom||''));
const archiveSceneOnly=computed(()=>!route.query.classroom&&!route.query.sessionId&&!route.query.feedbackId&&!route.query.demo);
watch(archiveSceneOnly, isSceneOnly=>{
  if(isSceneOnly){
    clearTimeout(archiveVideoEndTimer);
    archiveOpeningVideo.value?.pause();
    archiveVideoStarted.value=false;archiveVideoVisible.value=false;
    const seen=hasSeenArchiveOpening();
    archivePapersVisible.value=seen;archiveBagDone.value=seen;
  }
});
async function playArchiveOpening(){
  archiveVideoStarted.value=true;archiveVideoVisible.value=true;
  await nextTick();
  try { await archiveOpeningVideo.value?.play(); }
  catch { finishArchiveOpening(); }
}
function finishArchiveOpening(){
  if(!archiveVideoStarted.value || archiveBagDone.value || disposed)return;
  try{localStorage.setItem(archiveOpeningSeenKey,'true')}catch{}
  archivePapersVisible.value=true;archiveBagDone.value=true;archiveVideoVisible.value=false;
  archiveOpeningVideo.value?.pause();
  clearTimeout(archiveVideoEndTimer);
  // Keep the final video frame mounted until the scene crossfade has completed.
  archiveVideoEndTimer=setTimeout(()=>{archiveVideoStarted.value=false;},1500);
}
function placeArchivePaperOverlay(){
  const scene=archiveSceneElement.value, overlay=archivePaperOverlay.value;
  const background=scene?.querySelector('.archive-scene-papers');
  if(!scene||!overlay||!background)return;
  const sceneRect=scene.getBoundingClientRect(), imageRect=background.getBoundingClientRect();
  if(!imageRect.width||!imageRect.height)return;
  const naturalWidth=background.naturalWidth||3344, naturalHeight=background.naturalHeight||1882;
  const imageScale=Math.max(imageRect.width/naturalWidth,imageRect.height/naturalHeight);
  const scale=imageScale*naturalWidth/1200;
  const renderedWidth=1200*scale, renderedHeight=675*scale;
  overlay.style.left=`${imageRect.left-sceneRect.left+(imageRect.width-renderedWidth)/2}px`;
  overlay.style.top=`${imageRect.top-sceneRect.top+(imageRect.height-renderedHeight)/2}px`;
  overlay.style.width=`${renderedWidth}px`;overlay.style.height=`${renderedHeight}px`;
}
function openArchiveReport(item){if(!archivePapersVisible.value||!item?.session_id)return;router.push({path:'/ai-review',query:{classroom:String(item.session_id)}});}
function archiveReportKeydown(event,item){if(event.key==='Enter'||event.key===' '){event.preventDefault();openArchiveReport(item);}}
function openGmqArchiveReport(){if(!archivePapersVisible.value)return;router.push({path:'/ai-review',query:{demo:'gmq'}});}
function gmqArchiveReportKeydown(event){if(event.key==='Enter'||event.key===' '){event.preventDefault();openGmqArchiveReport();}}
function shortArchiveDate(value){return formatReportDate(value).split(/\s+/)[0];}
watch(archivePapersVisible,async visible=>{if(visible){await nextTick();placeArchivePaperOverlay();}});
function selectHistory(event){router.push({path:'/ai-review',query:{classroom:event.target.value}});}
function schedulePoll(){
  clearTimeout(pollTimer);
  if (!disposed && room.value?.report_state==='running') pollTimer=setTimeout(()=>{
    if (document.visibilityState==='hidden') schedulePoll();
    else loadRoom(room.value.session_id);
  },4000);
}
async function loadRoom(id){
  const current=++requestId;
  controller?.abort(); controller=new AbortController();
  try {
    const {data}=await api.get(`/classroom/sessions/${id}`,{timeout:15000,skipBusy:true,signal:controller.signal});
    if(disposed || current!==requestId)return;
    room.value=data;error.value='';
  } catch(e){
    if(disposed || current!==requestId)return;
    error.value=e.response?.status===404 ? '这节课堂不存在，或你没有查看权限。请选择其他课堂。' :
      e.response?.status===401 ? '登录已失效，请重新登录后查看报告。' : '报告读取失败，暂未取得最新结果。请重试。';
  } finally {if(!disposed && current===requestId){loading.value=false;schedulePoll();}}
}
async function loadHistory(){
  historyLoading.value=true;historyError.value='';
  try {const {data}=await api.get('/classroom/sessions',{timeout:15000,skipBusy:true});if(!disposed)history.value=data.items||[];}
  catch {if(!disposed)historyError.value='历史报告暂时无法读取。';}
  finally {historyLoading.value=false;}
}
async function initialize(){
  loading.value=true; error.value=''; historyError.value='';
  const historyPromise=loadHistory();
  const id=route.query.classroom;
  if(id===undefined){loading.value=false;await historyPromise;return;}
  if(id!==undefined && (typeof id!=='string' || !/^[1-9]\d*$/.test(id) || !Number.isSafeInteger(Number(id)))){
    error.value='课堂编号无效，请从历史课堂重新进入。';loading.value=false;await historyPromise;return;
  }
  await Promise.all([historyPromise,loadRoom(id)]);
}
async function regenerate(objection){
  if(busy.value || !room.value || room.value.report_state==='running' ||
    (room.value.report_state==='insufficient' && !room.value.report_readiness?.eligible))return;
  busy.value=true;error.value='';
  try {
    const {data}=await api.post(`/classroom/sessions/${room.value.session_id}/report`,{objection},{timeout:20000,skipBusy:true});
    if(disposed)return;
    room.value={...room.value,...data};
    await loadRoom(room.value.session_id);
  } catch(e){if(!disposed)error.value=e.response?.data?.message||'评课请求未确认，请刷新状态后再决定是否重试。';}
  finally {if(!disposed)busy.value=false;}
}
function printReport(){window.print();}
let printFolds=[];
function preparePrint(){
  printFolds=[...document.querySelectorAll('.evidence-report :is(.report-fold,.dimension-sources):not([open])')];
  printFolds.forEach(fold=>{fold.open=true;});
}
function restorePrint(){printFolds.forEach(fold=>{fold.open=false;});printFolds=[];}
onMounted(initialize);
onMounted(()=>{archiveOverlayResizeObserver=new ResizeObserver(placeArchivePaperOverlay);if(archiveSceneElement.value)archiveOverlayResizeObserver.observe(archiveSceneElement.value);window.addEventListener('beforeprint',preparePrint);window.addEventListener('afterprint',restorePrint);});
onBeforeUnmount(()=>{disposed=true;requestId++;controller?.abort();clearTimeout(pollTimer);clearTimeout(archiveVideoEndTimer);archiveOpeningVideo.value?.pause();archiveOverlayResizeObserver?.disconnect();window.removeEventListener('beforeprint',preparePrint);window.removeEventListener('afterprint',restorePrint);});
</script>
<template>
  <div class="classroom-review-page" :class="{'classroom-review-page--scene-only':archiveSceneOnly}">
    <div ref="archiveSceneElement" class="archive-scene" :class="{'archive-scene--full':archiveSceneOnly}" :aria-hidden="archiveSceneOnly?undefined:'true'">
      <img class="archive-scene-base" :class="{'is-hidden':archivePapersVisible}" :src="archiveSceneOnly?'/assets/archive-cover.png':'/assets/archive-reports-scene.png'" alt="" />
      <img v-if="archiveSceneOnly" class="archive-scene-papers" :class="{'is-visible':archivePapersVisible}" src="/assets/growth-archive-desk.png" alt="" @load="placeArchivePaperOverlay" />
      <ArchivePlantGlow v-if="archiveSceneOnly" :scene-element="archiveSceneElement" />
      <ArchiveCoverBag v-if="archiveSceneOnly && !archiveBagDone" :scene-element="archiveSceneElement" @play-video="playArchiveOpening" />
      <svg v-if="archiveSceneOnly" ref="archivePaperOverlay" class="archive-paper-report-overlay" :class="{'is-visible':archivePapersVisible}" viewBox="0 0 1200 675" preserveAspectRatio="none" role="group" aria-label="白纸上的最近和历史评课报告">
        <g v-for="(item,historyIndex) in (archivePapersVisible?archiveReports.slice(1,5):[])" :key="item.session_id" class="archive-paper-history" :transform="archiveHistoryPlacements[historyIndex]?.transform" role="link" tabindex="0" :aria-label="`历史报告，${shortArchiveDate(item.created_at)}，点击查看`" @click="openArchiveReport(item)" @keydown="archiveReportKeydown($event,item)">
          <title>{{ `历史评课报告 · ${formatReportDate(item.created_at)}` }}</title>
          <polygon :points="archiveHistoryPlacements[historyIndex]?.polygon" class="archive-paper-hit-area" />
          <text :x="archiveHistoryPlacements[historyIndex]?.x" :y="archiveHistoryPlacements[historyIndex]?.y" class="archive-paper-history-title">历史报告 · {{ shortArchiveDate(item.created_at) }}</text>
          <text :x="archiveHistoryPlacements[historyIndex]?.x" :y="archiveHistoryPlacements[historyIndex]?.y+17" class="archive-paper-placeholder">×××××× ××××××</text>
          <text :x="archiveHistoryPlacements[historyIndex]?.x" :y="archiveHistoryPlacements[historyIndex]?.y+31" class="archive-paper-placeholder">××××××××××</text>
        </g>
        <g v-if="archivePapersVisible&&archiveReports[0]" class="archive-paper-latest" role="link" tabindex="0" :aria-label="`最近一次评课报告：${archiveReports[0].topic||'课堂评课'}，${formatReportDate(archiveReports[0].created_at)}，点击查看`" @click="openArchiveReport(archiveReports[0])" @keydown="archiveReportKeydown($event,archiveReports[0])">
          <title>最近一次评课报告，点击打开完整报告</title>
          <polygon points="525,224 862,245 816,492 524,451" class="archive-paper-hit-area" />
          <g :transform="archiveReportPaperTransform">
            <text x="12" y="35" class="archive-paper-latest-heading">最近一次评课报告</text>
            <text x="12" y="66" class="archive-paper-latest-copy">报告日期：{{ shortArchiveDate(archiveReports[0].created_at) }}</text>
            <text x="12" y="97" class="archive-paper-latest-copy">课堂：{{ String(archiveReports[0].topic||'课堂评课').slice(0,14) }}</text>
            <text v-if="Number.isFinite(archiveReports[0].report?.overall_score)" x="12" y="128" class="archive-paper-latest-score">综合评分　{{ Math.round(archiveReports[0].report.overall_score) }} 分</text>
            <path d="M12 141 L230 141" class="archive-paper-rule" />
            <text x="12" y="165" class="archive-paper-placeholder">课堂证据与改进建议</text>
          </g>
        </g>
        <g v-else-if="archivePapersVisible" class="archive-paper-latest archive-paper-empty" role="link" tabindex="0" aria-label="打开 GMQ 试讲示例报告" @click="openGmqArchiveReport" @keydown="gmqArchiveReportKeydown">
          <title>GMQ 试讲示例报告，点击打开</title>
          <polygon points="525,224 862,245 816,492 524,451" class="archive-paper-hit-area" />
          <g :transform="archiveReportPaperTransform">
            <text x="12" y="35" class="archive-paper-latest-heading">GMQ 试讲报告</text>
            <text x="12" y="66" class="archive-paper-latest-copy">点击打开示例报告</text>
            <text x="12" y="97" class="archive-paper-placeholder">×××××× ××××××</text>
          </g>
        </g>
      </svg>
      <SceneLink direction="right" v-if="archiveSceneOnly" class="archive-desk-return" to="/courses" aria-label="返回办公桌">
        <img src="/assets/desk/wood-arrow.webp" alt="" />
      </SceneLink>
      <video v-if="archiveSceneOnly && archiveVideoStarted" ref="archiveOpeningVideo" class="archive-opening-video" :class="{'is-visible':archiveVideoVisible}" src="/assets/archive-opening.mp4?v=muted-20261125" playsinline muted preload="auto" @ended="finishArchiveOpening" @error="finishArchiveOpening" />
      <button v-if="archiveSceneOnly && archiveVideoVisible" type="button" class="archive-video-skip" @click.stop="finishArchiveOpening">跳过视频</button>
    </div>
    <template v-if="!archiveSceneOnly">
      <header class="review-masthead">
        <h1 class="sr-only">AI 评课</h1>
        <router-link class="review-button" :to="{path:'/ai-review',query:{demo:'gmq'}}">GMQ 试讲报告示例</router-link>
      </header>
      <p v-if="historyError" class="review-inline-alert" role="alert">{{ historyError }}</p>
      <div v-if="error" class="review-inline-alert" role="alert">{{ error }}<button class="review-button" :disabled="loading || busy" @click="initialize">重新读取</button><router-link to="/">重新登录</router-link></div>
      <section v-if="loading && !room" class="review-empty-state" role="status"><span class="review-loading-line" />正在读取课堂证据…</section>
      <template v-if="room">
        <div class="review-session-meta"><span>课堂 #{{ room.session_id }} · {{ room.topic }}</span><span>{{ formatReportDate(room.created_at) }} · {{ formatReportTime(Number.isFinite(room.elapsed)?room.elapsed*1000:NaN) }}</span></div>
        <section v-if="['active','paused'].includes(room.state)" class="review-empty-state"><h2>这节课堂还未结束</h2><p>课堂结束后再根据已保存的证据整理教练反馈。</p><router-link class="review-button" :to="classroomDestination(room)">返回课堂</router-link></section>
        <ClassroomReport v-else :room="room" :busy="busy" @regenerate="regenerate" @plans-created="loadRoom(room.session_id)" @refresh="loadRoom(room.session_id)" @print="printReport" />
      </template>
    </template>
  </div>
</template>
