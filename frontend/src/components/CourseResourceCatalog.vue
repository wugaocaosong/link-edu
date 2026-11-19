<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import ClassroomDialog from './ClassroomDialog.vue'
import StudioArt from './StudioArt.vue'
import { useUiVersion } from '../utils/uiVersion.js'
import { matchesResource, resourceCoverIndex } from '../utils/studioPresentation.js'
import { fetchResources } from '../services/dashboard'
import { resolveResourceLink } from '../utils/resourceLinks.js'

const props = defineProps({ query: { type: String, default: '' } })
const emit = defineEmits(['count'])
const { isStudio } = useUiVersion()
const items = ref([])
const page = ref(1)
const pageSize = 6
const tab = ref('全部')
const detail = ref(null)
const loading = ref(true)
const resourceError = ref('')
const tabs = ['全部', '教案', '素材', '报告', '档案']
const visible = computed(() => items.value.filter(item => (tab.value === '全部' || item.category === tab.value) && matchesResource(item, props.query)))
const pageCount = computed(() => Math.max(1, Math.ceil(visible.value.length / pageSize)))
const pageItems = computed(() => isStudio.value ? visible.value.slice((page.value - 1) * pageSize, page.value * pageSize) : visible.value)
watch([tab, () => props.query], () => { page.value = 1 })
const link = computed(() => resolveResourceLink(detail.value?.file_url, window.location.origin))
const detailOpen = computed({ get: () => Boolean(detail.value), set: value => { if (!value) detail.value = null } })

async function loadResources() {
  loading.value = true
  resourceError.value = ''
  detail.value = null
  try {
    items.value = await fetchResources()
    emit('count', items.value.length)
  } catch (error) {
    items.value = []
    emit('count', null)
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
    <p v-else-if="!visible.length" class="course-search-feedback" role="status">{{ query ? '没有找到匹配资料，试试其他关键词或分类。' : '当前分类暂无资源。' }}</p>
    <ul v-else class="resource-list">
      <li v-for="item in pageItems" :key="item.id" class="glare-row studio-resource-card">
        <StudioArt v-if="isStudio" :index="resourceCoverIndex(item)" />
        <div class="studio-resource-card__body"><em>{{ item.category }}</em><strong>{{ item.title }}</strong><span>{{ item.description }}</span><button v-if="isStudio" type="button" class="studio-outline" :aria-label="`查看资料：${item.title}`" @click="detail = item">查看资料 <span aria-hidden="true">›</span></button></div>
        <button v-if="!isStudio" type="button" @click="detail = item">查看详情</button>
      </li>
    </ul>
    <nav v-if="isStudio && visible.length && !loading && !resourceError" class="studio-pagination" aria-label="课程资源分页">
      <span>显示 {{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, visible.length) }} 项，共 {{ visible.length }} 项</span>
      <div><button type="button" :disabled="page === 1" aria-label="上一页" @click="page--">‹</button><button v-for="number in pageCount" :key="number" type="button" :aria-current="page === number ? 'page' : undefined" @click="page = number">{{ number }}</button><button type="button" :disabled="page === pageCount" aria-label="下一页" @click="page++">›</button></div>
    </nav>
    <ClassroomDialog v-model="detailOpen" title="资源详情">
      <template v-if="detail">
        <p>{{ detail.category }}</p>
        <h2>{{ detail.title }}</h2>
        <p>{{ detail.description || '暂无详细说明。' }}</p>
        <p v-if="link.status === 'missing'" role="status">当前资源没有可用文件链接。</p>
        <p v-else-if="link.status === 'invalid'" role="alert">文件链接无效，请联系管理员更新。</p>
        <div v-else class="resource-actions">
          <a :href="link.url" target="_blank" rel="noopener noreferrer">{{ link.external ? '访问来源网站' : '打开文件' }}</a>
          <a v-if="!link.external" :href="link.url" download>下载文件</a>
        </div>
      </template>
    </ClassroomDialog>
  </section>
</template>

<style scoped>
.course-resource-catalog { min-width:0; }
.resource-tabs { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:18px; }
.resource-tabs button { padding:8px 18px; border:1px solid var(--line); border-radius:99px; }
.resource-tabs button.active { color:#ffd1ad; background:#ff7a181a; border-color:#ff974859; }
.resource-actions { display:flex; gap:16px; margin-top:20px; }
.resource-actions a { color:#ffd1ad; padding:10px 16px; border:1px solid #ff974859; border-radius:10px; }
.resource-list li>div { min-width:0; overflow-wrap:anywhere; }
</style>
