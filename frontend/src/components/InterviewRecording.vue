<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { analyzeLessonAudio } from '../services/interviewAudio.js'

const emit=defineEmits(['transcript'])
const recognitionAvailable=Boolean(window.SpeechRecognition||window.webkitSpeechRecognition)
const auto=ref(false), transcript=ref(''), busy=ref(false), recording=ref(false), audioUrl=ref(''), message=ref('')
const buffer=ref(null)
const metrics=computed(()=>buffer.value&&analyzeLessonAudio(buffer.value,transcript.value))
let recorder, stream, recognition, timer, generation=0
function release(){
 clearTimeout(timer)
 try { recognition?.stop() } catch { /* Recognition may have already ended. */ }
 recognition=null
 stream?.getTracks().forEach(track=>track.stop())
 stream=null
}
function stop(){
 if(recorder?.state==='recording'){busy.value=true;recorder.stop()}
 recording.value=false
 release()
}
async function start(){
 if(busy.value||recording.value)return
 const run=++generation
 busy.value=true
 message.value=''
 try {
  if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder)throw Error('当前浏览器无法录音，可输入试讲稿继续练习。')
  const tracks=await navigator.mediaDevices.getUserMedia({audio:true})
  if(run!==generation){tracks.getTracks().forEach(t=>t.stop());return}
  stream=tracks
  const chunks=[]
  recorder=new MediaRecorder(stream)
  const mime=recorder.mimeType
  recorder.ondataavailable=event=>{if(event.data.size)chunks.push(event.data)}
  recorder.onstop=async()=>{
   if(run!==generation)return
   busy.value=true
   try {
    const blob=new Blob(chunks,{type:mime})
    if(audioUrl.value)URL.revokeObjectURL(audioUrl.value)
    audioUrl.value=URL.createObjectURL(blob)
    const AudioContext=window.AudioContext||window.webkitAudioContext
    const context=new AudioContext()
    try {
     const decoded=await context.decodeAudioData(await blob.arrayBuffer())
     if(run===generation){
      buffer.value=decoded
      if(!metrics.value)message.value='录音中未检测到足够清晰的声音，可以重新录制。'
     }
    } finally {await context.close()}
   } catch {if(run===generation)message.value='暂时无法分析这段录音，仍可回听或提交讲稿。'}
   finally {if(run===generation)busy.value=false}
  }
  recorder.onerror=()=>{if(run===generation){stop();message.value='录音中断，请重试。'}}
  recorder.start()
  buffer.value=null
  transcript.value=''
  recording.value=true
  timer=setTimeout(stop,120000)
  if(auto.value&&recognitionAvailable){
   const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition
   recognition=new Recognition()
   recognition.lang='zh-CN'
   recognition.continuous=true
   recognition.onresult=event=>{
    if(run===generation)transcript.value=Array.from(event.results).filter(item=>item.isFinal).map(item=>item[0].transcript).join(' ')
   }
   recognition.onerror=()=>{if(run===generation)message.value='自动转写暂不可用，可以手动补充转写。'}
   try {recognition.start()} catch {message.value='自动转写暂不可用，可以手动补充转写。'}
  }
 } catch(error) {
  release()
  message.value=error.name==='NotAllowedError'?'麦克风未授权，可以输入试讲稿继续练习。':error.message
 } finally {if(run===generation)busy.value=false}
}
onBeforeUnmount(()=>{
 generation++
 stop()
 if(audioUrl.value)URL.revokeObjectURL(audioUrl.value)
})
const player=ref(null)
function seek(seconds){
 if(player.value&&Number.isFinite(player.value.duration))player.value.currentTime=Math.min(seconds,player.value.duration)
}
const center=90
function point(index,value,count){
 const angle=2*Math.PI*index/count-Math.PI/2
 return [center+Math.cos(angle)*57*value/100,center+Math.sin(angle)*57*value/100]
}
const polygon=values=>values.map((value,index)=>point(index,value,values.length).join(',')).join(' ')
</script>

<template>
 <details class="interview-recording">
  <summary>试讲录音与反馈</summary>
  <label v-if="recognitionAvailable"><input v-model="auto" type="checkbox" :disabled="recording || busy"> 使用浏览器自动转写（音频可能发送给其语音服务）</label>
  <button type="button" :disabled="busy" @click="recording?stop():start()">{{ recording?'结束录音':busy?'处理中…':'开始录音（最多 2 分钟）' }}</button>
  <p v-if="message" role="status">{{ message }}</p>
  <audio ref="player" v-if="audioUrl" :src="audioUrl" aria-label="回听试讲录音" controls />
  <template v-if="audioUrl&&!recording">
   <textarea v-model="transcript" aria-label="录音转写稿" maxlength="6000" placeholder="可补写、校正原话，保留「嗯、啊」以便估算语气词" rows="2" />
   <button v-if="transcript.trim()" type="button" @click="emit('transcript',transcript.trim())">填入作答框</button>
  </template>
  <div v-if="metrics" class="interview-radar">
   <svg viewBox="0 0 180 180" role="img" aria-label="练习指标雷达图，具体分数见右侧列表">
    <polygon v-for="value in [25,50,75,100]" :key="value" :points="polygon(metrics.scores.map(()=>value))" fill="none" stroke="#9279a0"/>
    <line v-for="([label],index) in metrics.scores" :key="label" x1="90" y1="90" :x2="point(index,100,metrics.scores.length)[0]" :y2="point(index,100,metrics.scores.length)[1]" stroke="#9279a0"/>
    <polygon :points="polygon(metrics.scores.map(([,value])=>value))" fill="#ba86ef66" stroke="#dfb6ff" stroke-width="2"/>
    <text v-for="([label],index) in metrics.scores" :key="label" :x="point(index,130,metrics.scores.length)[0]" :y="point(index,130,metrics.scores.length)[1]+3" fill="currentColor" font-size="9" text-anchor="middle">{{ label }}</text>
   </svg>
   <div>
    <ul><li v-for="[label,value] in metrics.scores" :key="label">{{ label }} {{ value }}/100</li></ul>
    <p>{{ metrics.seconds }} 秒 · 停顿约 {{ metrics.pauses }} 次（{{ metrics.longPauses }} 次超过 1.2 秒）</p>
    <button v-for="pause in metrics.pauseMarkers" :key="pause.at" type="button" @click="seek(Math.max(0,pause.at-1))">回听 {{ pause.at.toFixed(1) }} 秒的停顿</button>
    <p v-if="metrics.pace!==null">约 {{ metrics.pace }} 字词/分钟 · 检出语气词 {{ metrics.fillers }} 组</p>
    <p v-else>补充转写稿可估算语速与语气词。</p>
    <p>练习分为规则估算。音量起伏可用于回听表达变化，感染力需结合内容与听众反应判断。</p>
   </div>
  </div>
 </details>
</template>
