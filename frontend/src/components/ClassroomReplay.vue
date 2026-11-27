<script setup>
import {ref,watch,onBeforeUnmount,nextTick,computed} from 'vue';
import {useAuthStore} from '../stores/auth';
import {getClassroomRecording,listClassroomRecordings,deleteClassroomRecording,recordingTime} from '../services/classroomRecordingStore.js';
const PROJECT_VIDEO_DURATION_MS=599008;
const props=defineProps({room:Object,event:Object,recordingSrc:String,recordingTitle:String});
const auth=useAuthStore(),video=ref(null),url=ref(''),record=ref(null),error=ref(''),notice=ref(''),loading=ref(false),items=ref([]),videoDuration=ref(0);
const currentTime=ref(0),dragging=ref(false),isPlaying=ref(false),muted=ref(false),volume=ref(1),playbackRate=ref(1),speedMenuOpen=ref(false),videoAspectRatio=ref(16/9);
const playbackRates=[0.75,1,1.25,1.5,2];
let revision=0,dragPointerId=null;
const isDemo=computed(()=>props.room?.report?.demo===true);
const duration=computed(()=>record.value?.static?PROJECT_VIDEO_DURATION_MS:(videoDuration.value||record.value?.durationMs||0));
const markers=computed(()=>{
  const span=duration.value;
  if(!span)return [];
  const timedEvents=(props.room?.events||[]).filter(e=>isDemo.value || (Number.isFinite(e.at_ms)&&e.at_ms>=0&&e.at_ms<=span));
  const evidenceIds=new Set([
    ...(props.room?.report?.coaching_focuses||[]).flatMap(item=>item.evidence_ids||[]),
    ...(props.room?.report?.dimensions||[]).flatMap(item=>item.event_ids||[]),
  ]);
  const selected=timedEvents.filter(event=>evidenceIds.has(event.id));
  const events=(selected.length?selected:timedEvents)
    .sort((a,b)=>(a.at_ms??0)-(b.at_ms??0))
    .slice(0,40);
  return events.map((e,index)=>{
    const at=isDemo.value ? (events.length===1 ? span/2 : span*index/(events.length-1)) : e.at_ms;
    return {id:e.id,at,left:`${Math.max(0,Math.min(100,at/span*100))}%`,label:`${Math.floor(at/60000)}:${String(Math.floor(at/1000)%60).padStart(2,'0')}`};
  });
});
function release(){video.value?.pause();isPlaying.value=false;if(url.value.startsWith('blob:'))URL.revokeObjectURL(url.value);url.value='';record.value=null;videoDuration.value=0;videoAspectRatio.value=16/9;currentTime.value=0;dragging.value=false;dragPointerId=null;}
async function load(){
  const id=++revision;release();error.value='';items.value=[];
  if(props.recordingSrc){
    record.value={static:true,filename:props.recordingTitle||'课堂录像',byteLength:131220613,durationMs:PROJECT_VIDEO_DURATION_MS,segments:[],mimeType:'video/webm'};
    url.value=props.recordingSrc;
    await nextTick();seek();
    return;
  }
  if(!auth.user?.id || !props.room?.session_id)return;
  if(isDemo.value){
    record.value={demo:true,filename:'LINK-模拟课堂回放.mp4',byteLength:0,durationMs:18000,segments:[{wallStart:0,wallEnd:18000,videoStart:0}],mimeType:'video/mp4'};
    url.value='/assets/mock-classroom.mp4';
    await nextTick();seek();
    return;
  }
  loading.value=true;
  try {
    const [row,list]=await Promise.all([getClassroomRecording(location.origin,auth.user.id,props.room.session_id),listClassroomRecordings(location.origin,auth.user.id)]);
    if(id!==revision)return;
    record.value=row;items.value=list;if(row)url.value=URL.createObjectURL(row.blob);
    await nextTick();seek();
  } catch {if(id===revision)error.value='本机录像读取失败，可重试；报告仍可查看。';}
  finally{if(id===revision)loading.value=false;}
}
function seek(){
  notice.value='';
  if(!record.value || !props.event)return;
  const at=recordingTime(record.value.segments,props.event.at_ms);
  if(at===null){video.value?.pause();notice.value='该时段无录像，请查看下方原始事件。';return;}
  if(video.value?.readyState>=1){video.value.currentTime=at;video.value.play().catch(()=>{notice.value='已定位，点击播放查看。';});}
}
function jump(at){
  const player=video.value;
  if(!player)return;
  const target=Math.max(0,Number(at)/1000);
  player.pause();
  player.currentTime=target;
  player.play().catch(()=>{notice.value=`已跳转到 ${Math.floor(target/60)}:${String(Math.floor(target%60)).padStart(2,'0')}，点击播放器继续播放。`;});
}
async function togglePlayback(){
  if(!video.value)return;
  if(video.value.paused){try{await video.value.play();}catch{notice.value='播放失败，请检查录像格式或浏览器支持。';}}
  else video.value.pause();
}
function toggleMute(){if(!video.value)return;video.value.muted=!video.value.muted;muted.value=video.value.muted;}
function updateVolume(event){if(!video.value)return;const value=Number(event.target.value);video.value.volume=value;if(value>0)video.value.muted=false;volume.value=value;muted.value=video.value.muted;}
function setPlaybackRate(rate){
  playbackRate.value=rate;
  if(video.value)video.value.playbackRate=playbackRate.value;
  speedMenuOpen.value=false;
}
function syncPlaybackRate(){if(video.value)playbackRate.value=video.value.playbackRate;}
async function toggleFullscreen(){
  const shell=video.value?.parentElement;
  if(!shell)return;
  try{if(document.fullscreenElement)await document.exitFullscreen();else await shell.requestFullscreen();}catch{notice.value='当前浏览器无法进入全屏。';}
}
function formatClock(seconds){
  const safe=Math.max(0,Math.floor(Number(seconds)||0)),hours=Math.floor(safe/3600),minutes=Math.floor(safe%3600/60),secs=safe%60;
  return hours?`${hours}:${String(minutes).padStart(2,'0')}:${String(secs).padStart(2,'0')}`:`${minutes}:${String(secs).padStart(2,'0')}`;
}
function seekFromRange(event){
  const player=video.value,target=Number(event.target.value);
  if(!player||!Number.isFinite(target))return;
  player.currentTime=target;currentTime.value=target;
}
function seekByKeyboard(event){
  const player=video.value;if(!player||!Number.isFinite(player.duration))return;
  const step=event.shiftKey?30:5;let target;
  if(event.key==='ArrowLeft')target=player.currentTime-step;
  else if(event.key==='ArrowRight')target=player.currentTime+step;
  else if(event.key==='Home')target=0;
  else if(event.key==='End')target=player.duration;
  else return;
  event.preventDefault();player.currentTime=Math.max(0,Math.min(player.duration,target));currentTime.value=player.currentTime;
}
function handleTimeUpdate(){if(!dragging.value&&video.value)currentTime.value=video.value.currentTime||0;}
function syncVideoDuration(){
  if(video.value){
    if(video.value.videoWidth>0&&video.value.videoHeight>0)videoAspectRatio.value=video.value.videoWidth/video.value.videoHeight;
    if(Number.isFinite(video.value.duration)&&video.value.duration>0){
      videoDuration.value=video.value.duration*1000;
      currentTime.value=Math.min(video.value.currentTime||0,video.value.duration);
    }
  }
}
function handleMetadata(){
  if(video.value)video.value.playbackRate=playbackRate.value;
  syncVideoDuration();
  seek();
}
async function remove(item){
  if(!window.confirm('删除这节课的本机录像？无法恢复；已下载副本不会被删除。'))return;
  try{await deleteClassroomRecording(location.origin,auth.user.id,item.sessionId);await load();}
  catch{error.value='删除失败，请重试。';}
}
function download(){if(!record.value)return;const a=document.createElement('a');a.href=url.value;a.download=record.value.filename;a.click();}
watch(()=>[props.room?.session_id,auth.user?.id,props.recordingSrc],load,{immediate:true});
watch(()=>props.event,seek);
onBeforeUnmount(()=>{revision++;release();});
</script>
<template>
  <section class="classroom-replay no-print" :aria-label="recordingTitle||'本机课堂录像'">
    <h3 v-if="recordingTitle" class="replay-title">{{ recordingTitle }}</h3>
    <p v-if="loading" role="status">正在读取本机录像…</p>
    <div v-if="url" class="replay-video-shell" :style="{'--replay-aspect-ratio':videoAspectRatio}">
      <video ref="video" :src="url" playsinline preload="metadata" aria-label="课堂证据录像" @loadedmetadata="handleMetadata" @durationchange="syncVideoDuration" @timeupdate="handleTimeUpdate" @play="isPlaying=true" @pause="isPlaying=false" @volumechange="muted=video.muted;volume=video.volume" @ratechange="syncPlaybackRate" @error="error='此录像格式无法在当前浏览器播放，可下载后查看。'" @click="togglePlayback" />
      <div v-if="duration>0" class="replay-player-controls" aria-label="课堂视频控制条">
        <div class="replay-controls-top">
          <button type="button" class="replay-control-button replay-play-button" :aria-label="isPlaying?'暂停':'播放'" @click="togglePlayback"><span v-if="isPlaying" class="replay-pause-glyph" aria-hidden="true"><i /><i /></span><span v-else class="replay-play-glyph" aria-hidden="true" /></button>
          <span class="replay-control-time">{{formatClock(currentTime)}} / {{formatClock(duration/1000)}}</span>
          <span class="replay-controls-spacer" />
          <button type="button" class="replay-control-button" :aria-label="muted?'取消静音':'静音'" @click="toggleMute">{{muted||volume===0?'静音':'音量'}}</button>
          <input class="replay-volume" type="range" min="0" max="1" step="0.05" :value="muted?0:volume" aria-label="音量" @input="updateVolume" />
          <div class="replay-speed-control">
            <button type="button" class="replay-control-button replay-speed-button" :aria-label="`播放速度，当前 ${playbackRate} 倍`" :aria-expanded="speedMenuOpen" aria-haspopup="menu" :title="`播放速度 ${playbackRate}×`" @click="speedMenuOpen=!speedMenuOpen">{{playbackRate}}×</button>
            <div v-if="speedMenuOpen" class="replay-speed-menu" role="menu" aria-label="选择播放速度" @keydown.esc="speedMenuOpen=false">
              <button v-for="rate in playbackRates" :key="rate" type="button" role="menuitemradio" :aria-checked="playbackRate===rate" :class="{'is-selected':playbackRate===rate}" @click="setPlaybackRate(rate)">{{rate}}×</button>
            </div>
          </div>
          <button type="button" class="replay-control-button replay-fullscreen-button" aria-label="全屏" @click="toggleFullscreen">⛶</button>
        </div>
        <div class="replay-track-wrap">
          <div class="replay-track" role="slider" tabindex="0" aria-label="视频播放进度" :aria-valuemin="0" :aria-valuemax="Math.floor(duration/1000)" :aria-valuenow="Math.floor(currentTime)" :aria-valuetext="`${formatClock(currentTime)} / ${formatClock(duration/1000)}`" @keydown="seekByKeyboard">
            <i class="replay-track-fill" :style="{width:`${Math.max(0,Math.min(100,currentTime/(duration/1000)*100))}%`}" />
            <span class="replay-track-thumb" :class="{'is-dragging':dragging}" :style="{left:`${Math.max(0,Math.min(100,currentTime/(duration/1000)*100))}%`}" />
          </div>
          <input class="replay-native-seek" type="range" min="0" :max="duration/1000" step="0.01" :value="currentTime" aria-label="拖动视频进度" @pointerdown="dragging=true" @pointerup="dragging=false" @pointercancel="dragging=false" @input="seekFromRange" />
          <button v-for="marker in markers" :key="marker.id" type="button" class="replay-marker" :style="{left:marker.left}" :title="`${marker.label} · 课堂事件 #${marker.id}`" :aria-label="`跳转到 ${marker.label}，课堂事件 ${marker.id}`" @pointerdown.stop @click.stop.prevent="jump(marker.at)" />
        </div>
      </div>
    </div>
    <p v-else-if="!loading&&!url">当前浏览器没有本节录像。换设备或清理浏览器数据后，录像不会自动恢复。</p>
    <p v-if="notice" role="status">{{notice}}</p><p v-if="error" role="alert">{{error}} <button @click="load">重试</button></p>
    <button v-if="record && !record.demo" @click="download">{{record.static?'下载项目录像':'下载本节录像'}} · {{(record.byteLength/1024/1024).toFixed(1)}} MiB</button>
    <details v-if="!record?.demo&&!record?.static"><summary>管理本机录像（{{items.length}}）</summary><p>仅当前站点、当前账户可见。删除仅影响浏览器内副本，不删除已下载文件。</p>
      <ul><li v-for="item in items" :key="item.key">课堂 #{{item.sessionId}} · {{(item.byteLength/1024/1024).toFixed(1)}} MiB <button @click="remove(item)">删除</button></li></ul>
    </details>
  </section>
</template>
<style scoped>
.replay-video-shell{position:relative;overflow:hidden;border-radius:8px;background:#08090c}.replay-video-shell video{display:block;width:100%;max-height:45vh;background:#08090c;object-fit:contain}.replay-player-controls{position:absolute;right:0;bottom:0;left:0;padding:30px 18px 12px;background:linear-gradient(transparent,#050608ed);color:#fff}.replay-controls-top{display:flex;align-items:center;gap:12px;min-height:32px;margin-bottom:7px}.replay-control-button{display:grid;place-items:center;min-width:30px;height:30px;padding:0;border:0;color:#fff;font-size:13px}.replay-play-button{font-size:18px}.replay-pause-glyph{display:flex;gap:4px;width:13px;height:16px}.replay-pause-glyph i{display:block;width:4px;height:100%;border-radius:1px;background:#fff}.replay-play-glyph{width:0;height:0;margin-left:3px;border-top:8px solid transparent;border-bottom:8px solid transparent;border-left:12px solid #fff}.replay-control-time{font-size:12px;font-variant-numeric:tabular-nums;white-space:nowrap}.replay-controls-spacer{flex:1}.replay-fullscreen-button{font-size:23px}.replay-speed-control{position:relative}.replay-speed-button{min-width:38px;font-variant-numeric:tabular-nums}.replay-speed-menu{position:absolute;right:0;bottom:calc(100% + 8px);z-index:5;display:grid;min-width:82px;gap:2px;padding:5px;border:1px solid #ffffff30;border-radius:9px;background:#11141bea;box-shadow:0 8px 24px #0009;backdrop-filter:blur(12px)}.replay-speed-menu button{width:100%;padding:6px 10px;border:0;border-radius:6px;color:#fff;text-align:center;font-size:12px}.replay-speed-menu button:hover,.replay-speed-menu button.is-selected{background:#ffffff20;color:#ffc18a}.replay-volume{width:78px;height:4px;accent-color:#fff}.replay-track-wrap{position:relative;height:24px;display:flex;align-items:center}.replay-track{position:relative;width:100%;height:4px;border-radius:6px;background:#ffffff75;outline:none;pointer-events:none}.replay-track:focus-visible{box-shadow:0 0 0 3px #d6a4ff}.replay-track-fill{position:absolute;inset:0 auto 0 0;height:100%;border-radius:inherit;background:#fff;pointer-events:none}.replay-track-thumb{position:absolute;top:50%;width:13px;height:13px;border:2px solid #fff;border-radius:50%;background:#fff;transform:translate(-50%,-50%);box-shadow:0 1px 6px #0008;pointer-events:none}.replay-track-thumb.is-dragging{transform:translate(-50%,-50%) scale(1.2)}.replay-native-seek{position:absolute;inset:0;z-index:1;width:100%;height:24px;margin:0;opacity:0;cursor:ew-resize;touch-action:none}.replay-native-seek::-webkit-slider-thumb{appearance:none;width:24px;height:24px}.replay-native-seek::-moz-range-thumb{width:24px;height:24px;border:0}.replay-marker{position:absolute;z-index:2;top:50%;width:9px;height:9px;padding:0;transform:translate(-50%,-50%);border:2px solid #111;background:#ffad6a;border-radius:50%;box-shadow:0 0 0 1px #ffad6a;cursor:pointer}.replay-marker:hover{transform:translate(-50%,-50%) scale(1.4);background:#fff}.replay-video-shell:fullscreen{width:100vw;height:100vh;display:grid;place-items:center;border-radius:0}.replay-video-shell:fullscreen video{width:100%;height:100%;max-height:none}.replay-video-shell:fullscreen .replay-player-controls{padding-bottom:20px}.classroom-replay{margin-bottom:1rem}button{color:inherit;background:transparent;border:1px solid var(--line);padding:.5rem .75rem;border-radius:8px;cursor:pointer}li{margin:.5rem 0}summary{cursor:pointer;margin:1rem 0}
.replay-title{margin:0;padding:14px 16px 9px;font-size:clamp(18px,2cqi,25px);line-height:1.25;}
.replay-video-shell video{width:100%;height:100%;max-height:none;object-fit:contain;}
.replay-player-controls{padding:clamp(11px,2.5cqi,30px) clamp(10px,1.8cqi,18px) clamp(8px,1.2cqi,12px);}
.replay-controls-top{gap:clamp(4px,1.2cqi,12px);min-height:clamp(28px,3.2cqi,32px);margin-bottom:clamp(4px,1cqi,7px);}
.replay-control-button{min-width:clamp(26px,3cqi,30px);height:clamp(28px,3.2cqi,32px);}
.replay-volume{width:clamp(42px,8cqi,78px);}
.replay-control-time{font-size:clamp(10px,1.2cqi,12px);}
.replay-track-wrap,.replay-native-seek{height:clamp(22px,2.4cqi,24px);}
@media(max-width:520px){.replay-player-controls{padding-right:9px;padding-left:9px;}.replay-controls-top{gap:3px;}.replay-volume{width:42px;}.replay-control-button{min-width:25px;}.replay-control-time{font-size:10px;}}
</style>
