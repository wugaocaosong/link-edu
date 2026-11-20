<template>
  <div class="sparse-page profile-page" :class="`profile-page--${page}`">
<PaperTitle v-if="!isStudio" :text="pageTitle" />
    <p v-if="profileError" class="dock-hint studio-error" role="alert">{{ profileError }} <button type="button" :disabled="profileLoading" @click="load">重新加载</button></p>

    <div ref="contentScroll" class="page-scroll" data-tour="profile">
    <header v-if="isStudio && page === 'center'" class="folio-head">
      <h1>微格训练成绩单</h1>
      <details><summary>考前说明</summary><p>核对考生信息后，到办公桌选课，在演绎厅完成训练。成绩栏汇总你的等级、徽章和最近评课。</p><button type="button" @click="startTour">查看操作指引</button></details>
    </header>
    <h1 v-if="isStudio && page === 'settings'" class="workshop-title">教室装修台</h1>
    <!-- 个人中心：身份、等级、徽章、最近训练 -->
    <div v-if="page === 'center'" class="profile-stack">
      <section class="identity-card">
        <header v-if="isStudio" class="studio-section-heading"><h2>考生信息</h2></header>
        <div class="identity-card__face">
          <b>{{ initial }}</b>
          <div>
            <h2>{{ form.name || '未填写姓名' }}</h2>
            <p>{{ roleLabel }} · {{ form.school || '未填写学校' }}</p>
          </div>
        </div>
        <form class="profile-grid" @submit.prevent="save">
          <label>姓名<input v-model="form.name" /></label>
          <label>
            角色
            <select v-model="form.role">
              <option value="student">师范生</option>
              <option value="teacher">指导教师</option>
            </select>
          </label>
          <label>学校<input v-model="form.school" /></label>
          <label>专业<input v-model="form.major" /></label>
          <label>年级<input v-model="form.grade" placeholder="如本科三年级" /></label>
          <label class="span-2">自我介绍<textarea v-model="form.bio" rows="4"></textarea></label>
          <button class="primary" type="submit" :disabled="saving || profileLoading || !!profileError">{{ saving ? '正在保存…' : '保存档案' }}</button>
          <p v-if="saved" class="dock-hint" role="status">档案已保存。</p>
          <p v-if="saveError" class="dock-hint" role="alert">{{ saveError }}</p>
        </form>
      </section>

      <section class="level-card">
        <h2 v-if="isStudio" class="profile-block-title">成绩栏</h2>
        <div class="level-card__meta">
          <strong>{{ profile.level_label || 'Lv.1 微格学员' }}</strong>
          <span>{{ profile.next_hint || '完成训练可提升等级' }}</span>
        </div>
        <div class="xp-bar" aria-label="经验进度">
          <i :style="{ width: `${profile.xp_percent || 0}%` }"></i>
        </div>
        <p class="dock-hint">经验 {{ profile.xp || 0 }} · 累计训练 {{ profile.session_count || 0 }} 次</p>
      </section>

      <section class="profile-badges">
        <h3 class="profile-block-title">徽章墙</h3>
        <div class="badge-grid">
          <article v-for="item in badges" :key="item.id" :class="{ earned: item.earned }">
            <StudioArt v-if="isStudio" kind="badge" :index="badgeArtIndex(item)" />
            <div class="badge-copy">
            <strong>{{ item.name }}</strong>
            <span>{{ item.hint }}</span>
            <b>{{ item.earned ? '已获得' : '未点亮' }}</b>
            </div>
          </article>
        </div>
        <p v-if="!badges.length" class="dock-hint">{{ profileLoading ? '正在整理成长记录…' : profileError ? '重新加载档案后查看徽章。' : '完成训练后，在这里查看获得的徽章。' }}</p>
      </section>

      <section class="profile-recent">
        <h3 class="profile-block-title">最近训练摘要</h3>
        <div v-if="recent.length" class="recent-list">
          <button
            v-for="item in recent"
            :key="item.id"
            type="button"
            class="recent-item"
            @click="openReview(item.id)"
          >
            <b>{{ item.overall_score }}</b>
            <div>
              <strong>{{ item.course_title || '微格训练' }}</strong>
              <p>{{ item.suggestion }}</p>
            </div>
          </button>
        </div>
        <p v-else class="profile-copy">暂无历史训练报告。<router-link to="/ai-review">查看模拟课堂评课 →</router-link></p>
      </section>
    </div>

    <!-- 设置：只做系统操作 -->
    <div v-else-if="page === 'settings'" class="settings-stack">
      <section class="settings-block appearance-settings">
        <h3>教室配色</h3>
        <p>随时切换，选择会保存在当前浏览器。</p>
        <ThemeSwitcher cards />
      </section>
      <section class="settings-block settings-guide">
        <h3>使用引导</h3>
        <button type="button" @click="startTour">重新查看新手引导</button>
        <p>摄像头、音量与字幕可在课堂内调整。</p>
        <router-link to="/classroom">前往模拟课堂 →</router-link>
      </section>

      <section class="settings-block settings-display">
        <h3>显示与评课</h3>
        <div class="settings-row">
          <span>问候语</span>
          <div class="mode-picks">
            <button type="button" :aria-pressed="settings.greetingLang === 'zh'" :class="{ active: settings.greetingLang === 'zh' }" @click="setSetting('greetingLang', 'zh')">中文</button>
            <button type="button" :aria-pressed="settings.greetingLang === 'en'" :class="{ active: settings.greetingLang === 'en' }" @click="setSetting('greetingLang', 'en')">英文</button>
            <button type="button" :aria-pressed="settings.greetingLang === 'both'" :class="{ active: settings.greetingLang === 'both' }" @click="setSetting('greetingLang', 'both')">中英都要</button>
          </div>
        </div>
      </section>

      <section class="settings-block settings-account">
        <h3>账号</h3>
        <dl class="account-dl">
          <div><dt>账号</dt><dd>{{ auth.user?.account || '—' }}</dd></div>
          <div><dt>姓名</dt><dd>{{ auth.user?.name || profile.name || '—' }}</dd></div>
          <div><dt>角色</dt><dd>{{ auth.user?.role_label || roleLabel }}</dd></div>
        </dl>
        <button type="button" @click="logout">退出登录</button>
      </section>

      <section class="settings-block settings-data">
        <h3>数据与偏好</h3>
        <p>偏好保存在当前浏览器。课堂数据的使用范围以授课前的授权说明为准。</p>
        <button type="button" @click="clearPrefs">清除本机偏好，恢复默认</button>
        <p v-if="prefsCleared" class="dock-hint">已恢复默认训练项与显示选项。</p>
        <p v-if="settingsError" class="dock-hint" role="alert">{{ settingsError }}</p>
      </section>
    </div>

    <!-- 联系我们 -->
    <div v-else class="contact-stack">

      <section v-if="supportEmail" class="contact-card contact-support">
        <h3>技术支持</h3>
        <ul class="contact-people">
          <li>
            <strong>技术支持</strong>
            <span>{{ supportEmail }}</span>
            <button type="button" class="ghost-link" @click="copyEmail">复制邮箱</button>
          </li>
        </ul>
        <p v-if="copied" class="dock-hint">邮箱已复制。</p>
        <p v-if="copyError" class="dock-hint" role="alert">{{ copyError }}</p>
      </section>


      <section v-if="isStudio" class="pinned-board" aria-label="我的留言板">
        <header><h1>留言板</h1><button ref="newNoteButton" type="button" :aria-expanded="writing" @click="openNote">＋ 写留言</button></header>
        <p v-if="notesError" role="alert">{{ notesError }} <button @click="readNotes">重试</button></p>
        <p v-if="messageOk" class="board-status" role="status">邮件已发送，留言已贴上。</p>
        <div class="board-notes">
          <form v-if="writing" class="pinned-paper note-editor" @submit.prevent="submitMessage">
            <select v-model="message.topic" aria-label="留言主题"><option v-for="topic in topics" :key="topic">{{ topic }}</option></select>
            <textarea ref="noteBody" v-model="message.body" maxlength="4000" aria-label="留言内容" rows="4" placeholder="写给项目团队的邮件…" required></textarea>
            <label>落款 <input v-model="message.name" aria-label="落款" placeholder="匿名"></label>
            <footer><button type="button" :disabled="messageSaving" @click="closeNote">收起</button><button type="submit" :disabled="messageSaving">{{ messageSaving ? '发送中…' : '发邮件并贴上' }}</button></footer>
            <p v-if="messageError" role="alert">{{ messageError }}</p>
          </form>
          <article v-for="note in notes" :key="note.id" class="pinned-paper"><small>{{ note.topic }}</small><p>{{ note.text }}</p><footer>{{ note.author }} · {{ note.date }}</footer></article>
        </div>
      </section>
      <section v-else class="contact-card contact-form">
        <h3>留言板</h3>
        <p class="dock-hint">留言会发送至项目邮箱，并保存到你的训练日志。</p>
        <form class="profile-grid" @submit.prevent="submitMessage">
          <label>姓名<input v-model="message.name" /></label>
          <label>
            主题
            <select v-model="message.topic">
              <option>训练故障</option>
              <option>评课异议</option>
              <option>课程资源</option>
              <option>其他</option>
            </select>
          </label>
          <label class="span-2">内容<textarea v-model="message.body" rows="5" placeholder="写清发生了什么、哪一次训练或哪份评课。"></textarea></label>
          <button class="primary" type="submit" :disabled="messageSaving">{{ messageSaving ? '发送中…' : '发送邮件' }}</button>
          <p v-if="messageOk" class="dock-hint" role="status">邮件已发送，留言已保存。</p>
          <p v-if="messageError" class="dock-hint" role="alert">{{ messageError }}</p>
        </form>
      </section>
    </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { startTour } from '../utils/onboarding.js'
import { sendBoardMessage, fetchJournals, fetchFeedbacks, fetchProfile, saveProfile } from '../services/dashboard'
import { useAuthStore } from '../stores/auth'
import { loadSettings, resetSettings, saveSettings } from '../utils/settings'
import { journalSubmitErrorMessage } from '../utils/dashboardState'
import ThemeSwitcher from '../components/ThemeSwitcher.vue'
import StudioArt from '../components/StudioArt.vue'
import { useUiVersion } from '../utils/uiVersion.js'
import { badgeArtIndex } from '../utils/studioPresentation.js'
const { isStudio } = useUiVersion()
const saving = ref(false)
const messageSaving = ref(false)
const profileLoading = ref(true)

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const contentScroll = ref(null)
const saved = ref(false)
const saveError = ref('')
const profileError = ref('')
const prefsCleared = ref(false)
const settingsError = ref('')
const copied = ref(false)
const copyError = ref('')
const messageOk = ref(false)
const messageError = ref('')
const configuredEmail = String(import.meta.env.VITE_SUPPORT_EMAIL || '').trim()
const supportEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(configuredEmail) ? configuredEmail : ''
const profile = ref({
  badges: [],
  recent_feedbacks: [],
  school: '',
  major: '',
  grade: '',
  bio: '',
  name: '',
  role: 'student',
  level_label: '',
  xp: 0,
  xp_percent: 0,
  session_count: 0,
  next_hint: '',
})
const form = reactive({ name: '', school: '', major: '', grade: '', bio: '', role: 'student' })
const settings = reactive(loadSettings())
const message = reactive({ name: '', topic: '训练故障', body: '' })
let pendingMail
const topics = ['训练故障','评课异议','课程资源','其他']
const writing = ref(false), notes = ref([]), notesError = ref('')
const noteBody = ref(null), newNoteButton = ref(null)
function openNote() {
  writing.value = true
  messageOk.value = false
  nextTick(() => noteBody.value?.focus())
}
function closeNote() {
  writing.value = false
  nextTick(() => newNoteButton.value?.focus())
}
async function readNotes() {
  notesError.value = ''
  try {
    notes.value = (await fetchJournals()).flatMap(item => {
      const match = /^\[留言\/([^\]]+)\] (.*?)：([\s\S]*)$/.exec(item.body)
      return match ? [{ id:item.id, topic:match[1], author:match[2], text:match[3], date:item.entry_date }] : []
    })
  } catch { notesError.value = '暂时无法读取墙上的留言。' }
}

const page = computed(() => {
  const tab = String(route.query.tab || '')
  if (tab === 'settings' || tab === 'contact') return tab
  return 'center'
})
const pageTitle = computed(() => ({
  center: '个人中心',
  settings: '设置',
  contact: '留言板',
}[page.value]))
watch(() => isStudio.value && page.value === 'contact', active => { if (active) readNotes() }, { immediate:true })
const initial = computed(() => (form.name || profile.value.name || '临').slice(0, 1))
const roleLabel = computed(() => (form.role === 'teacher' ? '指导教师' : '师范生'))
const badges = computed(() => profile.value.badges || [])
const recent = computed(() => profile.value.recent_feedbacks || [])

watch(() => route.query.tab, () => {
  nextTick(() => { if (contentScroll.value) contentScroll.value.scrollTop = 0 })
  saved.value = false
  saveError.value = ''
  profileError.value = ''
  prefsCleared.value = false
  settingsError.value = ''
  messageOk.value = false
  copied.value = false
  copyError.value = ''
  messageError.value = ''
})

onMounted(load)

async function load() {
  profileLoading.value = true
  try {
    profile.value = await fetchProfile()
    profileError.value = ''
  } catch (error) {
    profile.value = {
      name: auth.user?.name || '',
      role: auth.user?.role || 'student',
      school: '',
      major: '',
      grade: '',
      bio: '',
      level_label: '',
      xp: 0,
      xp_percent: 0,
      session_count: 0,
      next_hint: '',
      recent_feedbacks: [],
      badges: [],
    }
    profileError.value = error?.response?.data?.message || '个人资料加载失败，请检查服务后重试。'
  }
  form.name = profile.value.name || ''
  form.school = profile.value.school || ''
  form.major = profile.value.major || ''
  form.grade = profile.value.grade || ''
  form.bio = profile.value.bio || ''
  form.role = profile.value.role === 'teacher' ? 'teacher' : 'student'
  if (!profile.value.recent_feedbacks?.length) {
    try {
      const items = await fetchFeedbacks()
      profile.value.recent_feedbacks = (items || []).slice(0, 3).map((row) => ({
        id: row.id,
        overall_score: row.overall_score,
        suggestion: row.suggestion,
        course_title: row.course_title || '微格训练',
        created_at: row.created_at,
      }))
    } catch {
      /* 没有评课记录时保持空列表 */
    }
  }
  message.name = form.name
  profileLoading.value = false
}

async function save() {
  if (saving.value || profileLoading.value || profileError.value) return
  saving.value = true
  saved.value = false
  saveError.value = ''
  try {
    profile.value = await saveProfile({ ...form })
    auth.user = {
      ...auth.user,
      name: form.name,
      role: form.role,
      role_label: roleLabel.value,
      school: form.school,
      major: form.major,
    }
    saved.value = true
  } catch (error) {
    saveError.value = error?.response?.data?.message || '档案保存失败，请检查后端连接后重试。'
  } finally {
    saving.value = false
  }
}

function setSetting(key, value) {
  settings[key] = value
  persistSettings()
}

function persistSettings() {
  settingsError.value = ''
  try {
    saveSettings({ ...settings })
  } catch {
    settingsError.value = '设置保存失败，请检查浏览器存储权限后重试。'
  }
  prefsCleared.value = false
}

function clearPrefs() {
  settingsError.value = ''
  try {
    Object.assign(settings, resetSettings())
    prefsCleared.value = true
  } catch {
    settingsError.value = '设置清除失败，请检查浏览器存储权限后重试。'
  }
}

function logout() {
  auth.logout()
  router.push('/')
}

function openReview(id) {
  router.push({ path: '/ai-review', query: { feedbackId: id } })
}


async function copyEmail() {
  copied.value = false
  copyError.value = ''
  try {
    if (!navigator.clipboard?.writeText) throw new Error('clipboard unavailable')
    await navigator.clipboard.writeText(supportEmail)
    copied.value = true
  } catch {
    copyError.value = '邮箱复制失败，请手动选择邮箱地址。'
  }
}

async function submitMessage() {
  if (messageSaving.value) return
  messageOk.value = false
  messageError.value = ''
  const body = message.body.trim()
  if (!body) {
    messageError.value = '请填写留言内容。'
    return
  }
  const payload = { topic: message.topic, author: message.name || form.name || '匿名', body }
  const signature = JSON.stringify(payload)
  if (pendingMail?.signature !== signature) pendingMail = { signature, id: crypto.randomUUID() }
  messageSaving.value = true
  try {
    await sendBoardMessage({ ...payload, request_id: pendingMail.id })
    pendingMail = null
    message.body = ''
    messageOk.value = true
    if (isStudio.value) { closeNote(); await readNotes() }
  } catch (error) {
    messageError.value = journalSubmitErrorMessage(error)
  } finally {
    messageSaving.value = false
  }
}
</script>
