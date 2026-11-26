<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { api } from '../services/api.js'
import { yuan } from '../services/assistantUsage.js'

const quota=ref(null), quotaPending=ref(true)
const detailsOpen=ref(false), page=ref(0), usage=ref(null)
const error=ref(''), pending=ref(false)
let request
const lifetime=new AbortController()
const dateLabel=value=>new Date(value).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai'})
const services={dialogue:'文本模型',vision:'视觉识别'}

async function loadQuota(){
 quotaPending.value=true
 try{
  const {data}=await api.get('/assistant/quota',{signal:lifetime.signal,timeout:8000,skipBusy:true})
  if(!lifetime.signal.aborted&&Number.isFinite(data?.remaining_cny))quota.value=data
 }catch{}
 finally{quotaPending.value=false}
}

async function load(){
 request?.abort()
 const controller=request=new AbortController()
 pending.value=true;error.value=''
 try{
  const {data}=await api.get('/assistant/usage',{params:{page:page.value},signal:controller.signal,timeout:8000,skipBusy:true})
  if(controller.signal.aborted)return
  usage.value=data;quota.value=data
 }catch{if(!controller.signal.aborted)error.value='暂时无法读取，请重试。'}
 finally{if(request===controller)pending.value=false}
}
function goPage(next){page.value=next;void load()}
watch(detailsOpen,()=>{if(detailsOpen.value)void load();else request?.abort()})
onMounted(loadQuota)
onUnmounted(()=>{request?.abort();lifetime.abort()})
</script>

<template>
 <section class="assistant-account" aria-label="阿贝贝额度和会员">
  <header>
   <div>
    <p class="assistant-account__label">阿贝贝 · AI 体验额度</p>
    <h2 v-if="quota">{{ yuan(quota.remaining_cny) }} <span>剩余／共 {{ yuan(quota.allowance_cny) }}</span></h2>
    <p v-else>{{ quotaPending?'正在读取余额…':'余额暂不可用' }} <button v-if="!quotaPending" type="button" @click="loadQuota">重试</button></p>
   </div>
   <div class="assistant-account__actions" role="group" aria-label="账户详情">
    <button type="button" aria-controls="assistant-account-usage" :aria-expanded="detailsOpen" @click="detailsOpen=!detailsOpen">用量明细</button>
   </div>
  </header>
  <p class="assistant-account__explanation">注册一次性获赠 ¥2.00 虚拟体验金，仅用于阿贝贝模型调用，不是真实货币。</p>
  <div v-if="detailsOpen" id="assistant-account-usage" class="assistant-account__details">
  <p v-if="pending" role="status">正在加载…</p>
  <p v-if="error" class="assistant-account__notice" role="status">{{ error }} <button type="button" @click="load">刷新</button></p>
   <p>这里记录 AI 模型调用。一问可能有多次调用。待结算为临时预留，不是最终扣费；本地帮助和纯离线练习不计费。</p>
   <ul v-if="usage?.items?.length" class="assistant-account__ledger">
    <li v-for="(row,index) in usage.items" :key="index">
     {{ dateLabel(row.at) }} · {{ services[row.service]||'模型调用' }} ·
     {{ row.status==='pending'?'待结算预留':'已结算' }} {{ yuan(row.amount_cny) }}
    </li>
   </ul>
   <p v-else-if="usage&&!pending">暂无模型用量。</p>
   <div v-if="page||usage?.has_more">
    <button type="button" :disabled="pending||!page" @click="goPage(page-1)">上一页</button>
    <button type="button" :disabled="pending||!usage?.has_more" @click="goPage(page+1)">下一页</button>
   </div>
  </div>
 </section>
</template>

<style scoped>
.assistant-account { padding: clamp(16px, 3vw, 28px); color: var(--member-ink); background: var(--member-surface); border: 1px solid var(--member-line); border-radius: 16px; font-size: 14px; line-height: 1.6; }
.assistant-account header { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
.assistant-account__label { color: var(--member-accent); font-weight: 700; }
.assistant-account h2 { margin: 0; font-size: clamp(23px, 3vw, 32px); font-variant-numeric: tabular-nums; }
.assistant-account h2 span { color: var(--member-muted); font-size: 13px; font-weight: 500; }
.assistant-account .assistant-account__explanation { color: var(--member-muted); margin-top: 12px; }
.assistant-account__actions { display: flex; flex-wrap: wrap; gap: 8px; }
.assistant-account__details { margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--member-line); }
.assistant-account__notice { padding: 8px 12px; background: var(--member-tint); border-radius: 8px; }
.assistant-account__ledger { padding-left: 1.25em; }
.assistant-account p, .assistant-account ul { margin-block: 4px; }
.assistant-account button { min-height: 36px; padding: 5px 12px; color: var(--member-accent); background: var(--member-surface); border: 1px solid var(--member-accent); border-radius: 8px; cursor: pointer; }
.assistant-account button:hover:not(:disabled) { background: var(--member-tint); }
.assistant-account button[aria-expanded="true"] { color: white; background: var(--member-accent); }
.assistant-account button:focus-visible { outline: 2px solid var(--member-accent); outline-offset: 2px; }
.assistant-account button:disabled { opacity: .65; cursor: default; }
.assistant-account__details button { margin: 3px 8px 3px 0; }
</style>
