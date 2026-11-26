<script setup>
import { computed } from 'vue'
import ClassroomDialog from './ClassroomDialog.vue'
import ClassroomCalibration from './ClassroomCalibration.vue'
import { speechProviderLabel } from '../services/classroomStatus.js'
const open = defineModel({ type: Boolean })
const consent = defineModel('consent', { type: Boolean })
const cameraConsent = defineModel('cameraConsent', { type: Boolean })
const recordEnabled = defineModel('recordEnabled', { type: Boolean })
const mode = defineModel('mode', { type: String })
const topic = defineModel('topic', { type: String })
const subject = defineModel('subject', { type: String })
const props = defineProps({ capabilities: Object, practicePlan: Object, study: Boolean, concealCamera: Boolean, room: Object, state: String,
  busy: Boolean, active: Boolean, cameraEnabled: Boolean, pose: Object, blockers: Array,
  hint: String, loading: Boolean, needsSettings: Boolean })
defineEmits(['start', 'preview', 'refresh', 'settings'])
const asr = computed(() => props.capabilities?.services?.asr?.provider)
const llm = computed(() => props.capabilities?.services?.dialogue?.provider === 'openai_next' ? 'OpenAI Next（DeepSeek 模型）' : 'DeepSeek')
</script>
<template>
  <ClassroomDialog v-model="open" title="课前准备">
    <div class="classroom-preparation">
      <div class="preparation-topic"><div v-if="study"><small>{{ capabilities?.scenario?.grade || '小学数学' }}</small><h3>{{ capabilities?.scenario?.topic || '分数的初步认识' }}</h3></div>
<div v-else class="topic-fields"><label>学科<select v-model="subject" :disabled="!!room || busy"><option value="小学数学">小学数学</option><option value="信息科技">信息技术</option><option value="其他">其他</option></select></label><label>课程名称 / 本节课题<input v-model.trim="topic" maxlength="128" :disabled="!!room || busy" placeholder="例如：认识几分之一、Python变量与数据类型" /></label><small v-if="subject!=='小学数学' || topic!==capabilities?.scenario?.topic">自定义课题采用通用课堂反馈，虚拟学生不预设该学科的标准答案。</small></div>
        <strong v-if="study">10 分钟 · 认识几分之一</strong>
        <label v-else-if="!room" class="lesson-mode"><span class="sr-only">训练时长</span><select id="class-mode" v-model="mode" :disabled="busy"><option value="full">10 分钟 · 完整课</option><option value="fragment">8 分钟 · 专项练习</option></select></label>
      </div>
      <p v-if="!study && !room && !practicePlan && !busy" class="preparation-practice">普通练习将生成课堂教练反馈。参加《认识几分之一》测评，请从 <router-link to="/study">实验场次</router-link> 进入，以便关联前后测与本轮反馈。</p>
      <section v-if="state !== 'ended'" class="preparation-permissions" aria-label="设备与授权">
        <h3>设备与授权</h3>
        <label><input type="checkbox" v-model="consent" :disabled="active || busy" />同意语音识别与 AI 评课</label>
        <label v-if="!concealCamera"><input type="checkbox" v-model="cameraConsent" :disabled="active || busy" />同意摄像头开启</label>
        <p v-if="concealCamera">本场不显示摄像头画面，反馈报告也不使用画面。授课录像仍会保存在这台电脑，课后可以导出给研究人员。</p>
        <p v-else-if="study">本场录制师生音画，保存在当前浏览器，课后可导出。</p>
        <label v-if="!study"><input type="checkbox" v-model="recordEnabled" :disabled="!!room || busy" />本机录像<span>课后选择保存或放弃</span></label>
        <button v-if="!concealCamera" class="class-btn secondary" :disabled="!cameraConsent || busy || active" @click="$emit('preview')">{{ cameraEnabled ? '查看授课画面' : '开启摄像头预览' }}</button>
      </section>
      <details class="disclosure privacy-details"><summary>隐私与录像说明</summary>
        <p>麦克风音频上传{{ speechProviderLabel(asr) }}识别；文字与本地动作摘要提交{{ llm }}用于对话和评课。未选择录像时不保存原始录音，转写与课堂事件会保留。</p>
        <p>本机录像包含教师画面、学生、字幕和师生声音，不上传服务器；课后选择保存或放弃。清理浏览器数据会移除已保存录像，下载副本需自行保管。</p>
        <p>摄像头为授课必需条件，仍须浏览器授权。动作检测在本机运行，不做人脸识别或心理推断。云端截图分析需另行授权。</p>
        <p v-if="study">暂停会停止计时和录像。结束后先填写独立自评，再到实验场次领取本组反馈。</p>
        <p v-else>暂停同时停止计时和录像。有效授课满 10 秒且转写、完整学生反馈充足才评课；动作或场景不足时教态不评分。</p>
      </details>
      <details v-if="!study && capabilities?.scenario && subject==='小学数学' && topic===capabilities.scenario.topic" class="disclosure preparation-scenario"><summary>训练目标与学生设定</summary>
        <p>{{ capabilities.scenario.objective }}</p>
        <ul><li v-for="(student,id) in capabilities.scenario.students" :key="id"><strong>{{ { ming:'小明', yu:'小雨', lin:'小林' }[id] }}</strong><span>{{ student.focus }}</span></li></ul>
        <p class="subtle-note">这些是模拟学生的初始设定，状态变化用于训练复盘，不代表真实儿童的学习测量。</p>
      </details>
      <section v-if="practicePlan" class="preparation-practice" aria-label="本次复练任务"><h3>本次复练任务</h3><p>{{ practicePlan.task_text }}</p><p>完成判据：本节至少记录 {{ practicePlan.criteria?.minimum_observed || 1 }} 次目标行为。</p><small>来自课堂 #{{ practicePlan.source_session_id }}，完成后可返回原报告核对。</small></section>
      <ClassroomCalibration v-if="!concealCamera" :enabled="cameraEnabled" :active="active" :motion="pose" :study="study" />
      <section v-if="!room || ['paused','disconnected'].includes(state)" class="preparation-readiness" aria-label="开课检查">
        <p role="status">{{ hint }}</p>
        <ul v-if="blockers?.length"><li v-for="reason in blockers" :key="reason.code">{{ reason.message }}</li></ul>
        <div class="preparation-actions"><button class="text-action" :disabled="loading || busy" @click="$emit('refresh')">{{ loading ? '读取中…' : '刷新设备与服务状态' }}</button><button v-if="needsSettings" class="text-action" @click="$emit('settings')">查看配置</button></div>
      </section>
      <footer class="preparation-footer"><button class="class-btn secondary" @click="open = false">返回课堂</button><button v-if="!active && state !== 'ended'" class="class-btn" :disabled="blockers?.length > 0 || busy" @click="$emit('start')">{{ room ? '继续授课' : '开始授课' }}</button></footer>
    </div>
  </ClassroomDialog>
</template>
<style scoped>
.classroom-preparation { display:grid; gap:16px; }
.preparation-topic { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
.preparation-topic h3 { margin:4px 0 0; font-size:20px; }
.topic-fields{display:grid;grid-template-columns:minmax(140px,.35fr) minmax(260px,1fr);gap:10px;width:min(100%,680px)}
.topic-fields label{display:grid;gap:5px;font-size:12px;color:var(--class-muted)}
.topic-fields input,.topic-fields select{min-width:0;padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:var(--class-surface);color:var(--class-ink);font:inherit}
.topic-fields small{grid-column:1/-1;color:var(--class-muted)}
.preparation-topic small { color:var(--class-muted); }
.preparation-permissions { display:grid; gap:8px; padding:16px; border:1px solid var(--line); border-radius:12px; background:linear-gradient(135deg,#b45cff0d,#ff7a1808); }
.preparation-permissions h3 { margin:0 0 4px; }
.preparation-permissions label { display:flex; align-items:center; gap:8px; min-height:32px; font-size:13px; flex-wrap:wrap; }
.preparation-permissions label span { font-size:11px; color:var(--class-muted); }
.preparation-permissions button { justify-self:start; }
.preparation-scenario ul { display:grid; gap:8px; padding:0; list-style:none; }
.preparation-scenario li { display:flex; gap:12px; font-size:12px; }
.preparation-scenario li strong { flex:none; color:var(--class-ink); }
.preparation-scenario li span { color:var(--class-muted); }
.preparation-readiness { border-top:1px solid var(--line); padding-top:12px; font-size:12px; }
.preparation-readiness ul { color:var(--class-muted); padding-left:20px; }
.preparation-actions,.preparation-footer { display:flex; flex-wrap:wrap; gap:12px; }
.preparation-footer { justify-content:flex-end; padding-top:8px; }
.preparation-practice { padding:12px; background:var(--class-surface-raised); border-radius:8px; font-size:13px; }
@media(max-width:560px) { .topic-fields{grid-template-columns:1fr}.preparation-permissions { padding:12px; } }
</style>
