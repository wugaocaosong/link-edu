<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import ClassroomDialog from './ClassroomDialog.vue'
import MarkdownReader from './MarkdownReader.vue'
import { fetchResources } from '../services/dashboard'
import { resolveResourceLink } from '../utils/resourceLinks.js'

const items = ref([])
const tab = ref('全部')
const detail = ref(null)
const loading = ref(true)
const resourceError = ref('')
const tabs = ['全部', '教案', '素材', '报告', '档案']
const visible = computed(() => tab.value === '全部' ? items.value : items.value.filter(item => item.category === tab.value))
const link = computed(() => resolveResourceLink(detail.value?.file_url, window.location.origin))
const detailOpen = computed({ get: () => Boolean(detail.value), set: value => { if (!value) detail.value = null } })

// 本地 Markdown 直接在弹窗内渲染：新标签页打开裸文件会被浏览器按 GBK 猜编码，中文全变乱码
const isLocalMarkdown = computed(() => {
  if (!detail.value) return false
  try {
    const url = new URL(detail.value.file_url, window.location.origin)
    return url.origin === window.location.origin && /\.md$/i.test(url.pathname)
  } catch {
    return false
  }
})
const markdown = ref('')
const markdownError = ref('')
const markdownLoading = ref(false)

async function loadMarkdown() {
  markdown.value = ''
  markdownError.value = ''
  if (!isLocalMarkdown.value) return
  markdownLoading.value = true
  try {
    const response = await fetch(link.value.url)
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    markdown.value = await response.text()
  } catch {
    markdownError.value = '内容暂时无法加载，可用「下载文件」获取原件查看。'
  } finally {
    markdownLoading.value = false
  }
}
watch(detail, loadMarkdown)

async function loadResources() {
  loading.value = true
  resourceError.value = ''
  detail.value = null
  try {
    items.value = await fetchResources()
  } catch (error) {
    items.value = []
    resourceError.value = error?.response?.data?.message || '资源加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}
onMounted(loadResources)
</script>

<template>
  <section class="course-resource-catalog" aria-label="课程资源">
    <div class="resource-tabs" aria-label="资源分类">
      <button v-for="item in tabs" :key="item" type="button" :aria-pressed="tab === item" :class="{ active: tab === item }" @click="tab = item">{{ item }}</button>
    </div>
    <p v-if="loading" class="course-search-feedback" role="status">正在加载资源…</p>
    <div v-else-if="resourceError" class="course-search-feedback" role="alert">
      <span>{{ resourceError }}</span>
      <button type="button" class="text-action" @click="loadResources">重新加载资源</button>
    </div>
    <p v-else-if="!visible.length" class="course-search-feedback" role="status">当前分类暂无资源。</p>
    <ul v-else class="resource-list">
      <li v-for="item in visible" :key="item.id" class="glare-row">
        <div><em>{{ item.category }}</em><strong>{{ item.title }}</strong><span>{{ item.description }}</span></div>
        <button type="button" @click="detail = item">查看详情</button>
      </li>
    </ul>
    <ClassroomDialog v-model="detailOpen" title="资源详情">
      <template v-if="detail">
        <p>{{ detail.category }}</p>
        <h2>{{ detail.title }}</h2>
        <p>{{ detail.description || '暂无详细说明。' }}</p>
        <p v-if="link.status === 'missing'" role="status">当前资源没有可用文件链接。</p>
        <p v-else-if="link.status === 'invalid'" role="alert">文件链接无效，请联系管理员更新。</p>
        <template v-else-if="isLocalMarkdown">
          <p v-if="markdownLoading" class="course-search-feedback" role="status">正在加载内容…</p>
          <p v-else-if="markdownError" class="course-search-feedback" role="alert">{{ markdownError }}</p>
          <div v-else class="resource-md-preview">
            <MarkdownReader :content="markdown" />
          </div>
          <div class="resource-actions">
            <a :href="link.url" download>下载文件</a>
          </div>
        </template>
        <div v-else class="resource-actions">
          <a :href="link.url" target="_blank" rel="noopener noreferrer">{{ link.external ? '访问来源网站' : '打开文件' }}</a>
          <a v-if="!link.external" :href="link.url" download>下载文件</a>
        </div>
      </template>
    </ClassroomDialog>
  </section>
</template>

<style scoped>
/* 自包含浅色纸卡：课程资源 tab 的文字必须压在浅底深字上，
   不依赖全局 styles.css，避免 workspace 背景调暗后浅字糊成一片。 */
.course-resource-catalog {
  min-width: 0;
  color: #3d4438;
}

/* 分类 tab：未选中米白胶囊+深棕字，选中橙色纸片 */
.course-resource-catalog .resource-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
  padding: 0;
  border: 0;
}
.course-resource-catalog .resource-tabs button {
  padding: 8px 18px;
  border: 1px solid #d8c19c;
  border-radius: 999px;
  background: #f7f0df;
  color: #5c4a30;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background .18s ease, border-color .18s ease, color .18s ease, box-shadow .18s ease;
}
.course-resource-catalog .resource-tabs button:hover {
  background: #fff6e2;
  border-color: #c99a52;
  color: #46331c;
}
.course-resource-catalog .resource-tabs button.active,
.course-resource-catalog .resource-tabs button[aria-pressed="true"] {
  border-color: #e0a24f;
  background: linear-gradient(160deg, #ffd992, #eab063);
  color: #422913;
  box-shadow: 0 2px 0 #b07c3f, 0 4px 10px #3a2a1240;
}

/* 加载 / 错误提示 */
.course-resource-catalog .course-search-feedback {
  min-height: 120px;
  padding: 20px 22px;
  border: 1px dashed #b9a67f;
  border-radius: 14px;
  background: rgba(253, 250, 242, .94);
  color: #5c5340;
}
.course-resource-catalog .course-search-feedback .text-action {
  color: #9a5a16;
  font-weight: 700;
}

/* 清单：不透明浅色卡片底，深字 */
.course-resource-catalog .resource-list {
  list-style: none;
  margin: 0;
  padding: 6px;
  border: 1px solid #c9b590;
  border-radius: 16px;
  background: #fdfaf2;
  box-shadow: 0 12px 30px #1f2a1540;
}
.course-resource-catalog .resource-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 16px;
  border-radius: 11px;
  border-bottom: 1px solid #e4d9c2;
  color: #3d4438;
}
.course-resource-catalog .resource-list li:last-child { border-bottom: 0; }
.course-resource-catalog .resource-list li:hover { background: #f6efdc; }
.course-resource-catalog .resource-list li > div { min-width: 0; overflow-wrap: anywhere; }
.course-resource-catalog .resource-list em {
  display: inline-block;
  margin-bottom: 4px;
  padding: 2px 8px;
  border-radius: 6px;
  background: #e7ddc6;
  color: #7a5b30;
  font-size: 11px;
  font-style: normal;
  font-weight: 700;
  letter-spacing: .06em;
}
.course-resource-catalog .resource-list strong {
  display: block;
  color: #2f3829;
  font-size: 15px;
  line-height: 1.45;
}
.course-resource-catalog .resource-list span {
  display: block;
  margin-top: 3px;
  color: #5d6555;
  font-size: 12.5px;
  line-height: 1.55;
}
/* 查看详情按钮：橙黄胶囊+深棕字，杜绝白底白字空白块 */
.course-resource-catalog .resource-list li > button {
  flex: 0 0 auto;
  padding: 8px 15px;
  border: 1px solid #c99a52;
  border-radius: 9px;
  background: linear-gradient(#fff0cf, #e8c88e);
  color: #4a3317;
  font-size: 12.5px;
  font-weight: 700;
  cursor: pointer;
  transition: background .18s ease, transform .18s ease;
}
.course-resource-catalog .resource-list li > button:hover { background: #fff2d2; transform: translateY(-1px); }
.course-resource-catalog .resource-list li > button:active { transform: translateY(0); }

/* 详情弹窗也铺浅底深字 */
.course-resource-catalog :deep(.classroom-dialog) {
  width: min(780px, calc(100vw - 32px));
  background: #fdfaf2;
  color: #3d4438;
}
.course-resource-catalog :deep(.classroom-dialog h2) { color: #2f3829; }
.course-resource-catalog :deep(.classroom-dialog p) { color: #5d6555; }
.course-resource-catalog .resource-actions { display: flex; gap: 16px; margin-top: 20px; }
.course-resource-catalog .resource-actions a {
  color: #4a3317;
  padding: 10px 16px;
  border: 1px solid #c99a52;
  border-radius: 10px;
  background: linear-gradient(#fff0cf, #e8c88e);
  font-weight: 700;
}
.course-resource-catalog .resource-md-preview {
  margin: 12px -20px 0;
  border-top: 1px solid #e4d9c2;
  max-height: 52dvh;
  overflow: auto;
  overscroll-behavior: contain;
}
.course-resource-catalog .resource-md-preview :deep(.markdown-reader) { padding: 18px 20px 28px; color: #3d4438; }
.course-resource-catalog .resource-md-preview :deep(h1) { font-size: 22px; margin-bottom: 14px; }
.course-resource-catalog .resource-md-preview :deep(h2) { margin: 22px 0 10px; font-size: 17px; }
.course-resource-catalog .resource-md-preview :deep(h3) { margin: 18px 0 8px; }

@media (max-width: 620px) {
  .course-resource-catalog .resource-list li { flex-direction: column; align-items: stretch; gap: 10px; }
  .course-resource-catalog .resource-list li > button { align-self: flex-start; }
}
</style>
