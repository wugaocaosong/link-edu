<script setup>
import { ref,onBeforeUnmount,watch } from 'vue'

const props=defineProps({disabled:Boolean})
const emit=defineEmits(['dictation','attachment','notice'])
const Mic=window.SpeechRecognition||window.webkitSpeechRecognition
const listening=ref(false), media=ref(null), video=ref(null), picker=ref(null)
let speech, alive=true, cameraRun=0
function dictate(){
 if(listening.value){speech.stop();return}
 if(!Mic){emit('notice','当前浏览器不支持语音转写，可继续打字。');return}
 speech=new Mic()
 speech.lang='zh-CN'
 speech.onresult=event=>{
  if(alive)emit('dictation',Array.from(event.results).filter(result=>result.isFinal).map(result=>result[0].transcript).join(''))
 }
 speech.onend=()=>{listening.value=false}
 speech.onerror=event=>{if(alive&&event.error!=='aborted')emit('notice','语音转写未完成，请检查麦克风权限或重试。')}
 try{speech.start();listening.value=true}catch{emit('notice','无法启动麦克风，请重试。')}
}
function stopCamera(){
 cameraRun++
 media.value?.getTracks().forEach(track=>track.stop())
 media.value=null
}
async function startCamera(){
 if(media.value){stopCamera();return}
 const run=++cameraRun
 try{
  const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}},audio:false})
  if(!alive||run!==cameraRun){stream.getTracks().forEach(track=>track.stop());return}
  media.value=stream
 }catch{if(alive&&run===cameraRun)emit('notice','摄像头不可用，可以上传已有照片。')}
}
function attachVideo(element){
 video.value=element
 if(element)element.srcObject=media.value
}
function capture(){
 const frame=video.value
 if(!frame?.videoWidth){emit('notice','相机画面尚未就绪，请稍等。');return}
 const run=cameraRun
 const canvas=document.createElement('canvas')
 canvas.width=frame.videoWidth
 canvas.height=frame.videoHeight
 canvas.getContext('2d').drawImage(frame,0,0)
 canvas.toBlob(blob=>{
  if(!alive||run!==cameraRun||!blob)return
  emit('attachment',new File([blob],'板书照片.jpg',{type:'image/jpeg'}))
  stopCamera()
 },'image/jpeg',.85)
}
function pick(event){
 const file=event.target.files?.[0]
 event.target.value=''
 if(file)emit('attachment',file)
}
watch(()=>props.disabled,disabled=>{if(disabled){speech?.abort();stopCamera()}})
onBeforeUnmount(()=>{alive=false;speech?.abort();stopCamera()})
</script>

<template>
 <div class="assistant-composer-tools">
  <button type="button" :disabled="disabled" :aria-pressed="listening" title="浏览器语音转写可能使用在线语音服务" @click="dictate">{{ listening?'停止语音':'🎙 语音输入' }}</button>
  <button type="button" :disabled="disabled" :aria-expanded="!!media" @click="startCamera">{{ media?'关闭相机':'📷 拍板书' }}</button>
  <button type="button" :disabled="disabled" @click="picker?.click()">＋ 本地文件</button>
  <input hidden ref="picker" type="file" accept=".png,.jpg,.jpeg,.webp,.txt,.md,.pdf,.docx" @change="pick">
  <div v-if="media" class="assistant-camera-preview">
   <video :ref="attachVideo" autoplay muted playsinline aria-label="板书拍摄预览" />
   <button type="button" :disabled="disabled" @click="capture">拍摄并添加</button>
  </div>
 </div>
</template>
