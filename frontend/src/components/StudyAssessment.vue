<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { api } from '../services/api'
import { recordingMime } from '../services/classroomRecorder'
import { getClassroomRecording, saveClassroomRecording } from '../services/classroomRecordingStore'
import { archive, blindFiles, downloadBlob } from '../services/studyArchive'

const props = defineProps({ attempt: Object, userId: Number })
const emit = defineEmits(['finished'])
const camera = ref(null), review = ref(''), record = shallowRef(null)
const state = ref('idle'), busy = ref(false), error = ref(''), marks = ref([null,null]), ms = ref(0)
const checked = ref(false), note = ref(''), actor = ref('')
const remaining = computed(() => Math.max(0, Math.ceil((300000-ms.value)/1000)))
const scope = location.origin + '/study/assessment'
let stream, recorder, timer, startTime, disposed = false

function show(row) {
  if (!row) return
  record.value = row
  marks.value = row.marks || props.attempt.assessment?.marks || []
  ms.value = row.durationMs
  review.value = URL.createObjectURL(row.blob)
  state.value = 'review'
}
onMounted(async () => {
  try {
    const row = await getClassroomRecording(scope, props.userId, props.attempt.id)
    if (!disposed) show(row)
  } catch (e) { error.value=e.message }
})
function release() {
  clearInterval(timer)
  stream?.getTracks().forEach(track => track.stop())
  stream=null
}
async function preview() {
  busy.value=true; error.value=''
  try {
    if (!recordingMime()) throw new Error('当前浏览器无法录制音视频')
    stream=await navigator.mediaDevices.getUserMedia({video:true, audio:true})
    if (disposed) { release(); return }
    camera.value.srcObject=stream
    await camera.value.play()
    if(disposed){release();return}
    state.value='ready'
  } catch (e) { release(); error.value=e.message }
  finally { busy.value=false }
}
function stop() {
  if (recorder?.state !== 'recording') return
  ms.value=Math.round(performance.now()-startTime)
  state.value='saving'; clearInterval(timer); recorder.stop()
}
function start() {
  error.value=''
  try {
    const chunks=[]
    marks.value=[null,null]
    recorder=new MediaRecorder(stream,{mimeType:recordingMime(),videoBitsPerSecond:1800000})
    recorder.ondataavailable=e=>{if(e.data.size) chunks.push(e.data)}
    recorder.onstop=async()=>{
      release()
      if (disposed) return
      const blob=new Blob(chunks,{type:recorder.mimeType})
      if (!blob.size) {error.value='未取得录像，请登记异常并联系协调员。';state.value='idle';return}
      const row={blob, marks:[...marks.value], durationMs:ms.value}
      show(row)
      try { await saveClassroomRecording(scope,props.userId,props.attempt.id,blob,row) }
      catch(e){error.value=e.message+'；请在离开前导出盲评包。'}
    }
    recorder.onerror=()=>{error.value='录制异常，请在核验时登记。';stop()}
    for(const track of stream.getTracks()) track.onended=()=>{error.value='设备断开，请登记异常。';stop()}
    recorder.start(500); startTime=performance.now(); state.value='recording'
    timer=setInterval(()=>{
      ms.value=Math.round(performance.now()-startTime)
      if(ms.value>=300000) stop()
    },100)
  } catch(e){error.value=e.message;release();state.value='idle'}
}
function mark(i) { if(marks.value[i]==null) marks.value[i]=Math.round(performance.now()-startTime) }
async function exportClip(){
  if(!record.value)return
  downloadBlob(await archive(blindFiles(props.attempt.clip,record.value,marks.value)),props.attempt.clip+'.zip')
}
async function finish() {
  busy.value=true;error.value=''
  try {
    await exportClip()
    await api.post('/study/attempts/'+props.attempt.id+'/assessment',{
      marks:marks.value,duration_ms:ms.value,av_checked:checked.value,note:note.value,actor:actor.value})
    emit('finished')
  } catch(e){error.value=e.response?.data?.message || e.message}
  finally{busy.value=false}
}
function guard(e){if(['recording','saving'].includes(state.value)){e.preventDefault();e.returnValue=''}}
window.addEventListener('beforeunload',guard)
onBeforeRouteLeave(()=>!['recording','saving'].includes(state.value))
onBeforeUnmount(()=>{disposed=true;stop();release();URL.revokeObjectURL(review.value);window.removeEventListener('beforeunload',guard)})
</script>
<template>
  <section>
    <h2>真人独立测评</h2>
    <p>请主持人持卡、宣读开场语。检查双方声音，确保纸张、手部和指图位置入镜。</p>
    <video v-show="!review" ref="camera" autoplay muted playsinline aria-label="机位预览"></video>
    <video v-if="review" :src="review" controls playsinline aria-label="核验测评录像"></video>
    <div class="actions">
      <button v-if="state==='idle' && !attempt.finished" :disabled="busy" @click="preview">检查设备</button>
      <button v-if="state==='ready'" @click="start">开始 5 分钟测评</button>
      <template v-if="state==='recording'">
        <strong>{{ Math.floor(remaining/60) }}:{{ String(remaining%60).padStart(2,'0') }}</strong>
        <button v-for="(_,i) in 2" :key="i" :disabled="marks[i]!=null || (i===0 && marks[1]!=null)" @click="mark(i)">{{ marks[i]!=null?'已标记机会 ':'标记机会 ' }}{{ i+1 }}</button>
        <button @click="stop">提前结束</button>
      </template>
    </div>
    <template v-if="review && !attempt.finished">
      <label>扮演者编号<input v-model="actor" maxlength="40"></label>
      <label>现场异常与受影响的机会<textarea v-model="note" maxlength="1000"></textarea></label>
      <label><input type="checkbox" v-model="checked">已回放核对师生音轨、纸张和手部画面</label>
      <button :disabled="busy || !checked || !actor.trim()" @click="finish">导出盲评包并提交</button>
    </template>
    <button v-if="attempt.finished && review" @click="exportClip">再次导出盲评包</button>
    <p v-if="attempt.finished && !review">请从原录制浏览器或已导出的盲评包取回录像。</p>
    <p role="alert">{{ error }}</p>
  </section>
</template>
