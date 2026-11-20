<template>
  <main v-ambient-ui="!isAcademy && !isStudio" class="dashboard app-shell" :class="{ immersive: immersive, 'sidebar-folded': sidebarFolded, 'protected-shell': protectedShell, 'studio-ui': isStudio, 'desk-fullscreen': isStudio && (['/courses','/dashboard','/growth'].includes(route.path) || archiveCoverPage) }">
    <a class="skip-content" href="#workspace-content">跳到页面内容</a>
    <AmbientVideo
      v-if="!immersive && !protectedShell && !isAcademy && !isStudio"
      class="app-shell-bg-video"
      source="/assets/login-bg-lite.mp4"
      fallback-source="/assets/login-bg.mp4"
      poster="/assets/login-bg.png"
      aria-hidden="true"
    />
    <div v-if="!immersive && !protectedShell && !isAcademy && !isStudio" class="app-shell-bg-shade" aria-hidden="true"></div>
    <Aurora v-if="!isAcademy && !isStudio" />
    <aside id="primary-sidebar" class="sidebar">
      <BrandMark home-link />
      <nav aria-label="主导航">
        <router-link
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="nav-link"
          :class="{ active: isActive(item.to) }"
          :aria-current="isActive(item.to) ? 'page' : undefined"
        ><svg class="academy-nav-icon shell-nav-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path :d="item.icon" /></svg><span>{{ item.label }}</span></router-link>
      </nav>
      <div class="side-bottom">
        <p v-if="isAcademy && !isStudio" class="academy-motto">先临课<br />再上课<small>把每一次练习，变成经验。</small></p>

        <button type="button" @click="logout">退出登录</button>
      </div>
    </aside>

    <section class="workspace" :class="{ 'workspace--immersive': immersive }">
      <button class="fold-nav" type="button" aria-controls="primary-sidebar" :aria-expanded="!sidebarFolded" :aria-label="sidebarFolded ? '展开导航' : '收起导航'" @click="sidebarFolded = !sidebarFolded">{{ sidebarFolded ? '☰' : '‹' }}</button>
      <header v-if="!immersive" class="topbar">
        <span class="page-crumb">{{ isStudio ? pageTitle : crumb }}</span>
        <select class="mobile-page-nav" aria-label="切换页面" :value="route.path" @change="router.push($event.target.value)">
          <option v-if="!nav.some(item => item.to === route.path)" :value="route.path" disabled>{{ crumb }}</option>
          <option v-for="item in nav" :key="item.to" :value="item.to">{{ item.label }}</option>
        </select>
        <form v-if="route.path !== '/courses' || !isStudio" class="cir-search" role="search" @submit.prevent="goSearch">
          <svg class="cir-search__icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="6.5" stroke="currentColor" stroke-width="1.8"/>
            <path d="M16.2 16.2L20 20" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
          </svg>
          <input
            v-model="search"
            class="cir-search__field"
            type="search"
            placeholder="搜索课程"
            aria-label="搜索课程"
          />
          <kbd class="cir-search__kbd">Enter</kbd>
        </form>
        <details ref="appearance" class="shell-appearance" @click.stop @keydown.esc.stop.prevent="closeAppearance">
          <summary><span aria-hidden="true">◐</span> 外观</summary>
          <div class="appearance-panel"><strong>界面外观</strong><ThemeSwitcher /><UiVersionSwitcher /></div>
        </details>
        <div class="profile" @keydown.esc.stop.prevent="closeProfile" @focusout="leaveProfile">
          <button
            ref="profileTrigger"
            class="profile-btn"
            type="button"
            aria-label="账户选项"
            aria-controls="profile-menu"
            :aria-expanded="menuOpen"
            @click.stop="menuOpen = !menuOpen"
          >
            <b>{{ profileInitial }}</b>
            <span>{{ displayName }} · {{ roleLabel }}</span>
            <em :class="{ open: menuOpen }">▾</em>
          </button>
          <div v-if="menuOpen" id="profile-menu" class="profile-menu" @click.stop>
            <button type="button" @click="goProfile('archive')">个人中心</button>
            <button type="button" @click="goProfile('settings')">设置</button>
            <button type="button" @click="goProfile('contact')">帮助与反馈</button>
            <button type="button" @click="menuOpen = false; productsOpen = true">谱联产品</button>
            <button class="mobile-logout" type="button" @click="logout">退出登录</button>
          </div>
        </div>
      </header>

      <div id="workspace-content" class="page-frame" tabindex="-1" :aria-label="pageTitle">
        <router-view v-slot="{ Component }">
          <transition name="page-sweep" :mode="enteringHallFromDesk ? undefined : 'out-in'" :css="!enteringHallFromDesk">
            <div class="page-slot" :key="route.path === '/classroom' ? route.path : route.fullPath">
              <component :is="Component" />
            </div>
          </transition>
        </router-view>
      </div>
    </section>

    <HelpChat />
    <NModal v-model:show="productsOpen" preset="card" title="谱联产品" :style="{width:'min(480px, calc(100vw - 32px))', maxHeight:'85dvh', overflowY:'auto'}">
      <ProductLinks current="link" />
    </NModal>
    <OnboardingTour />
  </main>
</template>

<script setup>
import { computed, onMounted, onUnmounted, provide, shallowRef, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { NModal } from 'naive-ui'
import ProductLinks from '../components/products/ProductLinks.vue'
const productsOpen = ref(false)
import BrandMark from '../components/BrandMark.vue'
import HelpChat from '../components/HelpChat.vue'
import OnboardingTour from '../components/OnboardingTour.vue'
import Aurora from '../components/fx/Aurora.vue'
import AmbientVideo from '../components/fx/AmbientVideo.vue'
import ThemeSwitcher from '../components/ThemeSwitcher.vue'
import UiVersionSwitcher from '../components/UiVersionSwitcher.vue'
import { useUiVersion } from '../utils/uiVersion.js'
import { useUiTheme } from '../utils/uiTheme.js'
import { ambientUi as vAmbientUi } from '../utils/ambientUi.js'
import { useAuthStore } from '../stores/auth'
import { buildSearchLocation } from '../utils/navigation'
import { classroomHelpKey } from '../utils/classroomHelpContext.js'

const route = useRoute()
const { isStudio } = useUiVersion()
const { isAcademy } = useUiTheme()
const router = useRouter()
const auth = useAuthStore()
provide(classroomHelpKey, shallowRef(null))
const search = ref('')
const sidebarFolded = ref(false)
const enteringHallFromDesk = ref(false)
watch(() => route.path, (to, from) => {
  enteringHallFromDesk.value = from === '/courses' && to === '/classroom'
}, { flush: 'sync' })
const menuOpen = ref(false)
const appearance = ref(null)
const profileTrigger = ref(null)

const nav = [
  ...(import.meta.env.VITE_ADAPTIVE_ENABLED === 'true' ? [{ label: '自适应学习', to: '/adaptive', icon: 'M4 19V5h16v14H4zm4-9h8M8 14h5' }] : []),
  { label: '标签墙', to: '/dashboard', icon: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z' },
  { label: '办公桌', to: '/courses', icon: 'M12 5C9 3 6 3 3 4v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1zm0 0v15' },
  { label: '演绎厅', to: '/classroom', icon: 'M3 3h18v15H3zM10 7l5 3.5-5 3.5zM8 21h8m-4-3v3' },
  { label: '档案袋', to: '/ai-review', icon: 'M4 3v17h17M9 15V9m5 6V5m5 10v-5' },
  { label: '小书架', to: '/resources', icon: 'M12 3l9 5-9 5-9-5zM3 12l9 5 9-5M3 16l9 5 9-5' },
]

const crumb = computed(() => {
  if (route.path === '/profile') {
    if (route.query.tab === 'settings') return '设置'
    if (route.query.tab === 'contact') return '帮助与反馈'
    return '个人中心'
  }
  return route.meta.crumb || '工作台  /  总览'
})
const pageTitle = computed(() => nav.find(item => isActive(item.to))?.label || crumb.value)
const immersive = computed(() => Boolean(route.meta.immersive))
const archiveCoverPage = computed(() => route.path === '/ai-review' && !Object.keys(route.query).length)
// Keep console shell chrome (sidebar / workspace) consistent on every authenticated page.
const protectedShell = computed(() => false)
const displayName = computed(() => auth.user?.name || '临客')
const roleLabel = computed(() => auth.user?.role_label || '师范生')
const profileInitial = computed(() => displayName.value.slice(0, 1))

function isActive(path) {
  return route.path === path || route.path.startsWith(`${path}/`) || (path === '/resources' && route.path === '/knowledge')
}

function goSearch() {
  router.push(buildSearchLocation(search.value))
}

function goProfile(tab) {
  menuOpen.value = false
  router.push({ path: '/profile', query: tab === 'archive' ? {} : { tab } })
}

function logout() {
  auth.logout()
  router.push('/')
}

function closeMenu() {
  menuOpen.value = false
  if (appearance.value) appearance.value.open = false
}

function closeAppearance() {
  if (appearance.value) appearance.value.open = false
  appearance.value?.querySelector('summary')?.focus()
}

function closeProfile() {
  menuOpen.value = false
  profileTrigger.value?.focus()
}

function leaveProfile(event) {
  if (!event.currentTarget.contains(event.relatedTarget)) menuOpen.value = false
}

watch(() => route.fullPath, closeMenu)

watch(() => route.query.q, (value) => {
  search.value = String(value || '')
}, { immediate: true })

onMounted(() => {
  auth.hydrate()
  window.addEventListener('click', closeMenu)
})

onUnmounted(() => {
  window.removeEventListener('click', closeMenu)
})
</script>

<style>
.fold-nav {display:none}
@media(min-width:801px){
 .app-shell .workspace{position:relative}
 .app-shell .fold-nav{position:absolute;z-index:12;display:grid;place-items:center;left:2px;top:22%;width:26px;height:40px;border:1px solid #b99163;border-radius:0 12px 12px 0;background:#392a21e6;color:#fff1cf;font:700 20px/1 system-ui;cursor:pointer}
 html[data-ui-theme] .app-shell.sidebar-folded{grid-template-columns:minmax(0,1fr)!important}
 html[data-ui-theme] .app-shell.sidebar-folded .sidebar{display:none!important}
 html[data-ui-theme] .app-shell.sidebar-folded .workspace{grid-column:1/-1;width:100%;margin-left:0}
 html[data-ui-theme] .app-shell.studio-ui.desk-fullscreen:not(.protected-shell) .workspace{position:relative;padding:0!important}
 html[data-ui-theme] .app-shell.studio-ui.desk-fullscreen:not(.protected-shell) .topbar{position:absolute;inset:8px 12px auto auto;z-index:8;width:auto;background:transparent!important}
 html[data-ui-theme] .app-shell.desk-fullscreen .page-frame,html[data-ui-theme] .app-shell.desk-fullscreen .page-slot{height:100%!important;padding:0;border-radius:0}
 html[data-ui-theme] .app-shell.studio-ui.desk-fullscreen .desk-page__tools{position:absolute;left:12px;top:8px}
 html[data-ui-theme] .app-shell.desk-fullscreen .desk-heading{display:none}
 html[data-ui-theme] .app-shell.studio-ui.desk-fullscreen .course-desk{height:100%;border:none;border-radius:0}
}
/* Use the same workspace bounds through the last frame of the tablet zoom. */
html[data-ui-theme] .app-shell.studio-ui:not(.protected-shell):has(.hall-entry) .workspace {
  position: relative;
  padding: 0 !important;
}
html[data-ui-theme] .app-shell.studio-ui:not(.protected-shell):has(.hall-entry) .topbar {
  position: absolute;
  inset: 8px 12px auto auto;
  width: auto;
  z-index: 8;
  margin: 0;
  background: transparent;
}
html[data-ui-theme] .app-shell.studio-ui:has(.hall-entry) :is(.page-frame,.page-slot) {
  position: relative;
  height: 100%;
  overflow: hidden;
  padding: 0;
  border-radius: 0;
}
.desk-to-hall .page-frame{view-transition-name:lesson-scene}
.desk-to-hall .page-sweep-enter-active,.desk-to-hall .page-sweep-leave-active,.desk-to-hall .hall-scene{animation:none!important}
::view-transition-old(lesson-scene){animation:desk-lower .7s ease-in-out both}
::view-transition-new(lesson-scene){animation:tablet-rise .7s ease-in-out both}
@keyframes desk-lower{to{transform:translateY(-17%) scale(1.07);opacity:0}}
@keyframes tablet-rise{from{transform:translateY(17%) scale(.97);opacity:0}}
html[data-ui-theme] .app-shell.studio-ui.desk-fullscreen:has(.tag-wall) .workspace {position:relative;padding:0!important;height:100dvh}
html[data-ui-theme] .app-shell.studio-ui.desk-fullscreen:has(.tag-wall) .topbar {position:absolute;inset:6px 10px auto auto;width:auto;max-width:100%;padding:0;min-height:0;margin:0;background:transparent;z-index:8}
.app-shell:has(.tag-wall) .topbar :is(.page-crumb,.cir-search){display:none}
html[data-ui-theme] .app-shell.studio-ui.desk-fullscreen .page-dashboard:has(.tag-wall) {height:100%!important;padding:0;overflow:hidden}
</style>
