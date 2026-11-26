<script setup>
import { computed, onMounted, onBeforeUnmount, ref, shallowRef } from 'vue'
import { api } from '../services/api'
import { getClassroomRecording, recordingTime } from '../services/classroomRecordingStore'
import { archive, downloadBlob } from '../services/studyArchive'

const props=defineProps({ attempt:Object, userId:Number, code:String })
const emit=defineEmits(['changed'])
const note=ref(''), durationNote=ref(''), seconds=ref(null), goal=ref(''), reviewed=ref(false), busy=ref(false), error=ref('')
const record=shallowRef(null), url=ref(''), player=ref(null), evidence=ref(null)
const parts=computed(()=>record.value?.parts || (record.value?[record.value]:[]))
const partIndex=ref(0)
function openPart(i, time=0){
  partIndex.value=i
  URL.revokeObjectURL(url.value)
  url.value=URL.createObjectURL(parts.value[i].blob)
  if(player.value)player.value.onloadedmetadata=()=>{player.value.currentTime=time}
}
const path=computed(()=>'/study/attempts/'+props.attempt.id)
let disposed=false
async function load() {
  try {
    const row=await getClassroomRecording(location.origin,props.userId,props.attempt.session_id)
    if(disposed)return
    record.value=row
    if(row)openPart(0)
    if(props.attempt.reflection)evidence.value=(await api.get(path.value+'/evidence')).data
  } catch(e){error.value=e.response?.data?.message || e.message}
}
onMounted(load)
onBeforeUnmount(()=>{disposed=true;URL.revokeObjectURL(url.value)})
async function submit(action, data){
  busy.value=true; error.value=''
  try {await api.post(path.value+'/'+action,data);emit('changed')}
  catch(e){error.value=e.response?.data?.message || e.message}
  finally{busy.value=false}
}
function seek(ms){
  const i=parts.value.findIndex(p=>recordingTime(p.segments,ms)!=null)
  const time=recordingTime(parts.value[i]?.segments,ms)
  if(time==null){error.value='该时间点没有对应录像，可能位于暂停或缺录区间。';return}
  if(i!==partIndex.value)openPart(i,time)
  else player.value.currentTime=time
  player.value.focus()
}
async function download(){
  const prefix=props.code+'-'+props.attempt.stage+'-'+props.attempt.number
  const videos=parts.value.map((p,i)=>[prefix+'-'+(i+1)+(p.blob.type.includes('mp4')?'.mp4':'.webm'),p.blob])
  const meta={...props.attempt,participant:props.code,parts:parts.value.map((p,i)=>({
    filename:videos[i][0],segments:p.segments,duration_ms:p.durationMs})),...evidence.value}
  const zip=await archive([...videos,['session.json',JSON.stringify(meta,null,2)]])
  downloadBlob(zip,prefix+'.zip')
}
</script>
<template>
  <section v-if="!attempt.reflection">
    <h2>独立自评</h2>
    <form @submit.prevent="submit('reflection',{text:note,at_ms:Math.round(seconds*1000),duration_note:durationNote})">
      <label>你想回看哪次师生回应？<textarea v-model="note" required maxlength="2000"></textarea></label>
      <label>距开课的时间（秒，含暂停）<input v-model.number="seconds" required type="number" min="0" step="0.1"></label>
      <label v-if="attempt.active_seconds<598">本场提前结束，请登记原因<input v-model="durationNote" required maxlength="1000"></label>
      <button :disabled="busy">保存独立自评</button>
    </form>
  </section>
  <section v-else>
    <h2>本轮反馈</h2>
    <p>我的自评 · {{ attempt.reflection.text }}</p>
    <template v-if="attempt.report">
      <article class="study-report">{{ attempt.report.text }}</article>
      <video v-if="url" :src="url" controls ref="player" playsinline aria-label="回看训练录像"></video>
      <p v-else>当前浏览器没有本场录像，请在原设备或已导出的训练包中回看。</p>
      <div v-if="url" class="actions"><button @click="seek(attempt.reflection.at_ms)">定位自评片段</button></div>
      <div v-if="parts.length>1" class="actions"><button v-for="(_,i) in parts" :key="i" @click="openPart(i)">录像片段 {{ i+1 }}</button></div>
      <details v-if="evidence"><summary>按师生对话定位</summary>
        <p v-for="(t,i) in evidence.transcript" :key="t.turn"><button :disabled="!url" @click="seek(evidence.turns[i].at_ms)">{{ t.turn }} · {{ t.speaker }}</button> {{ t.text }}</p>
      </details>
      <template v-if="!attempt.finished">
        <label><input type="checkbox" v-model="reviewed">已阅读报告、回看本人试讲录像</label>
        <label v-if="attempt.stage==='round1'">下一次准备改进的一件事<textarea v-model="goal" maxlength="2000"></textarea></label>
        <button :disabled="busy || !reviewed || (attempt.stage==='round1' && !goal.trim())" @click="submit('complete',{goal,reviewed_video:reviewed})">完成本轮反馈</button>
      </template>
      <p v-if="attempt.goal">我的修订目标 · {{ attempt.goal }}</p>
    </template>
    <p v-else>独立自评已保存，等待本组报告发放。<button @click="emit('changed')">刷新报告</button></p>
    <button v-if="record" @click="download">导出本轮录像与记录</button>
  </section>
  <p role="alert">{{ error }}</p>
</template>
