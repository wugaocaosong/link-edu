<template>
  <section class="adaptive-page" aria-labelledby="adaptive-title">
    <header class="learning-header">
      <div><p class="learning-caption">临客学习工作坊</p><h1 id="adaptive-title">让下一次练习，有据可循。</h1><p>从一次诊断出发，把教学技能变成可以持续练习的行动。</p></div>
      <div class="learning-actions"><button class="primary" :disabled="busy" @click="startQuiz()">开始六维诊断</button><button :disabled="busy || !overview" @click="generatePath">更新学习路径</button></div>
    </header>
    <p v-if="error" class="learning-error" role="alert">{{ error }} <button :disabled="busy" @click="reload">重新加载</button></p>
    <p v-if="!overview && !error" role="status">正在读取学习记录…</p>
    <template v-if="overview">
      <section class="learning-skills" aria-label="六维技能概览">
        <article v-for="skill in overview.skills" :key="skill.skill_id">
          <header><h2>{{ skill.name }}</h2><span>{{ skill.label }}</span></header>
          <p class="skill-score">{{ skill.score === null ? '—' : skill.score }}<small>{{ skill.score === null ? '待诊断' : '/ 100' }}</small></p>
          <div class="skill-meter" :aria-label="`${skill.name} ${skill.score ?? '待诊断'}`"><span :style="{ width: `${skill.score ?? 0}%` }"></span></div>
          <p class="skill-evidence">测验 {{ skill.quiz_score ?? '暂无' }} · 训练 {{ skill.training_score ?? '暂无' }}</p>
          <button :disabled="busy" @click="startQuiz(skill.skill_id)">专项复测</button>
        </article>
      </section>
      <details class="learning-rule"><summary>掌握度如何计算？</summary><p>{{ overview.rule }}这些阈值是平台学习规则，不是标准化教师评价。阅读完成不会直接增加掌握度。</p><p>测验取最近三次平均分；训练仅使用带有效证据的最新报告。旧演示评分和证据不足的维度不计入。</p></details>
      <div class="learning-columns">
        <section class="learning-path" aria-labelledby="path-title">
          <header class="section-heading"><h2 id="path-title">我的学习路径</h2><span v-if="overview.path">{{ completedCount }} / {{ overview.path.steps.length }} 步已完成</span></header>
          <div v-if="!overview.path" class="learning-empty"><h3>先认识自己，再选择下一步。</h3><p>完成诊断后，我们会把需要加强的技能排在前面。你也可以先生成入门学习路径。</p><button :disabled="busy" @click="generatePath">生成学习路径</button></div>
          <ol v-else class="path-list">
            <li v-for="step in overview.path.steps" :key="step.id" :class="{ done: step.status === 'completed' }">
              <span class="path-marker" aria-hidden="true">{{ step.status === 'completed' ? '✓' : kindLabels[step.kind] }}</span>
              <div class="path-body"><h3>{{ step.title }}</h3><p>{{ reasonText(step.reason) }}</p>
                <small v-if="step.reason.evidence.training">课堂 #{{ step.reason.evidence.training.session_id }} · 报告版本 {{ step.reason.evidence.training.version }}</small>
                <p v-if="!step.available" class="learning-error">资源已停用，请更新学习路径。</p>
                <template v-else-if="step.kind === 'resource'">
                  <button :disabled="busy" @click="openMaterial = openMaterial === step.id ? null : step.id">{{ openMaterial === step.id ? '收起学习卡' : '阅读学习卡' }}</button>
                  <div v-if="openMaterial === step.id" class="material-content"><p>{{ step.content }}</p><button :disabled="busy || step.status === 'completed'" @click="complete(step)">{{ step.status === 'completed' ? '已完成阅读' : '完成阅读' }}</button></div>
                </template>
                <button v-else-if="step.kind === 'diagnostic' || step.kind === 'retest'" :disabled="busy" @click="startQuiz(step.skill_id)">{{ step.kind === 'diagnostic' ? '开始诊断' : '开始复测' }}</button>
                <template v-else>
                  <template v-if="step.practice_status === 'superseded'"><p>原报告已修订，请更新学习路径后继续训练。</p><button :disabled="busy" @click="generatePath">更新学习路径</button></template>
                  <router-link v-else-if="step.practice_plan_id" :to="{ path: '/classroom', query: { practice: step.practice_plan_id } }">进入证据关联训练</router-link>
                  <template v-else><p>以“分数的初步认识”为情境，写一段教学设计，标出你对这项技能的具体应用，再通过复测检查理解。</p><button :disabled="busy || step.status === 'completed'" @click="complete(step)">{{ step.status === 'completed' ? '已记录自练' : '记录自练完成' }}</button><small>自我记录，仅计入学习进度。</small></template>
                </template>
              </div>
            </li>
          </ol>
        </section>
        <aside class="learning-history"><h2>诊断与复测记录</h2><p v-if="!overview.history.length">你的第一份学习记录，从一次诊断开始。</p><button v-for="item in overview.history" :key="item.id" :disabled="busy" @click="openQuiz(item.id)"><strong>{{ item.skill_id ? skillName(item.skill_id) + '复测' : '六维诊断' }}</strong><span>{{ item.status === 'submitted' ? '查看结果与解析' : '继续作答' }}</span><small>{{ new Date(item.created_at + 'Z').toLocaleString('zh-CN') }}</small></button></aside>
      </div>
    </template>
    <dialog ref="quizDialog" class="quiz-dialog" @close="quiz = null" @cancel="quiz = null">
      <template v-if="quiz"><header><div><h2>{{ quiz.status === 'submitted' ? '测验结果与解析' : quiz.skill_id ? '技能专项复测' : '六维技能诊断' }}</h2><p>{{ quiz.status === 'submitted' ? '对照理由，理解每一次选择。' : `共 ${quiz.questions.length} 题，请选择最合适的一项。` }}</p></div><button aria-label="关闭测验" @click="quizDialog.close()">关闭</button></header>
        <p v-if="quizError" role="alert" class="learning-error">{{ quizError }}</p>
        <form @submit.prevent="submitQuiz">
          <fieldset v-for="(q, index) in quiz.questions" :key="q.id"><legend>{{ index + 1 }}. {{ q.prompt }}</legend>
            <label v-for="(text, key) in q.options" :key="key" :class="{ correct: quiz.status === 'submitted' && key === q.answer }"><input v-model="answers[q.id]" type="radio" :name="`q-${q.id}`" :value="key" :disabled="quiz.status === 'submitted' || busy" required /><span>{{ key }}. {{ text }}</span></label>
            <p v-if="quiz.status === 'submitted'" class="answer-explanation">{{ q.correct ? '回答正确' : `你的选择：${q.selected}；正确答案：${q.answer}` }}。{{ q.explanation }}</p>
          </fieldset>
          <footer><span v-if="quiz.status !== 'submitted'">已答 {{ Object.keys(answers).length }} / {{ quiz.questions.length }}</span><button v-if="quiz.status !== 'submitted'" class="primary" :disabled="busy" type="submit">提交并查看结果</button><button v-else type="button" @click="quizDialog.close(); generatePath()" :disabled="busy">更新我的学习路径</button></footer>
        </form>
      </template>
    </dialog>
  </section>
</template>

<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import { api } from '../services/api'
const overview = ref(null), busy = ref(false), error = ref(''), quizError = ref('')
const quiz = ref(null), quizDialog = ref(null), answers = ref({}), openMaterial = ref(null)
const kindLabels = { diagnostic: '测', resource: '读', practice: '练', retest: '验' }
const completedCount = computed(() => overview.value?.path?.steps.filter(s => s.status === 'completed').length ?? 0)
const skillName = id => overview.value?.skills.find(s => s.skill_id === id)?.name || id
const reasonText = s => s.score === null ? '尚无有效记录，从基础诊断开始。' : `${s.name}当前掌握度 ${s.score}，建议${s.label}。依据${s.quiz_score !== null ? '最近测验' : ''}${s.quiz_score !== null && s.training_score !== null ? '与' : ''}${s.training_score !== null ? '有效课堂反馈' : ''}。`
async function run(fn) { if (busy.value) return; busy.value = true; error.value = ''; try { await fn() } catch (e) { error.value = e.response?.data?.message || '读取失败，请检查实验服务连接后重试。' } finally { busy.value = false } }
async function load() { overview.value = (await api.get('/adaptive/overview')).data }
const reload = () => run(load)
async function showQuiz(data) { quiz.value = data; answers.value = Object.fromEntries(data.questions.filter(q => q.selected).map(q => [q.id, q.selected])); quizError.value = ''; await nextTick(); if (!quizDialog.value.open) quizDialog.value.showModal() }
const startQuiz = skill_id => run(async () => { const data = (await api.post('/adaptive/quizzes', { skill_id, request_key: crypto.randomUUID() })).data; await showQuiz(data); await load() })
const openQuiz = id => run(async () => showQuiz((await api.get(`/adaptive/quizzes/${id}`)).data))
const generatePath = () => run(async () => { await api.post('/adaptive/paths', {}); await load() })
const complete = step => run(async () => { await api.post(`/adaptive/steps/${step.id}/complete`, {}); await load() })
async function submitQuiz() { if (busy.value) return; busy.value = true; quizError.value = ''; try { await showQuiz((await api.post(`/adaptive/quizzes/${quiz.value.id}/submit`, { answers: answers.value })).data); await load() } catch (e) { quizError.value = e.response?.data?.message || '提交失败，你的选择仍保留，请重试。' } finally { busy.value = false } }
onMounted(reload)
</script>

<style scoped>
.adaptive-page{--learn-ink:var(--ui-ink,#f0eaf7);--learn-paper:var(--ui-surface,#251d32);--learn-line:var(--ui-line,#44384f);--learn-accent:var(--ui-blue,#9167bd);color:var(--learn-ink);padding:8px 8px 40px;max-width:1500px;margin:auto}.learning-header{display:flex;justify-content:space-between;gap:28px;align-items:center;padding:18px 0 28px}.learning-caption{font-size:13px;color:var(--learn-accent);margin:0 0 10px}.learning-header h1{font-size:clamp(24px,2.4vw,36px);line-height:1.35;margin:0 0 12px;letter-spacing:-.02em}.learning-header p{line-height:1.7;max-width:620px}.learning-actions{display:flex;gap:10px;flex-wrap:wrap;flex-shrink:0}.adaptive-page button,.adaptive-page a{font:inherit}.adaptive-page button{border:1px solid var(--learn-line);border-radius:8px;background:var(--learn-paper);color:var(--learn-ink);padding:9px 14px;cursor:pointer}.adaptive-page button.primary{background:var(--learn-accent);color:white;border-color:var(--learn-accent)}.adaptive-page button:disabled{opacity:.55;cursor:default}.adaptive-page button:focus-visible,.adaptive-page a:focus-visible{outline:3px solid #688ccc;outline-offset:3px}.learning-skills{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));background:var(--learn-paper);border:1px solid var(--learn-line);border-radius:14px;overflow:hidden}.learning-skills article{padding:20px 16px;border-right:1px solid var(--learn-line)}.learning-skills article:last-child{border-right:0}.learning-skills header{display:flex;flex-direction:column;gap:8px}.learning-skills h2{font-size:16px;margin:0}.learning-skills header span{font-size:12px;opacity:.7}.skill-score{font-size:32px;margin:16px 0 10px;font-variant-numeric:tabular-nums}.skill-score small{font-size:12px;margin-left:8px;opacity:.65}.skill-meter{height:5px;background:#e8e9ef;border-radius:5px;overflow:hidden}.skill-meter span{display:block;height:100%;background:var(--learn-accent)}.skill-evidence{font-size:11px;line-height:1.6}.learning-skills button{padding:6px 10px;font-size:12px}.learning-rule{font-size:13px;line-height:1.8;margin:18px 0 30px;max-width:900px}.learning-rule summary{cursor:pointer}.learning-columns{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:32px}.section-heading{display:flex;justify-content:space-between;align-items:center}.section-heading h2,.learning-history h2{font-size:20px;margin:0 0 18px}.section-heading span{font-size:13px;opacity:.65}.learning-empty{padding:35px;background:var(--learn-paper);border-radius:12px;border:1px solid var(--learn-line)}.learning-empty p{line-height:1.8}.path-list{list-style:none;padding:0;margin:0}.path-list li{display:flex;gap:16px;padding:0 0 28px;position:relative}.path-list li:not(:last-child):before{content:'';position:absolute;top:38px;bottom:0;left:18px;border-left:1px solid var(--learn-line)}.path-marker{width:36px;height:36px;flex-shrink:0;display:grid;place-items:center;border:1px solid var(--learn-line);background:var(--learn-paper);border-radius:50%;font-size:13px}.done .path-marker{background:#e4f0e9;color:#245c43}.path-body{flex:1;min-width:0;border-bottom:1px solid var(--learn-line);padding:4px 0 22px}.path-body h3{font-size:17px;margin:0 0 8px}.path-body p{font-size:14px;line-height:1.8;margin:5px 0 12px}.path-body small{display:block;opacity:.7;font-size:12px;margin:8px 0}.path-body a{color:var(--learn-accent);text-decoration:underline}.material-content{padding:20px;margin-top:15px;background:var(--learn-paper);border-radius:10px;border:1px solid var(--learn-line)}.material-content p{white-space:pre-line;line-height:1.9}.learning-history{border-left:1px solid var(--learn-line);padding-left:24px}.learning-history>button{display:flex;flex-direction:column;text-align:left;gap:8px;width:100%;margin-bottom:10px;padding:15px}.learning-history span,.learning-history small{font-size:12px;opacity:.7}.learning-error{color:#a12f30;background:#fff0ef;padding:12px;border-radius:8px}.quiz-dialog{width:min(760px,calc(100vw - 32px));max-height:88dvh;padding:28px;border:1px solid var(--learn-line);border-radius:16px;background:var(--learn-paper);color:var(--learn-ink)}.quiz-dialog::backdrop{background:#18203299}.quiz-dialog>header{display:flex;justify-content:space-between;gap:20px;align-items:start}.quiz-dialog h2{font-size:22px;margin:0}.quiz-dialog header p{font-size:14px}.quiz-dialog fieldset{border:0;border-bottom:1px solid var(--learn-line);padding:18px 0;margin:10px 0 20px}.quiz-dialog legend{font-weight:600;line-height:1.8}.quiz-dialog label{display:flex;align-items:baseline;gap:10px;border:1px solid var(--learn-line);padding:12px;margin:8px 0;border-radius:8px;line-height:1.6;cursor:pointer}.quiz-dialog label.correct{border-color:#599779;background:#edf7f1;color:#245c43}.quiz-dialog input{accent-color:var(--learn-accent)}.answer-explanation{line-height:1.8;font-size:14px}.quiz-dialog footer{display:flex;justify-content:space-between;align-items:center;gap:20px;position:sticky;bottom:-28px;background:var(--learn-paper);padding:18px 0}.quiz-dialog footer span{font-size:13px}@media(max-width:1200px){.learning-skills{grid-template-columns:repeat(3,minmax(0,1fr))}.learning-skills article:nth-child(-n+3){border-bottom:1px solid var(--learn-line)}.learning-header{align-items:start;flex-direction:column}.learning-columns{grid-template-columns:minmax(0,1fr) 240px}}@media(max-width:750px){.learning-skills{grid-template-columns:repeat(2,minmax(0,1fr))}.learning-skills article{border-bottom:1px solid var(--learn-line)}.learning-columns{grid-template-columns:1fr}.learning-history{padding-left:0;border-left:0;border-top:1px solid var(--learn-line);padding-top:24px}.learning-header h1{font-size:25px}.quiz-dialog{padding:18px}.quiz-dialog footer{bottom:-18px}.section-heading{align-items:start;gap:12px}}
</style>
