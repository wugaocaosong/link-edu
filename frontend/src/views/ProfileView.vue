<template>
  <div class="sparse-page profile-page" :class="`profile-page--${page}`">
<PaperTitle v-if="!isStudio" :text="pageTitle" />
    <p v-if="profileError" class="dock-hint studio-error" role="alert">{{ profileError }} <button type="button" :disabled="profileLoading" @click="load">重新加载</button></p>

    <div ref="contentScroll" class="page-scroll" data-tour="profile">
    <StudioBanner :title="bannerTitle" :subtitle="bannerSubtitle" :variant="page">
      <template v-if="page === 'center'" #portrait><b class="studio-identity-avatar">{{ initial }}</b></template>
      <span v-if="page === 'center'" class="studio-banner__note">在每一次练习中，记录自己的成长。</span>
    </StudioBanner>
    <!-- 个人中心：身份、等级、徽章、最近训练 -->
    <div v-if="page === 'center'" class="profile-stack">
      <section class="identity-card">
        <header v-if="isStudio" class="studio-section-heading"><h2>个人档案</h2><p>完善个人信息，记录你的教师成长之路。</p></header>
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
        <h3>界面风格</h3>
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
      <section class="contact-card contact-project">
        <h3>项目信息</h3>
        <dl class="account-dl">
          <div><dt>产品</dt><dd>临客 LINK · AI 微格教学训练平台</dd></div>
        </dl>
      </section>

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

      <section class="contact-card contact-shortcuts">
        <h3>快捷入口</h3>
        <div class="contact-actions">
          <button type="button" @click="openHelp('bot')">常见问题</button>
          <button type="button" @click="openHelp('human')">记录问题</button>
        </div>
      </section>

      <section class="contact-card contact-form">
        <h3>留言反馈</h3>
        <p class="dock-hint">留言保存到你的训练日志，不会发送给外部客服。</p>
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
          <p v-if="isStudio" class="dock-hint span-2">记录具体情况，便于下次回顾。</p>
          <button class="primary" type="submit" :disabled="messageSaving">{{ messageSaving ? '正在保存…' : '保存留言' }}</button>
          <p v-if="messageOk" class="dock-hint" role="status">留言已保存到训练日志。</p>
          <p v-if="messageError" class="dock-hint" role="alert">{{ messageError }}</p>
        </form>
      </section>
      <div v-if="isStudio" class="contact-still-life" aria-hidden="true"></div>
    </div>
    </div>
  </div>
</template>

<script setup>
import PaperTitle from '../components/PaperTitle.vue'
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { startTour } from '../utils/onboarding.js'
import { addJournal, fetchFeedbacks, fetchProfile, saveProfile } from '../services/dashboard'
import { useAuthStore } from '../stores/auth'
import { loadSettings, openHelpChat, resetSettings, saveSettings } from '../utils/settings'
import { journalSubmitErrorMessage } from '../utils/dashboardState'
import ThemeSwitcher from '../components/ThemeSwitcher.vue'
import StudioBanner from '../components/StudioBanner.vue'
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

const page = computed(() => {
  const tab = String(route.query.tab || '')
  if (tab === 'settings' || tab === 'contact') return tab
  return 'center'
})
const pageTitle = computed(() => ({
  center: '个人中心',
  settings: '设置',
  contact: '帮助与反馈',
}[page.value]))
const bannerTitle = computed(() => ({ center: form.name || '个人中心', settings: '把课堂，调成喜欢的样子', contact: '每一次记录，都让下一次更好' }[page.value]))
const bannerSubtitle = computed(() => page.value === 'center' ? `${roleLabel.value} · ${form.school || '完善你的个人档案'}` : page.value === 'settings' ? '随时调整，让练习更专注。' : '帮助与反馈')
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
  persistSettings({ [key]: value })
}

function persistSettings(partial) {
  settingsError.value = ''
  try {
    saveSettings(partial)
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

function openHelp(mode) {
  openHelpChat(mode)
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
  const text = `[留言/${message.topic}] ${message.name || form.name || '匿名'}：${body}`
  messageSaving.value = true
  try {
    await addJournal({ entry_date: new Date().toISOString().slice(0, 10), body: text })
    message.body = ''
    messageOk.value = true
  } catch (error) {
    messageError.value = journalSubmitErrorMessage(error)
  } finally {
    messageSaving.value = false
  }
}
</script>
