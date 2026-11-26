<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../services/api'
import { useAuthStore } from '../stores/auth'
import StudyAssessment from '../components/StudyAssessment.vue'
import StudyDebrief from '../components/StudyDebrief.vue'

const names={pre:'共同前测',round1:'首次试讲',round2:'第二次试讲',post:'共同后测'}
const auth=useAuthStore(), userId=computed(()=>Number(auth.user?.id))
const info=ref(null), selected=ref(null), consent=ref(false), error=ref(''), busy=ref(false)
const row=computed(()=>info.value?.attempts.find(r=>r.id===selected.value))
const training=computed(()=>['round1','round2'].includes(row.value?.stage))
const revision=ref(0)
async function refresh(keep=false){
  error.value=''
  try{
    info.value=(await api.get('/study')).data
    if(!keep || !row.value)selected.value=info.value.attempts?.filter(r=>r.stage===info.value.stage).at(-1)?.id ?? null
    consent.value=false
    revision.value++
  }catch(e){error.value=e.response?.data?.message || e.message}
}
async function enter(){
  busy.value=true;error.value=''
  try{
    const {data}=await api.post('/study/attempts',{stage:info.value.stage,consent:consent.value})
    await refresh(); selected.value=data.id
  }catch(e){error.value=e.response?.data?.message || e.message}
  finally{busy.value=false}
}
onMounted(refresh)
</script>
<template>
  <main class="fraction-study">
    <header><h1>认识几分之一</h1><router-link to="/classroom">返回演绎厅</router-link></header>
    <p v-if="error" role="alert">{{ error }} <button @click="refresh()">重试</button></p>
    <p v-if="info && !info.enrolled">当前账号尚未登记本次实验，请联系协调员。</p>
    <template v-if="info?.enrolled">
      <p>{{ info.code }} <template v-if="info.arm"> · {{ info.arm==='multimodal'?'多模态评课组':'转写评课组' }}</template></p>
      <nav v-if="info.attempts.length" aria-label="我的实验场次">
        <button v-for="r in info.attempts" :key="r.id" :aria-current="r.id===selected?'step':undefined"
          :disabled="row && !row.finished && row.stage===info.stage && !training"
          @click="selected=r.id">{{ names[r.stage] }}{{ r.number>1?' · 补测 '+(r.number-1):'' }}</button>
      </nav>
      <section v-if="info.stage && (!row || row.finished || row.stage!==info.stage)">
        <h2>下一场 · {{ names[info.stage] }}</h2>
        <p v-if="info.stage==='round2'">按预约间隔 7 天到场。首轮修订目标：{{ info.attempts.filter(r=>r.stage==='round1').at(-1)?.goal }}</p>
        <label><input type="checkbox" v-model="consent">已核对场次安排，知悉本场录音录像用途并同意开始</label>
        <button :disabled="busy || !consent" @click="enter">进入场次</button>
      </section>
      <p v-if="!info.stage">全部场次已完成。</p>
      <template v-if="row">
        <StudyAssessment v-if="!training" :key="row.id" :attempt="row" :user-id="userId" @finished="refresh()"/>
        <section v-else-if="row.class_state!=='ended'">
          <h2>{{ names[row.stage] }} · 10 分钟</h2>
          <p>请使用{{ row.stage==='round1'?'折纸':'纸带' }}，围绕“平均分”和“几分之一”面向三名学生授课。</p>
          <router-link :to="{path:'/classroom',query:{study:row.id,...(row.session_id?{session:row.session_id}:{})}}">进入虚拟学生课堂</router-link>
        </section>
        <StudyDebrief v-else :key="row.id+'-'+revision" :attempt="row" :user-id="userId" :code="info.code" @changed="refresh(true)"/>
      </template>
    </template>
  </main>
</template>
<style>
.fraction-study{max-width:54rem;margin:auto;padding:clamp(1rem,4vw,3rem);height:100dvh;overflow:auto;box-sizing:border-box;color:var(--text-primary,inherit)}
.fraction-study header,.fraction-study .actions,.fraction-study nav{display:flex;align-items:center;gap:.8rem;flex-wrap:wrap}
.fraction-study header{justify-content:space-between}
.fraction-study section{padding-block:1.25rem;border-top:1px solid #978d91}
.fraction-study video{display:block;max-height:44vh;max-width:100%;border-radius:.6rem;margin-block:.8rem;background:#19151a}
.fraction-study label{display:block;margin-block:.8rem}
.fraction-study input:not([type=checkbox]),.fraction-study textarea{display:block;width:min(100%,36rem);box-sizing:border-box;padding:.5rem;font:inherit}
.fraction-study button,.fraction-study a{padding:.5rem .8rem;cursor:pointer;font:inherit;border-radius:.4rem}
.fraction-study button[aria-current=step]{outline:2px solid currentColor}
.fraction-study button:disabled{opacity:.6;cursor:default}
.study-report{white-space:pre-wrap;line-height:1.7}
</style>
