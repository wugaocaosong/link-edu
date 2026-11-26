<script setup>
import { computed, inject, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { answerPlatformQuestion, platformPageLabel } from '../services/platformHelp.js'
import { api } from '../services/api.js'
import { addJournal } from '../services/dashboard'
import { AssistantClient } from '../services/assistantClient.js'
import { journalSubmitErrorMessage } from '../utils/dashboardState'
import { classroomHelpKey } from '../utils/classroomHelpContext.js'
import { useHelpPosition } from '../utils/useHelpPosition.js'
import { startTour } from '../utils/onboarding.js'
import { useAuthStore } from '../stores/auth.js'
import { loadSettings, saveSettings } from '../utils/settings.js'
import faqs from '../data/systemGuide.json'
import AssistantCharacter from './AssistantCharacter.vue'
import '../help-chat.css'
import AssistantComposerTools from './AssistantComposerTools.vue'
import InterviewRecording from './InterviewRecording.vue'
import { interviewGreeting, latestReviewTopic, loadInterviewHistory, saveInterviewHistory } from '../services/interviewHistory.js'
import { defenseInterruptions, interviewModules, lessonPlanFramework, respondToInterview, startInterview, structuredTopics } from '../services/interviewPractice.js'
import { formatInterviewRubric, InterviewOnline } from '../services/interviewOnline.js'
import { isToolRequest, toolResourceRoute } from '../services/assistantTools.js'
import { motionEnabled, replyPose } from '../services/assistantPersona.js'
import { useReducedMotion } from '../utils/useReducedMotion.js'
import { usageLabel } from '../services/assistantUsage.js'
const route=useRoute(),router=useRouter()
const pageLabel=computed(()=>platformPageLabel(route.path))
const context=inject(classroomHelpKey,ref(null)),auth=useAuthStore()
const fab=ref(null),panel=ref(null),logRef=ref(null),fullscreenTarget=ref(null)
const open=ref(false),mode=ref('bot'),query=ref(''),draft=ref(''),sending=ref(false),voice=ref(false),status=ref('idle'),level=ref(0),notice=ref(''),partial=ref('')
const toolsOpen=ref(false), connectionError=ref('')
const attachment=ref(null), pendingAttachment=ref(null)
const attachmentUrls=new Set()
const cardFaces={
 structured:{icon:'⚖',back:'抽题 · 作答 · 考官追问'},
 lesson:{icon:'▤',back:'走上讲台 · 开始试讲'},
 defense:{icon:'◈',back:'教学依据 · 临场回应'},
 plan:{icon:'✎',back:'填写关键词 · 生成框架'},
}
function removeAttachment(){
 if(attachment.value){
  URL.revokeObjectURL(attachment.value.url)
  attachmentUrls.delete(attachment.value.url)
  attachment.value=null
 }
}
function addAttachment(file){
 const image=/\.(?:png|jpe?g|webp)$/i.test(file.name)
 if(!image&&!/\.(?:txt|md|pdf|docx)$/i.test(file.name)){notice.value='不支持这个格式。请选择 PNG、JPEG、WebP、PDF、DOCX、TXT 或 Markdown。';return}
 const limit=image?10:20
 if(!file.size||file.size>limit*1024*1024){notice.value=`附件应大于 0 且不超过 ${limit} MB。`;return}
 removeAttachment()
 const url=URL.createObjectURL(file)
 attachmentUrls.add(url)
 attachment.value={file,url,image}
 notice.value=''
}
function addDictation(text){
 const limit=practice.value?6000:2000
 if(!text)return
 draft.value=[draft.value,text].filter(Boolean).join(' ').slice(0,limit)
 markActivity()
}
function clearAttachmentUrls(){
 for(const url of attachmentUrls)URL.revokeObjectURL(url)
 attachmentUrls.clear()
 attachment.value=null
 pendingAttachment.value=null
}
const practice=ref(null)
const onlineDraft=ref('')
const plansOpen=ref(false),plans=ref([]),planReports=ref([]),selectedReport=ref(null),checking=ref(false)
const topicOptions=[...new Set([...structuredTopics,'人际关系','课堂管理','教育教学','自我认知','综合分析'])]
const practiceModule=computed(()=>interviewModules.find(item=>item.id===practice.value?.id))
const history=ref([])
const historyOpen=ref(false), onlyMistakes=ref(false), pressure=ref(false), topic=ref('')
let interruptionTimer
const historyEntries=computed(()=>onlyMistakes.value?history.value.filter(item=>item.assessment.missing.length):history.value)
const structuredProgress=computed(()=>structuredTopics.flatMap(label=>{
 const attempts=history.value.filter(item=>item.id==='structured'&&item.topic===label)
 if(!attempts.length)return []
 const score=entry=>entry.assessment.covered+'/'+entry.assessment.total
 return [{label, latest:score(attempts[0]), previous:attempts[1]?score(attempts[1]):''}]
}))
const reviewTopic=computed(()=>latestReviewTopic(history.value)?.topic)
async function selectPractice(id, offline=false){
 if(voice.value)stopVoice()
 clearReaction()
 clearTimeout(interruptionTimer)
 interruptionTimer=null
 mode.value='bot'
 toolsOpen.value=false
 historyOpen.value=false
 if(!id){practice.value=null;return}
 draft.value=''
 const local=startInterview(id,practice.value?.question,{pressure:pressure.value,topic:topic.value})
 practice.value=null
 const controller=practiceReview=new AbortController()
 sending.value=true;practiceBusy.value=true
 try{
  if(offline||(id==='structured'&&pressure.value))throw Error('离线练习')
  const question=await onlineRequest({action:'question',mode:id,topic:topic.value},controller)
  if(controller.signal.aborted)return
  practice.value={id,question:question.question,questionId:question.id,topic:question.topic,online:true,stage:'initial'}
  messages.value.push({role:'bot',text:`${question.question}\n\n目标口述时长 ${question.target_seconds} 秒`,usage:question.usage})
 }catch(error){
  if(controller.signal.aborted)return
  practice.value=local
  messages.value.push({role:'bot',text:`离线练习｜${local.message}`,usage:error.usage})
 }finally{
  practiceReview=null;sending.value=false;practiceBusy.value=false;onlineDraft.value=''
 }
 if(id==='lesson')react('invite')
}
function startWeakTopic(){
 topic.value=reviewTopic.value
 selectPractice('structured')
}
function queueDefenseInterruption(){
 const current=practice.value
 if(current?.online||current?.id!=='defense'||current.stage!=='answer'||current.interrupted||!draft.value.trim()||interruptionTimer)return
 interruptionTimer=setTimeout(()=>{
  interruptionTimer=null
  if(!open.value||practice.value!==current||sending.value||!draft.value.trim())return
  const question=defenseInterruptions[Math.floor(Math.random()*defenseInterruptions.length)]
  practice.value={...current,interrupted:true,activeQuestion:question}
  messages.value.push({role:'bot',text:`临场打断｜${question}\n原稿还在输入框，可以接着写你的临场回应。`})
 },6000+Math.random()*8000)
}
let planRequest
async function onlineRequest(payload, controller){
 if(controller.signal.aborted)throw Error('已取消')
 if(voice.value)stopVoice()
 if(!client.session&& !await client.start('text',style.value))throw Error('在线服务不可用')
 return interviewOnline.request(payload,controller.signal,text=>{onlineDraft.value=text})
}
async function loadPlans(){
 const uid=auth.user?.id
 try{
  const {data}=await api.get('/assistant/interview-plans',{skipBusy:true,timeout:8000})
  if(uid!==auth.user?.id)return
  plans.value=data.plans;planReports.value=data.reports
 }catch{if(uid===auth.user?.id)notice.value='暂时无法加载备考计划。'}
}
async function buildStudyPlan(kind){
 const controller=planRequest=new AbortController()
 sending.value=true;practiceBusy.value=true;notice.value=''
 try{
  const plan=await onlineRequest({action:'plan',kind,report_id:selectedReport.value},controller)
  if(!controller.signal.aborted){
   plans.value=[plan,...plans.value.filter(item=>item.id!==plan.id)]
   messages.value.push({role:'bot',text:'备考计划已保存。',usage:plan.usage})
  }
 }catch(error){if(!controller.signal.aborted){notice.value='暂时无法生成计划，请重试；已保存的计划不会丢失。'
  if(error.usage)messages.value.push({role:'bot',text:'计划生成未完成。',usage:error.usage})
 }}
 finally{planRequest=null;sending.value=false;practiceBusy.value=false;onlineDraft.value=''}
}
async function checkStudyPlan(plan, day){
 const uid=auth.user?.id
 checking.value=true
 try{
  const {data}=await api.patch(`/assistant/interview-plans/${plan.id}/steps/${day}`,{done:!plan.completed.includes(day)},{skipBusy:true,timeout:8000})
  if(uid===auth.user?.id)plans.value=plans.value.map(item=>item.id===plan.id?data:item)
 }catch{if(uid===auth.user?.id)notice.value='打卡未保存，请重试。'}
 finally{checking.value=false}
}
async function generatePlan(online=false){
 const input=draft.value.trim()
 if(!/[^；;，,、\s]/u.test(input)){notice.value='请先输入一个课题。';return}
 if(online&&input.length>1200){notice.value='在线润色请将教案构想缩短到 1200 字以内。';return}
 notice.value=''
 const turn=crypto.randomUUID()
 messages.value.push({role:'user',turn,text:input})
 if(!online){
  messages.value.push({role:'bot',turn,complete:true,text:lessonPlanFramework(input),free:true})
  return
 }
 const request=planRequest=new AbortController()
 sending.value=true
 practiceBusy.value=true
 try{
  const data=await onlineRequest({action:'framework',brief:input},request)
  if(!request.signal.aborted&&typeof data?.text==='string')messages.value.push({role:'bot',turn,complete:true,text:data.text,usage:data.usage})
 }catch(error){
  if(!request.signal.aborted){
   notice.value=error.response?.data?.message||'在线润色暂不可用。'
   messages.value.push({role:'bot',turn,complete:true,text:lessonPlanFramework(input),usage:error.usage})
  }
 }finally{
  if(planRequest===request){planRequest=null;practiceBusy.value=false;sending.value=false;onlineDraft.value=''}
 }
}
function rememberPractice(result,text){
 if(!result.assessment)return
 const title=result.topic||text.split(/[\n，,；;]/u)[0].slice(0,32)||practiceModule.value.label
 const entry={id:result.id,at:Date.now(),title,topic:result.topic,question:practice.value?.activeQuestion||result.question,
  answer:[practice.value?.firstAnswer,text].filter(Boolean).join('\n').slice(0,6000),
  feedback:result.message,assessment:result.assessment,rubric:result.rubric}
 if(saveInterviewHistory(auth.user?.id,entry))history.value=loadInterviewHistory(auth.user.id)
 else if(auth.user?.id)notice.value='练习已完成，本机未能保存这条记录。'
 const [latest,previous]=history.value
 if(latest?.at===entry.at&&previous&&entry.id==='structured'&&previous.id===entry.id&&
    entry.topic&&previous.topic===entry.topic&&entry.assessment.missing.length&&previous.assessment.missing.length)
  void api.post('/assistant/profile/practice',{topic:entry.topic,consecutive_incomplete:2},{skipBusy:true}).catch(()=>{})
}
const style=ref(loadSettings().assistantStyle)
const depth=ref(loadSettings().assistantDepth),animation=ref(loadSettings().assistantAnimation)
const reducedMotion=useReducedMotion()
const animateCharacter=computed(()=>motionEnabled(animation.value,reducedMotion.value))
function changeStyle(value){style.value=value;client.setStyle(value);try{saveSettings({assistantStyle:value})}catch{notice.value='偏好无法保存，本次会话仍使用已选风格'}}
function changeDepth(value){depth.value=value;client.setDepth(value);try{saveSettings({assistantDepth:value})}catch{notice.value='篇幅偏好无法保存，本次会话仍使用已选设置'}}
function changeAnimation(value){animation.value=value;if(!value)clearReaction();try{saveSettings({assistantAnimation:value})}catch{notice.value='动画偏好无法保存，本次会话仍使用已选设置'}}
const messages=ref([])
const savedMistakes=ref([])
let latestToolQuestion=''
async function loadSavedMistakes(){
 const uid=auth.user?.id
 if(!uid)return
 try{
  const {data}=await api.get('/assistant/mistakes',{skipBusy:true,timeout:8000})
  if(uid===auth.user?.id)savedMistakes.value=data.items
 }catch{}
}
function confirmTool(item, accepted){
 if(item.tool?.status!=='pending'||!item.complete||!client.session||client.turn!==item.turn)return
 client.send('tool_confirmation',{token:item.tool.token,accepted})
 item.tool={...item.tool,status:'processing',token:null}
}
function expirePendingTools(){
 for(const item of messages.value){
  if(['pending','processing'].includes(item.tool?.status)){
   item.tool={...item.tool,status:'expired',token:null,message:'本次确认已结束；可查看错题本或计划核对保存结果。'}
  }
 }
}
const suggestedTopic=ref('')
const {fabStyle,panelStyle,onResizeDown,onResizeMove,onResizeEnd,onResizeKey,dragging,onFabDown,onPanelDown,suppressClick,clampAll,anchorPanel}=useHelpPosition(fab,panel)
const reaction=ref(''), resting=ref(false), nearby=ref(false), focused=ref(false), look=ref(0), lookY=ref(0)
const practiceBusy=ref(false)
let reactionTimer, restTimer, stallTimer, practiceReview, lastPointerActivity=0
const role=computed(()=>({lesson:'student',structured:'examiner',defense:'examiner'})[practice.value?.id] || '')
function clearReaction(){
 clearTimeout(reactionTimer)
 reaction.value=''
}
function react(value){
 clearReaction()
 if(!value||!animateCharacter.value)return
 reaction.value=value
 reactionTimer=setTimeout(clearReaction,2400)
}
function resetRest(){
 clearTimeout(restTimer)
 resting.value=false
 restTimer=setTimeout(()=>resting.value=true,25000)
}
function scheduleEncouragement(){
 clearTimeout(stallTimer)
 if(open.value&&practice.value&&!sending.value&&!voice.value){
  stallTimer=setTimeout(()=>react('encourage'),15000)
 }
}
function trackPointer(event){
 if(!open.value&&event.timeStamp-lastPointerActivity>1000){
  lastPointerActivity=event.timeStamp
  resetRest()
 }
 if(context.value?.active||dragging.value||event.pointerType==='touch'||!fab.value)return
 const rect=fab.value.getBoundingClientRect()
 if(!rect.width||getComputedStyle(fab.value).visibility==='hidden')return
 const x=event.clientX-rect.left-rect.width/2
 const y=event.clientY-rect.top-rect.height*.36
 const close=Math.hypot(x,y)<(nearby.value?108:86)
 if(close&&!nearby.value)resetRest()
 nearby.value=close
 if(close){
  look.value=Math.max(-1,Math.min(1,x/46))
  lookY.value=Math.max(-1,Math.min(1,y/46))
 }else if(look.value||lookY.value)leavePointer()
}
function leavePointer(){nearby.value=false;look.value=0;lookY.value=0}
function markActivity(){
 queueDefenseInterruption()
 if(reaction.value==='encourage')clearReaction()
 scheduleEncouragement()
 resetRest()
}
watch([open,status,dragging],()=>{
 leavePointer()
 resetRest()
})
watch([open,practice,sending],scheduleEncouragement)
watch(dragging,value=>{
 if(value==='fab'&&!context.value?.active)react('startled')
})
onMounted(()=>{
 resetRest()
 window.addEventListener('pointermove',trackPointer,{passive:true})
 window.addEventListener('pointerdown',resetRest,{passive:true})
 window.addEventListener('keydown',resetRest)
 window.addEventListener('scroll',resetRest,{passive:true,capture:true})
 document.documentElement.addEventListener('pointerleave',leavePointer)
})
onUnmounted(()=>{
 clearAttachmentUrls()
 clearTimeout(interruptionTimer)
 clearReaction()
 clearTimeout(restTimer)
 clearTimeout(stallTimer)
 practiceReview?.abort()
 planRequest?.abort()
 window.removeEventListener('pointermove',trackPointer)
 window.removeEventListener('pointerdown',resetRest)
 window.removeEventListener('keydown',resetRest)
 window.removeEventListener('scroll',resetRest,true)
 document.documentElement.removeEventListener('pointerleave',leavePointer)
})
const pose=computed(()=>{
 if(context.value?.active||!animateCharacter.value) return ''
 if(dragging.value==='fab') return 'startled'
 if(dragging.value==='panel') return 'brace'
 if(practiceBusy.value||status.value==='thinking'||status.value==='connecting'||sending.value) return 'thinking'
 if(reaction.value) return reaction.value
 if(status.value==='speaking') return 'speaking'
 if(status.value==='listening'||(open.value&&draft.value.trim()&&!resting.value)) return 'notes'
 if(nearby.value||(!open.value&&focused.value))return 'curious'
 return resting.value?'sleep':''
})
const readerTarget=ref(null)
const target=computed(()=>context.value?.target||fullscreenTarget.value||readerTarget.value||'body')
const inLesson=computed(()=>Boolean(context.value))
const guidance=computed(()=>context.value?.active?'授课中，文字帮助随时可用':context.value?.state==='ended'?'课堂已结束，可保存录像并查看评课报告。':'从一次训练开始，再用课堂证据安排复练。')
const statusText=computed(()=>{
 if(practice.value)return practiceBusy.value?'正在看你的作答':'面试练习 · 可直接作答'
 if(mode.value==='human')return '记录到训练日志'
 if(connectionError.value)return connectionError.value==='voice'?'语音暂不可用':'在线问答暂不可用'
 return ({idle:client.session?'在线问答已连接':pageLabel.value?'可询问 '+pageLabel.value:'可询问平台功能',connecting:'正在连接',listening:'正在聆听 · 停顿后自动发送',thinking:'正在查找依据',speaking:'正在回答 · 可说话打断',error:'本次问答未完成'})[status.value]
})
const shortcuts=[{key:'prepare',label:'课前准备'},{key:'settings',label:'设备检查'},{key:'call',label:'如何点名'},{key:'captions',label:'字幕设置'},{key:'timeline',label:'课堂记录'}]
const matches=computed(()=>{const key=query.value.trim();return faqs.filter(item=>!key||`${item.q}${item.a}`.includes(key))})
function eventReceived(event){
 if(interviewOnline.receive(event))return
 if(event.type==='level'){level.value=event.level;return}
 if(event.type==='state'){connectionError.value='';status.value=event.state}
 if(event.type==='recognition'){
  partial.value=event.final?'':event.text
  if(event.final&&!messages.value.some(m=>m.turn===event.turn_id&&m.role==='user')){
   const pending=pendingAttachment.value
   const attached=pending&&pending.requestId===event.request_id?pending.item:null
   messages.value.push({role:'user',turn:event.turn_id,text:event.text,attachment:attached})
   if(attached){
    pending.turn=event.turn_id
    attachment.value=null
    draft.value=''
   }
  }
 }
 if(event.type==='attachment_parsed'){
  const message=messages.value.find(m=>m.turn===event.turn_id&&m.role==='user')
  if(message)message.attachmentSummary=event.summary+(event.truncated?'（部分摘录）':'')
  pendingAttachment.value=null
 }
 if(event.type==='attachment_sections'){
  const message=messages.value.find(m=>m.turn===event.turn_id&&m.role==='user')
  if(message)message.attachmentSections=event.sections
 }
 if(['tool_result','tool_resolution','tool_followup'].includes(event.type)){
  let message=messages.value.find(m=>m.turn===event.turn_id&&m.role==='bot')
  if(!message){messages.value.push({role:'bot',turn:event.turn_id,text:'',complete:false});message=messages.value.at(-1)}
  if(event.usage)message.usage=event.usage
  if(event.type==='tool_followup'){message.toolFollowup=event.text;react(replyPose(event.text));return}
  message.tool=event.card
  if(event.card?.status==='failed')react(replyPose('',{failed:true}))
  if(event.card?.name==='quiz_me'&&event.card.question){latestToolQuestion=event.card.question;practice.value=null}
  if(event.card?.name==='add_mistake'&&event.card.status==='confirmed')void loadSavedMistakes()
  if(event.card?.plan)plans.value=[event.card.plan,...plans.value.filter(plan=>plan.id!==event.card.plan.id)]
  const destination=toolResourceRoute(event.card)
  if(destination)void router.push(destination).catch(()=>{})
  return
 }
 if(['error','cancel','closed'].includes(event.type)&&pendingAttachment.value){
  const pending=pendingAttachment.value
  if(event.request_id===pending.requestId||(pending.turn&&(event.turn_id===pending.turn||event.cancelled_turn_id===pending.turn))||event.type==='closed')pendingAttachment.value=null
 }
 if(['answer_delta','answer'].includes(event.type)){
  if(event.type==='answer'&&!voice.value)status.value='idle'
  let message=messages.value.find(m=>m.turn===event.turn_id&&m.role==='bot');if(!message){message={role:'bot',turn:event.turn_id,text:''};messages.value.push(message);message=messages.value.at(-1)}
  message.text=event.text;message.sources=event.sources||[];message.complete=event.type==='answer';message.tier=event.tier
  if(event.usage)message.usage=event.usage
  if(message.complete)react(replyPose(event.text,{tier:event.tier}))
 }
 if(event.type==='cancel'){expirePendingTools();status.value=voice.value?'listening':'idle';level.value=0;const message=messages.value.find(m=>m.turn===event.cancelled_turn_id&&m.role==='bot');if(message&&!message.complete)message.text+='（已停止）'}
 if(event.type==='error'){connectionError.value=event.mode||'';notice.value=event.message;status.value='error';level.value=0;react(replyPose('',{failed:true}));if(!client.session)voice.value=false
  if(event.usage?.calls)messages.value.push({role:'bot',turn:event.turn_id,text:'本次回复未完成。',usage:event.usage})
 }
 if(event.type==='closed'){expirePendingTools();voice.value=false;status.value='idle';notice.value=event.message;partial.value=''}
}
const client=new AssistantClient({api,onEvent:eventReceived,depth:depth.value})
const interviewOnline=new InterviewOnline(client)
function cancelAttachment(){
 pendingAttachment.value=null
 client.interrupt()
}
function stopVoice(message=''){expirePendingTools();pendingAttachment.value=null;client.stop();connectionError.value='';voice.value=false;status.value='idle';level.value=0;partial.value='';notice.value=message}
function close(){toolsOpen.value=false;clearTimeout(interruptionTimer);interruptionTimer=null;practiceReview?.abort();planRequest?.abort();clearReaction();stopVoice();open.value=false;nextTick(()=>fab.value?.focus())}
function toggle(event){if(!suppressClick(event))open.value?close():open.value=true}
function switchMode(value){practiceReview?.abort();planRequest?.abort();stopVoice();historyOpen.value=false;clearTimeout(interruptionTimer);interruptionTimer=null;practice.value=null;mode.value=value;if(value==='human')notice.value='问题会保存到你的训练日志，不会发送给外部客服'}
function answer(item){messages.value.push({role:'bot',text:item.a,free:true,sources:[{id:'system:'+item.id,title:item.q,source:'LINK 功能说明'}]});react(replyPose(item.a))}
function replay(){if(context.value?.active){notice.value='结束授课后可以重新查看导览';return}close();startTour()}
function runAction(key){if(key==='call'){answer(faqs.find(x=>x.id==='students'));return}const action=context.value?.actions?.[key];if(action){close();nextTick(action)}}
async function startVoice(){if(context.value?.active||sending.value)return;historyOpen.value=false;practice.value=null;notice.value='';voice.value=true;mode.value='bot';if(!await client.start('voice',style.value))voice.value=false}
function visiblePageDetails() {
 const workspace=document.querySelector('#workspace-content')
 const visible=node=>node.getClientRects().length&&getComputedStyle(node).visibility==='visible'&&
  !node.closest('[hidden],[inert],[aria-hidden="true"],dialog:not([open])')&&
  (!node.closest('details:not([open])')||node.closest('summary'))
 const renderedText=node=>{
  const walker=document.createTreeWalker(node,NodeFilter.SHOW_TEXT)
  const parts=[]
  while(walker.nextNode()){
   const item=walker.currentNode
   if(!item.parentElement.closest('script,style,template')&&visible(item.parentElement))parts.push(item.textContent.trim())
  }
  return parts.filter(Boolean).join(' ').replace(/\s+/g,' ')
 }
 const read=(key,root=workspace,count=1,limit=1000)=>Array.from(root?.querySelectorAll(key==='mistake'?'[data-assistant-mistake]':`[data-assistant-detail="${key}"]`)||[])
  .filter(visible).slice(0,count).map(node=>node.dataset.assistantValue||renderedText(node)).filter(Boolean).join('\n').slice(0,limit)||undefined
 const reader=route.path==='/resources'?document.querySelector('dialog[data-assistant-reader][open]'):null
 return {weekly:read('weekly'),reportSummary:read('report-summary'),reportProblems:read('report-problems'),
  reportAdvice:read('report-advice'),reportFull:read('report-full',workspace,20,16000),
  resourceTitle:read('resource-title',reader,1,240),resourceSummary:read('resource-summary',reader,2,3200),
  mistakes:read('mistake',panel.value,10,2200),
  recentTraining:[read('training',workspace,8,1600),read('training',panel.value,6,600)].filter(Boolean).join('\n')||undefined}
}
async function send(){
 if(sending.value||pendingAttachment.value||status.value==='connecting')return
 const attached=mode.value==='bot'?attachment.value:null
 const text=draft.value.trim()
 if(!text&&!attached)return
 if(attached){
  if(text.length>2000){notice.value='附件问题最多 2000 字。';return}
  sending.value=true
  notice.value=''
  const requestId=crypto.randomUUID()
  try{
   const ok=client.session||await client.start('text',style.value)
   if(!ok||!open.value||attachment.value!==attached)return
   client.interrupt()
   pendingAttachment.value={requestId,item:attached}
   status.value='thinking'
   await client.sendAttachment(attached.image?'image':'file',attached.file,text,requestId)
  }catch(error){
   if(pendingAttachment.value?.requestId===requestId){
    pendingAttachment.value=null
    status.value='idle'
    if(error.name!=='AbortError'){
     client.interrupt()
     notice.value=error.message||'附件发送失败，请重试。'
    }
   }
  }finally{sending.value=false}
  return
 }
 sending.value=true;draft.value='';notice.value=''
 try{
  const toolRequest=mode.value==='bot'&&isToolRequest(text)
  if(practice.value&&!toolRequest){
   clearTimeout(interruptionTimer)
   interruptionTimer=null
   const turn=crypto.randomUUID()
   const current=practice.value
   clearReaction()
   const review=practiceReview=new AbortController()
   practiceBusy.value=true
   messages.value.push({role:'user',turn,text})
   let next
   if(current.online){
    try{
     const result=await onlineRequest({action:'grade',mode:current.id,question_id:current.questionId,answer:text},review)
     if(review.signal.aborted||practice.value!==current)return
     const missing=result.missing.map(index=>({label:`要点 ${index}`,advice:result.citation.points[index-1]}))
     const total=result.citation.points.length
     next={...current,stage:'complete',message:formatInterviewRubric(result),rubric:result,usage:result.usage,
      assessment:{missing,total,covered:total-missing.length},reaction:missing.length?'encourage':'cheer'}
    }catch(error){
     if(review.signal.aborted||practice.value!==current)return
     const local=startInterview(current.id,current.question,{pressure:pressure.value,topic:topic.value})
     if(current.id==='structured'){
      practice.value=local
      messages.value.push({role:'bot',turn,text:`在线评分暂不可用；离线规则不能给这道真题打分，已换成离线练习题。\n\n${local.message}`,usage:error.usage})
      return
     }
     next=respondToInterview(local,text)
     next.message='离线参考｜'+next.message
     next.usage=error.usage
    }
   }else next=respondToInterview(current,text)
   if(review.signal.aborted||practice.value!==current)return
   rememberPractice(next,text)
   practice.value=next
   messages.value.push({role:'bot',turn,text:next.message,usage:next.usage,free:!current.online})
   if(next.reaction)react(next.reaction)
  }else if(mode.value==='human'){
   await addJournal({entry_date:new Date().toISOString().slice(0,10),body:`[帮助/问题记录] ${text}`});messages.value.push({role:'bot',text:'问题已保存到你的训练日志。'})
  }else{
   const details=visiblePageDetails()
   const asksForVisibleContent=(details.reportFull||details.resourceTitle||details.recentTraining||details.mistakes)&&
    /总结|概括|归纳|解读|分析|待复练|错题|训练记录|这份(?:报告|资源)|这篇/u.test(text)
   const local=!toolRequest&&!asksForVisibleContent&&answerPlatformQuestion(text,route.path,details,path=>router.resolve(path).matched.some(record=>record.path===path))
   if(local){
    if(status.value==='error'){connectionError.value='';status.value='idle'}
    const turn=crypto.randomUUID()
    messages.value.push({role:'user',turn,text},{role:'bot',turn,complete:true,free:true,...local})
    react(replyPose(local.text))
    return
   }
   const uid=auth.user?.id
   const ok=client.session||await client.start('text',style.value);if(!ok){if(uid===auth.user?.id)draft.value=text;return}
   if(uid!==auth.user?.id)return
   const practiceQuestion=practice.value?.activeQuestion||practice.value?.question||latestToolQuestion||history.value[0]?.question
   client.interrupt();status.value='thinking';client.send('text',{text,page_details:visiblePageDetails(),practice_question:toolRequest?practiceQuestion:undefined})
  }
 }catch(error){draft.value=text;notice.value=mode.value==='human'?'问题保存失败：'+journalSubmitErrorMessage(error):'发送失败，请稍后重试'}finally{practiceReview=null;practiceBusy.value=false;sending.value=false;onlineDraft.value=''}
}
async function saveConversation(){
 if(sending.value)return;const lines=messages.value.filter(m=>m.turn&&m.complete!==false&&m.text).slice(-12).map(m=>`${m.role==='user'?'我':'阿贝贝老师'}：${m.text}`)
 if(!lines.length){notice.value='暂无可保存的问答';return}sending.value=true
 try{await addJournal({entry_date:new Date().toISOString().slice(0,10),body:'[助手问答]\n'+lines.join('\n')});notice.value='问答已保存到训练日志'}catch(error){notice.value=journalSubmitErrorMessage(error)}finally{sending.value=false}
}
function openFromEvent(event){
 if(event.detail?.readerClosed){if(readerTarget.value){close();readerTarget.value=null}return}
 const reader=event.detail?.reader
 readerTarget.value=reader?.matches('dialog[data-assistant-reader][open]')?reader:null
 switchMode(event.detail?.mode==='human'?'human':'bot');open.value=true
}
function fullscreenChanged(){fullscreenTarget.value=document.fullscreenElement;nextTick(clampAll)}
function escapePanel(event){if(open.value&&event.key==='Escape'){event.preventDefault();event.stopPropagation();close()}}
function hidden(){if(document.hidden && voice.value)stopVoice('页面已隐藏，语音会话已停止')}
function captureStarted(){stopVoice('课堂采集中，请使用文字帮助')}
watch(open,async value=>{
 suggestedTopic.value=''
 if(!value)return
 const uid=auth.user?.id
 if(uid)void api.get('/assistant/profile',{skipBusy:true,timeout:4000}).then(({data})=>{
  if(open.value&&uid===auth.user?.id)suggestedTopic.value=data.weaknesses?.includes('人际关系')?'人际关系':data.weaknesses?.[0]||''
 }).catch(()=>{})
 history.value=loadInterviewHistory(auth.user?.id)
 const greeting={role:'bot',text:interviewGreeting(auth.user?.name,history.value),greeting:true}
 if(messages.value[0]?.greeting)messages.value[0]=greeting
 else messages.value.unshift(greeting)
 await nextTick()
 if(!open.value)return
 anchorPanel()
 panel.value?.querySelector('button')?.focus()
})
watch(()=>messages.value.map(m=>m.text).join(''),async()=>{await nextTick();if(logRef.value)logRef.value.scrollTop=logRef.value.scrollHeight})
watch(()=>context.value?.active,active=>{if(active)stopVoice('授课中，请使用文字助手')})
watch(()=>route.path,()=>{if(readerTarget.value){close();readerTarget.value=null}})
watch(()=>auth.user?.id,()=>{clearTimeout(interruptionTimer);interruptionTimer=null;history.value=[];clearAttachmentUrls();historyOpen.value=false;plansOpen.value=false;plans.value=[];planReports.value=[];selectedReport.value=null;draft.value='';practiceReview?.abort();planRequest?.abort();clearReaction();stopVoice();practice.value=null;messages.value=[];open.value=false})
watch([open,plansOpen],([opened,showPlans])=>{if(opened&&showPlans)void loadPlans()})
watch(historyOpen,value=>{if(value)void loadSavedMistakes()})
watch(()=>auth.user?.id,()=>{savedMistakes.value=[];latestToolQuestion=''})
onMounted(()=>{window.addEventListener('link-help',openFromEvent);window.addEventListener('link:classroom-capture',captureStarted);document.addEventListener('visibilitychange',hidden);document.addEventListener('fullscreenchange',fullscreenChanged);document.addEventListener('keydown',escapePanel,true)})
onUnmounted(()=>{stopVoice();window.removeEventListener('link-help',openFromEvent);window.removeEventListener('link:classroom-capture',captureStarted);document.removeEventListener('visibilitychange',hidden);document.removeEventListener('fullscreenchange',fullscreenChanged);document.removeEventListener('keydown',escapePanel,true)})
</script>
<template>
<Teleport :to="target"><div class="help-dock" :class="{'in-lesson':inLesson,'lesson-active':context?.active,'assistant-open':open}">
 <button ref="fab" class="help-fab digital-human-fab" type="button" :style="fabStyle"
  data-tour="assistant" :data-pose="pose"
  @focus="focused=$event.currentTarget.matches(':focus-visible');resetRest()" @blur="focused=false" @pointerdown="onFabDown" @click="toggle"
  aria-label="打开阿贝贝老师，可拖动调整位置" aria-controls="link-help-panel" :aria-expanded="open" aria-haspopup="dialog">
  <AssistantCharacter :pose="pose" :look="look" :look-y="lookY" :quiet="context?.active" :animated="animateCharacter" />
 </button>
 <Transition name="assistant-panel"><section v-if="open" id="link-help-panel" ref="panel" class="help-chat" :style="panelStyle" role="dialog" aria-label="阿贝贝老师" @keydown.esc.stop.prevent="close">
  <header class="help-chat__bar" @pointerdown="onPanelDown">
   <div v-if="!role" class="assistant-header-character"><AssistantCharacter :pose="pose" :level="level" :quiet="context?.active" :animated="animateCharacter" /></div>
   <div><strong>阿贝贝老师</strong><p role="status">{{ statusText }}</p></div>
   <button class="assistant-tools-toggle" type="button" aria-controls="assistant-tools" :aria-expanded="toolsOpen" @pointerdown.stop @click="toolsOpen=!toolsOpen">工具</button>
   <button type="button" class="close-x" aria-label="关闭小助手" @click="close">×</button>
  </header>
  <div v-if="suggestedTopic&&mode==='bot'&&!practice&&!voice" class="help-chat__shortcuts">
   <button type="button" :disabled="sending||!!attachment||status==='connecting'" @click="topic=suggestedTopic;selectPractice('structured')">继续练{{ suggestedTopic }}题</button>
  </div>
  <div v-show="toolsOpen" id="assistant-tools" class="assistant-tools-panel">
  <div class="help-chat__guide"><p>{{ guidance }}</p><div class="help-chat__shortcuts"><template v-if="inLesson"><button v-for="item in shortcuts" :key="item.key" type="button" @click="runAction(item.key)">{{ item.label }}</button></template><button type="button" :disabled="context?.active" @click="replay">新手引导</button></div></div>
  <div class="assistant-style" role="group" aria-label="阿贝贝老师语言风格"><button type="button" :aria-pressed="style==='warm'" @click="changeStyle('warm')">温暖</button><button type="button" :aria-pressed="style==='calm'" @click="changeStyle('calm')">冷静</button></div>
  <div class="assistant-style" role="group" aria-label="阿贝贝老师回复篇幅"><button type="button" :aria-pressed="depth==='brief'" @click="changeDepth('brief')">简洁</button><button type="button" :aria-pressed="depth==='detailed'" @click="changeDepth('detailed')">详细</button></div>
  <label><input type="checkbox" :checked="animation" @change="changeAnimation($event.target.checked)"> 角色动画<span v-if="reducedMotion">（系统已减少动态效果）</span></label>
  <div class="help-chat__tools"><input v-model="query" type="search" aria-label="搜索使用帮助" placeholder="查找使用帮助…"/><button type="button" :aria-pressed="mode==='bot'" @click="switchMode('bot')">问答</button><button type="button" :aria-pressed="mode==='human'" @click="switchMode('human')">记录问题</button></div>
  <div v-if="mode==='bot'" class="help-voice"><button v-if="!voice" type="button" :disabled="context?.active||status==='connecting'" @click="startVoice">开始语音对话</button><template v-else><button @click="stopVoice()">结束语音</button><button v-if="['speaking','thinking'].includes(status)" @click="client.interrupt()">停止回答</button></template><details><summary>语音与隐私</summary><p>点击开始后需授权麦克风，语音和问题将发送至系统已配置的语音及模型服务。默认中文，最多5分钟，静默60秒结束；对话默认不保存，可主动记录。授课期间仅支持文字。</p></details></div>
  <div v-if="query&&mode==='bot'" class="help-chat__matches"><button v-for="item in matches" :key="item.id" @click="answer(item);toolsOpen=false">{{ item.q }}</button><p v-if="!matches.length">没有找到匹配的帮助内容，可在下方提问。</p></div>
  </div>
  <div v-if="mode==='bot' && !inLesson" class="interview-practice" aria-label="教资面试备考">
   <div class="interview-practice__title"><strong>教资面试备考</strong><button type="button" :aria-expanded="historyOpen" @click="historyOpen=!historyOpen">错题与成长</button><button v-if="practice" type="button" :disabled="sending" @click="selectPractice()">退出训练</button></div>
   <div class="interview-practice__modules">
    <button v-for="item in interviewModules" :key="item.id" class="interview-skill-card" type="button"
     :aria-label="item.label" :aria-pressed="practice?.id===item.id" :disabled="sending" @click="selectPractice(item.id)">
     <span class="interview-skill-card__inner">
      <span class="interview-skill-card__front"><span aria-hidden="true">{{ cardFaces[item.id].icon }}</span>{{ item.label }}</span>
      <span class="interview-skill-card__back" aria-hidden="true">{{ cardFaces[item.id].back }}</span>
     </span>
    </button>
   </div>
   <div class="interview-controls" v-if="!practice || practice.id==='structured'">
    <label><input v-model="pressure" type="checkbox"> 离线压力面试</label>
    <select v-model="topic" aria-label="结构化题型"><option value="">按画像选题</option><option v-for="item in topicOptions" :key="item">{{ item }}</option></select>
    <button v-if="reviewTopic" type="button" :disabled="sending" @click="startWeakTopic">复练{{ reviewTopic }}</button>
   </div>
   <p v-if="practice?.id==='defense'&&!practice.online">准备好后输入作答，考官可能在你组织答案时插入追问。</p>
   <button v-if="practice?.online" type="button" :disabled="sending" @click="selectPractice(practice.id,true)">改用离线练习</button>
   <p v-if="practice?.id==='plan'">依次输入课题、学段、学科、关键词，用逗号分隔。</p>
   <button v-if="practice?.id==='plan'" type="button" :disabled="sending||!draft.trim()" @click="generatePlan(true)">在线生成教案框架 · 使用问答额度</button>
   <button v-if="practice?.id==='plan'" type="button" :disabled="sending||!draft.trim()" @click="generatePlan()">离线生成框架</button>
   <InterviewRecording v-if="practice?.id==='lesson'&&!historyOpen" @transcript="draft=$event;markActivity()" />
  </div>
  <details v-if="mode==='bot'&&!inLesson" class="interview-history" :open="plansOpen" @toggle="plansOpen=$event.target.open">
   <summary>备考计划与打卡</summary>
   <button type="button" :disabled="sending" @click="buildStudyPlan('week')">生成 7 天备考计划</button>
   <select v-model="selectedReport" aria-label="选择报告"><option :value="null">选择一次评课报告</option><option v-for="item in planReports" :key="item.id" :value="item.id">{{ item.date }} · 报告 #{{ item.id }}</option></select>
   <button type="button" :disabled="sending||!selectedReport" @click="buildStudyPlan('report')">生成复练路线</button>
   <details v-for="plan in plans" :key="plan.id">
    <summary>{{ plan.kind==='week'?'7 天备考计划':`报告 #${plan.report_id} 复练路线` }} · {{ plan.completed.length }}/{{ plan.steps.length }}</summary>
    <p v-if="plan.kind==='week'&&plan.report_id">参考评课报告 #{{ plan.report_id }}</p>
    <ol><li v-for="step in plan.steps" :key="step.day">
     <p>{{ step.task }}｜完成标准：{{ step.criterion }}</p>
     <button type="button" :disabled="checking" :aria-pressed="plan.completed.includes(step.day)" @click="checkStudyPlan(plan,step.day)">{{ plan.completed.includes(step.day)?'取消打卡':'完成打卡' }}</button>
    </li></ol>
   </details>
  </details>
  <p v-if="practiceBusy" role="status">{{ onlineDraft||'正在处理练习…' }} <button type="button" @click="practiceReview?.abort();planRequest?.abort()">取消</button></p>
  <div v-if="role" :key="role" class="assistant-role" :class="'assistant-role--'+role">
   <span>{{ role==='student'?'试讲黑板':practiceModule.label }}</span>
   <div class="assistant-role__visitor"><AssistantCharacter :pose="pose" :role="role" :animated="animateCharacter" /><span>{{ role==='student'?'听课学生':'面试考官' }}</span></div>
  </div>
  <section v-if="historyOpen" class="interview-history" aria-label="错题本与成长档案">
   <header><strong>练习成长档案</strong><label><input v-model="onlyMistakes" type="checkbox"> 只看待复练</label></header>
   <section v-if="savedMistakes.length" aria-label="已保存错题"><strong>已保存到错题本</strong>
    <ul><li v-for="item in savedMistakes" :key="item.id" data-assistant-mistake>{{ item.question }}</li></ul>
   </section>
   <p>最近 {{ history.length }} 条练习记录保存在当前浏览器，按账号区分。覆盖数用于复练自查。</p>
   <ul v-if="structuredProgress.length" class="interview-progress">
    <li v-for="item in structuredProgress" :key="item.label">{{ item.label }} · 最近 {{ item.latest }}<span v-if="item.previous"> · 上次 {{ item.previous }}</span></li>
   </ul>
   <p v-if="!historyEntries.length">{{ onlyMistakes?'暂无待复练记录。':'完成作答后会在这里看到记录。' }}</p>
   <details v-for="(entry,index) in historyEntries" :key="entry.at+'-'+index">
    <summary data-assistant-detail="training" :data-assistant-mistake="entry.assessment.missing.length?'mistake':null">{{ entry.title }} · {{ entry.assessment.covered }}/{{ entry.assessment.total }} 项覆盖 · {{ new Date(entry.at).toLocaleDateString() }}</summary>
    <p v-if="entry.question" :data-assistant-mistake="entry.assessment.missing.length?'mistake':null">{{ entry.question }}</p>
    <p>我的作答｜{{ entry.answer }}</p>
    <p>{{ entry.feedback }}</p>
   </details>
  </section>
  <div v-show="!historyOpen" ref="logRef" class="help-chat__log" aria-label="帮助对话">
   <article v-for="(item,index) in messages" :key="index" :class="item.role">
    <p v-if="item.text">{{ item.text }}</p>
    <small v-if="item.usage" class="assistant-usage-line">{{ usageLabel(item.usage) }}</small>
    <small v-else-if="item.free" class="assistant-usage-line">本地处理 · 免费</small>
    <a v-if="item.attachment" :href="item.attachment.url" :download="item.attachment.file.name" class="assistant-attachment"><img v-if="item.attachment.image" :src="item.attachment.url" :alt="item.attachment.file.name">{{ item.attachment.file.name }}</a>
    <p v-if="item.attachmentSummary" class="assistant-attachment-summary">附件摘录 · {{ item.attachmentSummary }}</p>
    <dl v-if="item.attachmentSections" class="help-sources"><template v-for="(value,label) in item.attachmentSections" :key="label"><dt>{{ label }}</dt><dd>{{ value }}</dd></template></dl>
    <section v-if="item.tool" class="help-sources" aria-label="工具执行结果">
     <strong>{{ item.tool.status==='pending'?'等待确认':item.tool.status==='processing'?'处理中':'工具执行结果' }}</strong>
     <p>{{ item.tool.message }}</p>
     <p v-if="item.tool.question_number">{{ item.tool.source }} · 第 {{ item.tool.question_number }} 题</p>
     <RouterLink v-if="toolResourceRoute(item.tool)" :to="toolResourceRoute(item.tool)">打开{{ item.tool.resource.title }}</RouterLink>
     <template v-if="item.tool.status==='pending'">
      <button type="button" :disabled="!item.complete" @click="confirmTool(item,true)">确认写入</button>
      <button type="button" :disabled="!item.complete" @click="confirmTool(item,false)">取消</button>
     </template>
     <p v-if="item.toolFollowup&&item.toolFollowup!==item.tool.message">{{ item.toolFollowup }}</p>
    </section>
    <details v-if="item.sources?.length" class="help-sources" :open="item.tier==='grounded'||item.sources.some(source=>source.to||source.id==='attachment:1') || undefined"><summary>依据 · {{ item.sources.length }}</summary><div v-for="source in item.sources" :key="source.id"><b>{{ source.title }}</b><span>{{ source.source }} {{ source.location }}</span><RouterLink v-if="source.to" :to="source.to" @click="close">打开{{ source.title }}</RouterLink></div></details>
   </article>
  </div>
  <p v-if="pendingAttachment&&!attachment" class="help-partial" role="status">附件解析中… <button type="button" @click="cancelAttachment">取消</button></p>
  <p v-if="partial" class="help-partial">{{ partial }}</p><p v-if="notice" class="help-notice" role="status">{{ notice }} <button v-if="connectionError&&!toolsOpen" type="button" @click="toolsOpen=true">查看使用帮助</button></p>
  <div v-if="mode==='bot'&&messages.some(m=>m.turn)" class="help-save"><button :disabled="sending" @click="saveConversation">保存本次问答到训练日志</button></div>
  <AssistantComposerTools v-if="open&&!historyOpen&&!context?.active&&mode==='bot'" :disabled="sending||!!pendingAttachment||voice"
   @dictation="addDictation" @attachment="addAttachment" @notice="notice=$event" />
  <div v-if="attachment&&!historyOpen&&mode==='bot'" class="assistant-attachment-draft">
   <img v-if="attachment.image" :src="attachment.url" alt="待发送的照片">
   <span>{{ attachment.file.name }} · {{ pendingAttachment?'解析中…':'发送后解析并用于回答' }}</span>
   <button v-if="pendingAttachment" type="button" @click="cancelAttachment">取消</button>
   <button v-else type="button" :disabled="sending" @click="removeAttachment">移除</button>
  </div>
  <form v-show="!historyOpen" class="help-chat__form" @submit.prevent="send" @input="markActivity" @focusin="resetRest"><textarea v-if="practice" v-model="draft" maxlength="6000" rows="2" aria-label="训练作答" :placeholder="practiceModule.placeholder" /><input v-else v-model="draft" maxlength="2000" type="text" aria-label="问题内容" :placeholder="mode==='human'?'记录到我的训练日志':'可问当前页面、资源或档案'"/><button type="submit" :disabled="sending||!!pendingAttachment">{{ sending?'发送中…':mode==='human'?'保存':'发送' }}</button></form>
  <button class="help-chat__resize" type="button" aria-label="调整聊天窗大小，可拖动或使用方向键" title="拖动调整聊天窗大小"
   @pointerdown="onResizeDown" @pointermove="onResizeMove" @pointerup="onResizeEnd" @pointercancel="onResizeEnd" @lostpointercapture="onResizeEnd" @keydown="onResizeKey">◣</button>
 </section></Transition>
</div></Teleport>
</template>
