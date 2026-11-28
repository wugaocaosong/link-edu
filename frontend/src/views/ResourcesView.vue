<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import DraggableResourceCard from "../components/DraggableResourceCard.vue";
import MarkdownReader from "../components/MarkdownReader.vue";
import CourseResourceCatalog from "../components/CourseResourceCatalog.vue";
import { libraryResources } from "../data/libraryResources";
import { SCENE_OPTIONS, MODULE_OPTIONS, LENGTH_OPTIONS, sceneOf, moduleOf, lengthOf } from "../data/libraryFacets";

const route = useRoute();
const query = ref(typeof route.query.q === "string" ? route.query.q.slice(0, 200) : "");
const collection = ref('library');
const activeCard = ref(libraryResources[0].id);
const selected = ref(null);
const markdown = ref("");
const loading = ref(false);
const loadError = ref("");
const videoError = ref(false);
const videoRetry = ref(0);
const videoSrc = computed(() => {
  const url = selected.value?.readUrl || "";
  return videoRetry.value ? `${url}${url.includes("?") ? "&" : "?"}retry=${videoRetry.value}` : url;
});
function handleVideoError() {
  if (videoRetry.value < 1) {
    videoRetry.value += 1;
    return;
  }
  videoError.value = true;
}
const layoutKey = ref(0);
const readerRef = ref(null);
let readerTrigger = null;
let requestId = 0;

const sceneTone = {
  备课: "topic",
  试讲与答辩: "review",
  课例观摩: "case",
  备考与官方资料: "official",
};

const DECK_SLOTS = [
  { left: 18, bottom: 46, rotate: 0, surface: 'envelope' },
  { left: 38.5, bottom: 45, rotate: 0, surface: 'linen' },
  { left: 59, bottom: 43.5, rotate: 0, surface: 'binder' },
  { left: 20, bottom: 6, rotate: 0, surface: 'folio' },
  { left: 67, bottom: 4, rotate: 1, surface: 'folder' },
];
const DECK_PAGE_SIZE = DECK_SLOTS.length;
const deckPage = ref(0);

function deckSlot(index) {
  const slot = index % DECK_PAGE_SIZE;
  return {
    ...DECK_SLOTS[slot],
    z: 4 + slot,
  };
}

/**
 * 画布每页 4 张并排，条目多的时候左右翻页。
 * 「全部」直接列出所有条目（靠翻页看完），单分类列本分类全部。
 */
/** 关键词搜索：跨分类匹配标题/分类/简介/来源/学段/格式等字段，空格分词做 AND。 */
const searchTerms = computed(() =>
  query.value.trim().toLowerCase().split(/\s+/).filter(Boolean),
);
const searchActive = computed(() => searchTerms.value.length > 0);

function searchableText(item) {
  return [
    item.title, item.category, item.description, item.source, item.stage,
    item.format, item.coverLabel, item.coverTitle, item.downloadName, item.year,
  ].filter(Boolean).join(" ").toLowerCase();
}

const matched = computed(() => {
  const terms = searchTerms.value;
  if (!terms.length) return libraryResources;
  return libraryResources.filter((item) => {
    const text = searchableText(item);
    return terms.every((term) => text.includes(term));
  });
});

/** 三个筛选维度：主题 × 模块 × 体量，可任意组合；空字符串 = 该维度的「全部」 */
const filterValues = ref({ theme: "", module: "", length: "" });
const openMenu = ref("");

const FILTER_DEFS = [
  { key: "theme", label: "主题", options: SCENE_OPTIONS, of: sceneOf },
  { key: "module", label: "模块", options: MODULE_OPTIONS, of: moduleOf },
  { key: "length", label: "体量", options: LENGTH_OPTIONS, of: lengthOf },
];

const filtered = computed(() => {
  const { theme, module, length } = filterValues.value;
  return matched.value.filter((item) =>
    (!theme || sceneOf(item) === theme)
    && (!module || moduleOf(item) === module)
    && (!length || lengthOf(item) === length)
  );
});

const filterActive = computed(() =>
  Boolean(filterValues.value.theme || filterValues.value.module || filterValues.value.length)
);

/** 卡片 key 与空状态文案用它 */
const filterKey = computed(() =>
  [filterValues.value.theme, filterValues.value.module, filterValues.value.length].join("|")
);
const activeFilterLabel = computed(() =>
  FILTER_DEFS.map((def) => filterValues.value[def.key]).filter(Boolean).join(" · ")
);

/** 每个维度里各选项的资源计数（菜单右侧的小数字） */
const facetCounts = computed(() => {
  const counts = { theme: {}, module: {}, length: {} };
  libraryResources.forEach((item) => {
    FILTER_DEFS.forEach((def) => {
      const key = def.of(item);
      counts[def.key][key] = (counts[def.key][key] || 0) + 1;
    });
  });
  return counts;
});

function pickFilter(dimension, value) {
  filterValues.value[dimension] = value;
  openMenu.value = "";
}

function clearFilters() {
  filterValues.value = { theme: "", module: "", length: "" };
}

/** 点外面 / Tab 走出菜单时收起 */
function onSceneBlur(event, dimension) {
  if (!event.currentTarget.contains(event.relatedTarget) && openMenu.value === dimension) {
    openMenu.value = "";
  }
}

/** 设计图里的 5 个精选原型置顶，保证第一页的文案与 5 种物件一一对应 */
const FEATURED_IDS = [
  'ntce-primary', 'ntce-secondary', 'ntce-kindergarten', 'info-knowledge', 'info-misconceptions',
];
const deckItems = computed(() => {
  const items = filtered.value;
  const featured = FEATURED_IDS.map((id) => items.find((item) => item.id === id)).filter(Boolean);
  const rest = items.filter((item) => !FEATURED_IDS.includes(item.id));
  return [...featured, ...rest];
});

const deckPageCount = computed(() => Math.max(1, Math.ceil(deckItems.value.length / DECK_PAGE_SIZE)));

const visible = computed(() =>
  deckItems.value
    .slice(deckPage.value * DECK_PAGE_SIZE, deckPage.value * DECK_PAGE_SIZE + DECK_PAGE_SIZE)
    .map((item, index) => ({ ...item, position: deckSlot(index) })),
);

const canPrevPage = computed(() => deckPage.value > 0);
const canNextPage = computed(() => deckPage.value < deckPageCount.value - 1);

function goPrevPage() {
  if (canPrevPage.value) deckPage.value -= 1;
}

function goNextPage() {
  if (canNextPage.value) deckPage.value += 1;
}

watch([filterKey, query], () => {
  deckPage.value = 0;
  listPage.value = 0;
});

watch(deckPageCount, (count) => {
  if (deckPage.value > count - 1) deckPage.value = count - 1;
});

/** 清单视图：一页 20 行，翻完所有条目 */
const LIST_PAGE_SIZE = 20;
const viewMode = ref("deck");
const listPage = ref(0);

const listPageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / LIST_PAGE_SIZE)));

const listItems = computed(() =>
  filtered.value.slice(listPage.value * LIST_PAGE_SIZE, listPage.value * LIST_PAGE_SIZE + LIST_PAGE_SIZE),
);

const canPrevList = computed(() => listPage.value > 0);
const canNextList = computed(() => listPage.value < listPageCount.value - 1);

const shelfScroll = ref(null);
const previewBoard = ref(null);
const previewBelow = ref(false);
watch(previewBoard, (board, _, cleanup) => {
  previewBelow.value = false;
  if (!board || !shelfScroll.value) return;
  const observer = new IntersectionObserver(([entry]) => {
    previewBelow.value = !entry.isIntersecting && entry.boundingClientRect.top >= (entry.rootBounds?.bottom ?? 0);
  }, { root: shelfScroll.value, rootMargin: '0px 0px -56px 0px' });
  observer.observe(board);
  cleanup(() => observer.disconnect());
}, { flush: 'post' });
function revealPreview() {
  previewBoard.value?.scrollIntoView({ block:'start', behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
  previewBoard.value?.focus({ preventScroll:true });
}

function switchView(mode) {
  viewMode.value = mode;
  listPage.value = 0;
  deckPage.value = 0;
}

function rowMeta(item) {
  const size = item.sheetCover?.footer || "";
  return [item.category, item.format, size].filter(Boolean).join(" · ");
}


/** 空分类不隐藏：留着位置，写清楚为什么还空着、要什么样的素材。 */
const emptySceneNotes = {
  备课: {
    title: "这一类还想再补",
    text: "现有《数据、信息与知识》课题包与图示素材。想要更多学科、更多课题的备课稿，等拿到真正能用的再加。",
  },
  试讲与答辩: {
    title: "这一类还想再补",
    text: "现有逐字稿、结构化六大类与成套题库。想要更多分题型的完整稿子和题库，等整理出可靠版本再加。",
  },
  课例观摩: {
    title: "这一类还想再补",
    text: "已有初中数学、高中信息课例与全真模拟。想要更多学科、更多学段的示范课例，等拿到真正能用的再加。",
  },
  备考与官方资料: {
    title: "这一类还想再补",
    text: "现有考前清单、官方大纲、评课维度与外部资源索引。等有权威新版文件再补。",
  },
};

const DEFAULT_EMPTY_NOTE = {
  title: "这一类暂时空着",
  text: "还没收录资料。等拿到真正能用、来源写清楚的材料再放进来。",
};

function emptyNoteFor(sceneName) {
  return emptySceneNotes[sceneName] || DEFAULT_EMPTY_NOTE;
}

const resultCount = computed(() => filtered.value.length);
const resultLabel = computed(() => {
  if (searchActive.value) return `找到 ${resultCount.value} 份`;
  if (filterActive.value) return `${resultCount.value} / ${libraryResources.length} 份`;
  return `${libraryResources.length} 份资料`;
});

const boardColumns = computed(() => {
  const order = filterValues.value.theme ? [filterValues.value.theme] : SCENE_OPTIONS;
  const items = filtered.value;
  return order
    .map((sceneName) => ({
      scene: sceneName,
      tone: sceneTone[sceneName] || "topic",
      items: items.filter((item) => sceneOf(item) === sceneName),
    }))
    // 搜索中只列出命中的分类，不摆一堆「0 份」占位卡
    .filter((column) => !searchActive.value || column.items.length > 0);
});

/** 有条目的分类排卡片，没有的排一张说明卡（保持分类顺序，不空着也不藏起来）。 */
const boardTiles = computed(() =>
  boardColumns.value.flatMap((column) => {
    if (column.items.length) {
      return column.items.map((item) => ({ ...item, tone: column.tone, placeholder: false }));
    }
    const note = emptyNoteFor(column.scene);
    return [{
      id: `empty-${column.scene}`,
      placeholder: true,
      category: column.scene,
      tone: column.tone,
      title: note.title,
      text: note.text,
    }];
  }),
);

const deckEmptyNote = computed(() => {
  if (filtered.value.length) return null;
  if (searchActive.value) {
    return {
      title: `没找到和「${query.value.trim()}」相关的资料`,
      text: "换个关键词试试，比如「试讲」「说课」「评价」「数据」。也可以用下方的分类筛选。",
    };
  }
  if (filterActive.value) {
    return {
      title: `「${activeFilterLabel.value}」暂时没有资料`,
      text: "这个组合还没凑齐。换个维度试试，或点「清空筛选」看全部。",
    };
  }
  return DEFAULT_EMPTY_NOTE;
});

function metaLabel(item) {
  if (item.pages) return `${item.format} · ${item.pages} 页`;
  if (item.duration) return `${item.format} · ${item.duration}`;
  return item.format || "点击阅读";
}

async function open(item) {
  readerTrigger = document.activeElement;
  selected.value = item;
  markdown.value = "";
  loadError.value = "";
  videoError.value = false;
  videoRetry.value = 0;
  const currentRequest = ++requestId;
  await nextTick();
  if (currentRequest !== requestId) return;
  readerRef.value?.showModal();

  if (item.readType === "markdown") {
    loading.value = true;
    try {
      const response = await fetch(item.readUrl);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const content = await response.text();
      if (currentRequest === requestId) markdown.value = content;
    } catch {
      if (currentRequest === requestId) {
        loadError.value = "内容暂时无法加载，请下载原文件查看。";
      }
    } finally {
      if (currentRequest === requestId) loading.value = false;
    }
  } else {
    loading.value = false;
  }

}

function askAboutResource() {
  window.dispatchEvent(new CustomEvent("link-help", { detail: { reader: readerRef.value } }));
}

function closeReader() {
  window.dispatchEvent(new CustomEvent("link-help", { detail: { readerClosed: true } }));
  readerRef.value?.close();
  requestId += 1;
  selected.value = null;
  markdown.value = "";
  loadError.value = "";
  videoError.value = false;
  videoRetry.value = 0;
  loading.value = false;
  readerTrigger?.focus();
}

function handleKeydown(event) {
  if (event.key === "Escape" && selected.value) closeReader();
}

watch(selected, (value) => {
  document.body.style.overflow = value ? "hidden" : "";
});

watch(() => route.query.resource, (id) => {
  const item = typeof id === "string" && libraryResources.find((resource) => resource.id === id);
  if (item && selected.value?.id !== item.id) void open(item);
}, { immediate: true, flush: "post" });

onMounted(() => window.addEventListener("keydown", handleKeydown));
onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
  document.body.style.overflow = "";
});
</script>

<template>
  <div class="sparse-page resource-page">
    <div ref="shelfScroll" class="page-scroll">
    <section class="resource-showcase" aria-labelledby="resource-page-title">
      <header class="resource-collection-row" data-tour="resources">
        <h1 id="resource-page-title">小书架</h1>
        <div class="collection-switch" aria-label="资料来源">
          <button type="button" :aria-pressed="collection === 'library'" @click="collection = 'library'">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 5h6v14H4zM11 7h4v12h-4zM16.5 9.5 20 10l-2.5 10" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
            精选资料
          </button>
          <button type="button" :aria-pressed="collection === 'courses'" @click="collection = 'courses'">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 5C9 3 6 3 3 4v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-3-1-6-1-9 1zm0 0v15" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
            课程资源
          </button>
        </div>
        <div v-if="collection === 'library'" class="resource-header-tools">
          <div class="resource-search" role="search">
            <svg class="resource-search__icon" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" stroke-width="2" />
              <path d="M16.5 16.5 21 21" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
            <input
              v-model="query"
              type="search"
              aria-label="搜索资料"
              placeholder="搜标题、主题、来源…"
            />
            <button
              v-if="query"
              class="resource-search__clear"
              type="button"
              aria-label="清空搜索"
              @click="query = ''"
            >×</button>
          </div>
          <div class="view-toggle" role="group" aria-label="视图切换">
            <button type="button" :aria-pressed="viewMode === 'deck'" :class="{ active: viewMode === 'deck' }" @click="switchView('deck')">卡片</button>
            <button type="button" :aria-pressed="viewMode === 'list'" :class="{ active: viewMode === 'list' }" @click="switchView('list')">清单</button>
          </div>
          <nav v-if="collection === 'library' && viewMode === 'deck' && deckPageCount > 1" class="resource-pager resource-deck-pager" aria-label="资料翻页">
            <button type="button" class="resource-pager__btn" :disabled="!canPrevPage" @click="goPrevPage">
              <span aria-hidden="true">‹</span> 上一页
            </button>
            <span class="resource-pager__count">
              <b>{{ deckPage + 1 }}</b> / {{ deckPageCount }}
            </span>
            <button type="button" class="resource-pager__btn" :disabled="!canNextPage" @click="goNextPage">
              下一页 <span aria-hidden="true">›</span>
            </button>
          </nav>
        </div>
        <span class="resource-count" aria-live="polite">{{ resultLabel }}</span>
      </header>
      <CourseResourceCatalog v-if="collection === 'courses'" />
      <div v-if="collection === 'library'" class="resource-toolbar">
        <div class="facet-group" aria-label="资源筛选">
          <div
            v-for="def in FILTER_DEFS"
            :key="def.key"
            class="scene-select"
            :class="{ open: openMenu === def.key }"
            @focusout="onSceneBlur($event, def.key)"
          >
            <button
              type="button"
              class="scene-select__trigger"
              :class="{ active: filterValues[def.key] }"
              aria-haspopup="listbox"
              :aria-expanded="openMenu === def.key"
              @click="openMenu = openMenu === def.key ? '' : def.key"
            >
              <span class="scene-select__dim">{{ def.label }}</span>
              <span class="scene-select__val">{{ filterValues[def.key] || '全部' }}</span>
              <svg class="scene-select__chevron" viewBox="0 0 12 12" aria-hidden="true">
                <path d="M2.5 4.5 6 8l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
            <ul v-show="openMenu === def.key" class="scene-select__menu" role="listbox" :aria-label="`按${def.label}筛选`">
              <li>
                <button type="button" role="option" :aria-selected="!filterValues[def.key]" :class="{ active: !filterValues[def.key] }" @click="pickFilter(def.key, '')">
                  全部 <b>{{ libraryResources.length }}</b>
                </button>
              </li>
              <li v-for="opt in def.options" :key="opt">
                <button type="button" role="option" :aria-selected="filterValues[def.key] === opt" :class="{ active: filterValues[def.key] === opt }" @click="pickFilter(def.key, opt)">
                  {{ opt }} <b>{{ facetCounts[def.key][opt] || 0 }}</b>
                </button>
              </li>
            </ul>
          </div>
          <span v-if="filterActive" class="facet-active-tag">{{ activeFilterLabel }}</span>
          <button v-if="filterActive" class="facet-clear" type="button" @click="clearFilters">
            <svg viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 2.5l7 7m0-7-7 7" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
            清空
          </button>
        </div>
        <div class="resource-toolbar__tools">
          <button class="reset-layout" type="button" @click="layoutKey += 1">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 11a8 8 0 0 1 13.6-5.2L20 8m0-5v5h-5M20 13a8 8 0 0 1-13.6 5.2L4 16m0 5v-5h5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>
            重置卡片位置
          </button>
        </div>
      </div>


      <section v-if="collection === 'library' && viewMode === 'deck'" class="resource-deck" aria-label="可拖动资源卡片墙">


        <DraggableResourceCard
          v-for="item in visible"
          :key="`${layoutKey}-${filterKey}-${deckPage}-${item.id}`"
          :item="item"
          :active="activeCard === item.id"
          @activate="activeCard = $event"
          @open="open"
        />
        <div v-if="deckEmptyNote" class="resource-deck-empty">
          <span class="resource-deck-empty__tag">{{ searchActive ? '搜索结果' : (activeFilterLabel || '全部资料') }}</span>
          <strong>{{ deckEmptyNote.title }}</strong>
          <p>{{ deckEmptyNote.text }}</p>
        </div>
      </section>

      <section v-if="collection === 'library' && viewMode === 'list'" class="resource-list" aria-label="资源清单">
        <ol class="resource-list__rows">
          <li v-for="(item, idx) in listItems" :key="item.id" class="resource-list__row">
            <span class="resource-list__num">{{ listPage * LIST_PAGE_SIZE + idx + 1 }}</span>
            <button type="button" class="resource-list__title" :title="item.description" @click="open(item)">
              {{ item.title }}
            </button>
            <span class="resource-list__meta">{{ rowMeta(item) }}</span>
            <a
              v-if="item.downloadUrl"
              class="resource-list__dl"
              :href="item.downloadUrl"
              :download="item.downloadName"
              @click.stop
            >下载</a>
          </li>
        </ol>
        <div v-if="!listItems.length" class="resource-deck-empty">
          <span class="resource-deck-empty__tag">{{ searchActive ? '搜索结果' : (activeFilterLabel || '全部资料') }}</span>
          <strong>{{ deckEmptyNote?.title || '没有资料' }}</strong>
          <p>{{ deckEmptyNote?.text || '换个筛选条件试试。' }}</p>
        </div>
        <nav v-if="listPageCount > 1" class="resource-pager" aria-label="清单翻页">
          <button type="button" class="resource-pager__btn" :disabled="!canPrevList" @click="listPage -= 1">
            <span aria-hidden="true">‹</span> 上一页
          </button>
          <span class="resource-pager__count">
            <b>{{ listPage + 1 }}</b> / {{ listPageCount }}
          </span>
          <button type="button" class="resource-pager__btn" :disabled="!canNextList" @click="listPage += 1">
            下一页 <span aria-hidden="true">›</span>
          </button>
        </nav>
      </section>
    </section>

    <section v-if="collection === 'library'" ref="previewBoard" tabindex="-1" class="resource-board" aria-label="分类资料浏览">
      <header class="resource-board__head">
        <h2>分类浏览</h2>
      </header>
      <div class="resource-board__legend" aria-label="按用途筛选">
        <button
          v-for="scene in SCENE_OPTIONS"
          :key="scene"
          type="button"
          :class="`tone-${sceneTone[scene] || 'topic'}`"
          :aria-pressed="filterValues.theme === scene"
          @click="pickFilter('theme', filterValues.theme === scene ? '' : scene)"
        >
          {{ scene }} <b>{{ facetCounts.theme[scene] || 0 }}</b>
        </button>
      </div>
      <div class="resource-board__grid">
        <template v-for="tile in boardTiles" :key="`board-${tile.id}`">
          <div v-if="tile.placeholder" class="resource-board-card is-empty">
            <div class="resource-board-card__copy">
              <em>{{ tile.category }}</em>
              <strong>{{ tile.title }}</strong>
              <p>{{ tile.text }}</p>
            </div>
          </div>
          <button
            v-else
            type="button"
            class="resource-board-card"
            :data-tone="tile.tone"
            @click="open(tile)"
          >
            <span class="resource-board-card__cover" aria-hidden="true">
              <span>{{ tile.coverLabel || tile.category }}</span>
              <strong>{{ tile.coverTitle || tile.title }}</strong>
              <span>{{ tile.format?.split(' / ')[0] }}</span>
            </span>
            <span class="resource-board-card__copy">
              <em>{{ tile.category }}</em>
              <strong>{{ tile.title }}</strong>
              <p>{{ tile.description }}</p>
              <span class="resource-board-card__foot">
                <span>{{ metaLabel(tile) }}</span>
                <span aria-hidden="true">↗</span>
              </span>
            </span>
          </button>
        </template>
      </div>
      <p class="resource-note">课题专包与评课说明为训练摘要；官方大纲提供 PDF 预览与原始 Word。非正式国标条目均已在简介中标明。</p>
    </section>


    </div>

    <button v-if="previewBelow" type="button" class="shelf-preview-hint" aria-label="向下查看分类资料预览" @click="revealPreview"><span aria-hidden="true">⌄</span></button>
    <Teleport to="body">
      <dialog v-if="selected" ref="readerRef" data-assistant-reader class="reader-mask" :aria-labelledby="`reader-title-${selected.id}`" @cancel.prevent="closeReader" @mousedown.self="closeReader">
        <section
          class="reader-dialog"
          tabindex="-1"
        >
          <header class="reader-head">
            <div>
              <span>{{ selected.category }} · {{ selected.source }} · {{ selected.year }}</span>
              <h2 :id="`reader-title-${selected.id}`" data-assistant-detail="resource-title">{{ selected.title }}</h2>
              <p data-assistant-detail="resource-summary">{{ selected.description }}</p>
            </div>
            <div class="reader-head__actions">
              <button type="button" @click="askAboutResource">问阿贝贝</button>
              <button type="button" aria-label="关闭阅读器" autofocus @click="closeReader">×</button>
            </div>
          </header>

          <div class="reader-body">
            <iframe
              v-if="selected.readType === 'pdf'"
              :src="selected.readUrl"
              :title="`${selected.title} PDF 预览`"
            />
            <div v-else-if="selected.readType === 'video' && !videoError" class="reader-video-wrap">
              <video
                :key="videoRetry"
                class="reader-video"
                :src="videoSrc"
                :poster="selected.thumbnail || selected.boardImage || undefined"
                controls
                playsinline
                preload="metadata"
                :aria-label="selected.title"
                @error="handleVideoError"
              ></video>
            </div>
            <div v-else-if="selected.readType === 'video'" class="reader-status is-error">
              <p>这段视频暂时播不了，可以重试或直接打开视频文件：</p>
              <p class="reader-video-actions">
                <button type="button" @click="videoError = false; videoRetry = 0">重试播放</button>
                <a :href="selected.downloadUrl || selected.readUrl" target="_blank" rel="noopener noreferrer">在新标签页打开 ↗</a>
              </p>
            </div>
            <div v-else-if="selected.readType === 'image'" class="reader-image-wrap">
              <img
                :src="selected.readUrl"
                :alt="selected.title"
                loading="lazy"
                decoding="async"
              />
            </div>
            <div v-else-if="selected.readType === 'external'" class="reader-status">
              <a
                class="reader-external-link"
                :href="selected.externalUrl || selected.readUrl"
                target="_blank"
                rel="noopener noreferrer"
              >在新标签页打开外部资源 ↗</a>
            </div>
            <div v-else-if="loading" class="reader-status">正在载入内容...</div>
            <div v-else-if="loadError" class="reader-status is-error">{{ loadError }}</div>
            <MarkdownReader v-else data-assistant-detail="resource-summary" :content="markdown" />
          </div>

          <footer class="reader-foot">
            <span>
              {{ selected.format }}
              <template v-if="selected.pages"> · {{ selected.pages }} 页</template>
              <template v-else-if="selected.duration"> · {{ selected.duration }}</template>
            </span>
            <a
              v-if="selected.readType === 'external'"
              :href="selected.externalUrl || selected.readUrl"
              target="_blank"
              rel="noopener noreferrer"
            >打开链接 ↗</a>
            <a v-if="selected.downloadUrl" :href="selected.downloadUrl" :download="selected.downloadName">下载原文件</a>
            <span v-else class="reader-foot-hint">点上方「文件清单」里的文件名直接查看 / 下载</span>
          </footer>
        </section>
      </dialog>
    </Teleport>
  </div>
</template>

<style scoped>
/* Keep the shared navigation and top bar used by the course desk. */
:global(html[data-ui-theme] .app-shell:not(.protected-shell) .workspace:has(.resource-page)) {
  background:
    repeating-linear-gradient(105deg, #8463440e 0 1px, transparent 1px 5px),
    linear-gradient(180deg, #826950, #cbb397 48%, #eadcc6);
}

.resource-page {
  --rb-ink: #3f3024;
  --rb-ink-soft: #6e5945;
  --rb-paper: #fdf7e9;
  --rb-paper-2: #f4e7cd;
  --rb-wood: #8a5a32;
  --rb-accent: #dc8142;
  --rb-accent-deep: #b76128;
  --rb-line: rgba(125, 88, 52, .3);
  --rb-pill: 999px;
  --rb-shadow: 0 18px 40px rgba(24, 16, 8, .38);
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  max-width: none;
  padding-bottom: 0;
  overflow: hidden;
}

.resource-showcase {
  display: grid;
  gap: 12px;
  min-width: 0;
  padding: clamp(12px, 1.5vw, 20px);
  border: 1px solid #b58f6659;
  border-radius: 16px;
  background:
    radial-gradient(ellipse at 88% 0%, #d8aa7430, transparent 50%),
    linear-gradient(154deg, #6c5341, #483628);
  box-shadow: inset 0 1px #e6c59b32, 0 8px 24px #251a1740;
}

.resource-showcase .resource-collection-row,
.resource-showcase .resource-toolbar,
.resource-showcase .resource-deck-pager {
  margin-bottom: 0;
}

.resource-showcase .resource-deck-pager {
  justify-self: end;
  margin-block-start: -4px;
}

.resource-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  width: 100%;
  max-width: none;
  margin-bottom: 16px;
}

.resource-head :deep(.split-title) {
  font-size: clamp(40px, 4.5vw, 58px);
  letter-spacing: 0;
}

.resource-head .shiny-kicker {
  margin-bottom: 7px;
}

.resource-head .page-lead {
  margin-top: 7px;
  font-size: 14px;
}

.resource-summary {
  display: flex;
  align-items: baseline;
  gap: 9px;
  padding-bottom: 7px;
  color: #7c6247;
}

.resource-summary strong {
  color: #c9661f;
  font-size: 38px;
  line-height: 1;
}

.resource-summary span {
  font-size: 12px;
  letter-spacing: 0.08em;
}

.resource-toolbar {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  padding: 7px 10px;
  border: 1px solid rgba(255, 235, 196, .34);
  border-radius: 16px;
  background: rgba(252, 245, 229, .94);
  box-shadow: 0 10px 28px rgba(28, 18, 9, .26), inset 0 1px rgba(255, 255, 255, .7);
  backdrop-filter: blur(8px);
}

.resource-toolbar__tools {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 0 0 auto;
}

.resource-search {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 226px;
  height: 38px;
  padding: 0 14px;
  border: 1px solid rgba(138, 90, 50, .32);
  border-radius: var(--rb-pill);
  background: #fffdf7;
  color: #7a634a;
  box-shadow: inset 0 1px 2px rgba(90, 60, 30, .08);
  transition: border-color .18s ease, background .18s ease, box-shadow .18s ease;
}

.resource-search:focus-within {
  border-color: rgba(220, 129, 66, .72);
  background: #fffaf0;
  box-shadow: 0 0 0 3px rgba(220, 129, 66, .16);
  color: var(--rb-ink);
}

.resource-search__icon {
  width: 16px;
  height: 16px;
  flex: 0 0 auto;
}

.resource-search input {
  flex: 1;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: #3f4837;
  font-size: 12.5px;
}

.resource-search input::placeholder {
  color: #596453;
}

.resource-search input::-webkit-search-cancel-button {
  display: none;
}

.resource-search__clear {
  flex: 0 0 auto;
  width: 18px;
  height: 18px;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  color: #44503c;
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
}

.resource-search__clear:hover {
  background: rgba(255, 122, 24, 0.3);
  color: #46513e;
}

.facet-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px;
  flex: 1 1 auto;
  min-width: 0;
}

.scene-select {
  position: relative;
  flex: 0 0 auto;
}

.scene-select__trigger {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 14px;
  border: 1px solid rgba(138, 90, 50, .3);
  border-radius: var(--rb-pill);
  background: #fffaf0;
  color: var(--rb-ink);
  font-size: 12.5px;
  line-height: 1.2;
  cursor: pointer;
  box-shadow: 0 2px 0 rgba(138, 90, 50, .16);
  transition: border-color .16s ease, background .16s ease, color .16s ease, transform .16s ease, box-shadow .16s ease;
}

.scene-select__trigger:hover,
.scene-select.open .scene-select__trigger {
  border-color: rgba(220, 129, 66, .6);
  background: #fff2dc;
  transform: translateY(-1px);
}

.scene-select__trigger:active {
  transform: translateY(1px);
  box-shadow: none;
}

.scene-select__trigger.active {
  border-color: #d68b48;
  background: linear-gradient(140deg, #ffdda7, #e2a05d);
  color: #422a17;
  font-weight: 700;
  box-shadow: 0 2px 0 #b36e33, 0 6px 14px rgba(120, 70, 25, .22);
}

.scene-select__dim {
  color: #5a6552;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.scene-select__val {
  max-width: 9em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.facet-active-tag {
  flex: 0 0 auto;
  padding: 7px 13px;
  border: 1px solid #d68b48;
  border-radius: var(--rb-pill);
  background: linear-gradient(140deg, #ffe0ad, #e3a160);
  color: #422a17;
  font-size: 11.5px;
  font-weight: 700;
  box-shadow: 0 2px 0 #b36e33;
}

.facet-clear {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  flex: 0 0 auto;
  padding: 7px 11px;
  border: 1px solid rgba(138, 90, 50, .28);
  border-radius: var(--rb-pill);
  background: rgba(255, 253, 247, .8);
  color: #7a5a3e;
  font-size: 11.5px;
  cursor: pointer;
  transition: border-color .16s ease, color .16s ease, background .16s ease;
}

.facet-clear svg {
  width: 10px;
  height: 10px;
}

.facet-clear:hover {
  border-color: rgba(220, 129, 66, .6);
  background: #fff2dc;
  color: #a85420;
}

.scene-select__trigger:focus-visible {
  outline: 2px solid rgba(220, 129, 66, .65);
  outline-offset: 2px;
}

.scene-select__chevron {
  width: 11px;
  height: 11px;
  transition: transform 0.18s ease;
}

.scene-select.open .scene-select__chevron {
  transform: rotate(180deg);
}

.scene-select__menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 30;
  min-width: 172px;
  margin: 0;
  padding: 5px;
  list-style: none;
  border: 1px solid rgba(138, 90, 50, .32);
  border-radius: 14px;
  background: #fffaf0;
  box-shadow: 0 14px 34px rgba(32, 20, 9, .42);
}

.scene-select__menu button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  width: 100%;
  padding: 8px 11px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: #42503a;
  font-size: 12.5px;
  line-height: 1.2;
  text-align: left;
  cursor: pointer;
  transition: background 0.14s ease, color 0.14s ease;
}

.scene-select__menu button b {
  font-size: 11px;
  font-weight: 600;
  color: #596453;
}

.scene-select__menu button:hover {
  background: rgba(255, 122, 24, 0.1);
  color: #46513e;
}

.scene-select__menu button.active {
  background: linear-gradient(140deg, #ffe0ad, #e3a160);
  color: #422a17;
  font-weight: 700;
}

.scene-select__menu button.active b {
  color: #7a4a22;
}

.reset-layout {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  flex: 0 0 auto;
  padding: 8px 14px;
  border: 1px solid rgba(138, 90, 50, .35);
  border-radius: var(--rb-pill);
  background: linear-gradient(#fffaf0, #f0dfbe);
  color: #5b4029;
  font-size: 12px;
  cursor: pointer;
  box-shadow: 0 2px 0 rgba(138, 90, 50, .2);
  transition: transform .16s ease, background .16s ease, box-shadow .16s ease;
}

.reset-layout svg {
  width: 15px;
  height: 15px;
}

.reset-layout:hover {
  background: #fff3dc;
  transform: translateY(-1px);
}

.reset-layout:active {
  transform: translateY(1px);
  box-shadow: none;
}

.reset-layout:focus-visible {
  outline: 2px solid rgba(220, 129, 66, .65);
  outline-offset: 2px;
}

/* 卡片 / 清单 视图切换 */
.view-toggle {
  display: inline-flex;
  flex: 0 0 auto;
  gap: 3px;
  padding: 3px;
  border: 1px solid rgba(138, 90, 50, .3);
  border-radius: var(--rb-pill);
  background: rgba(255, 250, 240, .8);
}

.view-toggle button {
  padding: 6px 14px;
  border: 0;
  border-radius: var(--rb-pill);
  background: transparent;
  color: #7a634a;
  font-size: 12px;
  cursor: pointer;
  transition: background .16s ease, color .16s ease;
}

.view-toggle button:hover {
  background: rgba(220, 129, 66, .1);
}

.view-toggle button.active {
  background: linear-gradient(140deg, #ffdda7, #e2a05d);
  color: #422a17;
  font-weight: 700;
  box-shadow: 0 1px 4px rgba(120, 70, 25, .2);
}

/* 清单视图 */
.resource-page .resource-list {
  flex: 0 0 auto;
  border: 1px solid rgba(138, 90, 50, .35);
  border-radius: 14px;
  background: #fdfaf2;
  box-shadow: 0 14px 34px rgba(20, 12, 5, .3);
  overflow: hidden;
}

.resource-list__rows {
  margin: 0;
  padding: 0;
  list-style: none;
}

.resource-list__row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 16px;
  border-bottom: 1px dashed rgba(143, 153, 132, 0.25);
}

.resource-list__row:last-child {
  border-bottom: 0;
}

.resource-list__row:hover {
  background: rgba(255, 240, 207, 0.45);
}

.resource-list__num {
  flex: 0 0 34px;
  color: #a89a80;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.resource-list__title {
  flex: 1 1 auto;
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: #3d4438;
  font-size: 13px;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  cursor: pointer;
}

.resource-list__title:hover {
  color: #8a5a1e;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.resource-list__meta {
  flex: 0 0 auto;
  max-width: 320px;
  color: #8f8a7c;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.resource-page .resource-list__dl {
  flex: 0 0 auto;
  padding: 5px 13px;
  border: 1px solid rgba(178, 141, 88, 0.5);
  border-radius: var(--rb-pill, 999px);
  background: linear-gradient(160deg, #fff0cf, #e3c690);
  color: #5b3c18;
  font-size: 11.5px;
  font-weight: 700;
  text-decoration: none;
  white-space: nowrap;
}

.resource-page .resource-list__dl:hover {
  background: linear-gradient(160deg, #fff6e0, #edcf9a);
  box-shadow: 0 2px 6px rgba(120, 80, 30, .22);
}

.resource-list .resource-pager {
  position: static;
  display: flex;
  justify-content: center;
  gap: 10px;
  padding: 10px 0;
  border-top: 1px dashed rgba(143, 153, 132, 0.25);
}

.resource-deck {
  position: relative;
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
  min-height: 585px;
  aspect-ratio: 1.74;
  container-type: inline-size;
  overflow: hidden;
  border: 1px solid #9d7958;
  border-radius: 12px;
  background: #89634e url('/assets/desk/resource-reference.png') center / 100% 100% no-repeat;
  box-shadow: 0 12px 28px #261c2440, inset 0 1px #ffe5bb80;
  isolation: isolate;
}

.resource-board {
  margin-top: clamp(24px, 3.4vw, 46px);
  display: grid;
  gap: 18px;
  padding: clamp(18px, 2.5vw, 32px);
  border: 1px solid #d0b89b;
  border-top: 5px solid #a27a55;
  border-radius: 14px;
  background: linear-gradient(155deg, #fcf6e9, #f0e5d2);
  color: #44362e;
  box-shadow: inset 0 1px #fff9ec, 0 8px 24px #24181030;
}
/* 左右翻页：卡片墙每页 4 张，多的翻页看，不往下溢出 */
.resource-pager {
  position: absolute;
  left: 50%;
  bottom: 14px;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border: 1px solid rgba(150, 104, 58, .5);
  border-radius: 14px;
  background: linear-gradient(160deg, rgba(255, 249, 233, .97), rgba(238, 220, 186, .96));
  box-shadow: 0 4px 0 rgba(120, 80, 42, .34), 0 14px 28px rgba(16, 10, 4, .42), inset 0 1px rgba(255, 255, 255, .9);
  backdrop-filter: blur(10px);
  z-index: 30;
}

.resource-pager.resource-deck-pager {
  position: static;
  display: flex;
  justify-content: center;
  width: fit-content;
  max-width: 100%;
  margin: 0 0 10px auto;
  transform: none;
  z-index: auto;
}

.resource-pager__btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: 1px solid transparent;
  border-radius: 999px;
  background: transparent;
  color: #42503a;
  font-size: 12px;
  letter-spacing: 0.02em;
  transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease;
}

.resource-pager__btn span {
  font-size: 14px;
  line-height: 1;
}

.resource-pager__btn:hover:not(:disabled) {
  border-color: rgba(220, 129, 66, .4);
  background: #fff0d6;
  color: #a85420;
  transform: translateX(2px);
}

.resource-pager__btn:disabled {
  opacity: .32;
  cursor: not-allowed;
  transform: none;
}

.resource-pager__count {
  min-width: 52px;
  text-align: center;
  font-size: 11px;
  letter-spacing: 0.08em;
  color: #606b56;
}

.resource-pager__count b {
  color: #a85420;
  font-size: 14px;
  font-weight: 700;
}

/* 空分类：模块留着，写清楚为什么空，别用别的素材来凑 */
.resource-deck-empty {
  position: absolute;
  inset: 50% auto auto 50%;
  transform: translate(-50%, -50%) rotate(-1deg);
  width: min(420px, 76%);
  display: grid;
  gap: 8px;
  padding: 22px 24px;
  border: 1.5px dashed rgba(255, 154, 66, 0.45);
  border-radius: 18px;
  background: #faf7eeed;
  text-align: center;
  justify-items: center;
}

.resource-deck-empty__tag {
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 122, 24, 0.16);
  color: #42503a;
  font-size: 11px;
  letter-spacing: 0.08em;
}

.resource-deck-empty strong {
  font-size: 16px;
  color: #3f4837;
}

.resource-deck-empty p {
  margin: 0;
  color: #596453;
  font-size: 12.5px;
  line-height: 1.75;
}

.resource-board__head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
}

.resource-board__head p {
  margin: 0 0 4px;
  color: #9d97a3;
  font-size: 10px;
  letter-spacing: 0.22em;
}

.resource-board__head h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 650;
}

.resource-board__head > span {
  color: #8f8994;
  font-size: 12px;
}

.resource-board__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.resource-board__legend button {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 7px 15px;
  border: 1px solid rgba(138, 90, 50, .28);
  border-radius: var(--rb-pill);
  background: rgba(253, 247, 233, .94);
  color: #5b4632;
  cursor: pointer;
  font-size: 12px;
  box-shadow: 0 3px 0 rgba(120, 80, 42, .22), 0 6px 14px rgba(20, 12, 5, .2);
  transition: transform .16s ease, background .16s ease, border-color .16s ease;
}

.resource-board__legend button:hover {
  transform: translateY(-2px);
  background: #fff6e3;
  border-color: rgba(220, 129, 66, .5);
}

.resource-board__legend button:active {
  transform: translateY(1px);
}

.resource-board__legend button[aria-pressed="true"],
.resource-board__legend button:hover[aria-pressed="true"] {
  border-color: #d68b48;
  background: linear-gradient(140deg, #ffdda7, #e2a05d);
  color: #422a17;
  font-weight: 700;
  box-shadow: 0 3px 0 #b36e33, 0 7px 16px rgba(120, 70, 25, .26);
}

.resource-board__legend b {
  font-weight: 600;
  opacity: 0.8;
}

.resource-board__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: clamp(16px, 1.55vw, 20px);
  align-items: stretch;
}

.resource-page .resource-board-card {
  --cover-paper: #d4d6b8;
  --cover-ink: #414829;
  width: 100%;
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr);
  gap: clamp(12px, 1.7vw, 20px);
  padding: clamp(14px, 1.6vw, 20px);
  border: 1px solid #c7ac8d;
  border-radius: 9px;
  background: #fbf1df;
  box-shadow: 0 2px 5px #65452d12;
  color: #382b23;
  text-align: left;
}

.resource-board-card.is-empty .resource-board-card__copy {
  grid-column: 1 / -1;
}

button.resource-board-card {
  cursor: pointer;
  transition: border-color 0.2s, background-color 0.2s;
}

.resource-page button.resource-board-card:hover,
.resource-page button.resource-board-card:focus-visible {
  border-color: #80502e;
  background: #fff5e5;
}

.resource-board-card[data-tone="official"] {
  --cover-paper: #e7d1ae;
  --cover-ink: #653f25;
}

.resource-board-card[data-tone="review"] {
  --cover-paper: #ddd2df;
  --cover-ink: #543e59;
}

.resource-board-card[data-tone="case"] {
  --cover-paper: #cbd9d6;
  --cover-ink: #304b4a;
}

.resource-board-card__cover {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 5px;
  min-width: 0;
  min-height: 108px;
  padding: 9px 7px 8px 12px;
  border: 1px solid #33251a30;
  border-radius: 3px 6px 6px 3px;
  background: linear-gradient(90deg, #32271c30, transparent 10px), var(--cover-paper);
  color: var(--cover-ink);
  box-shadow: 2px 2px 0 #b79c7d;
  overflow-wrap: anywhere;
}

.resource-board-card__cover > span {
  font-size: 9px;
  line-height: 1.2;
}

.resource-board-card__cover strong {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  overflow: hidden;
  font-family: "Songti SC", SimSun, serif;
  font-size: 12px;
  line-height: 1.35;
}

.resource-board-card__copy {
  display: grid;
  align-content: start;
  gap: 7px;
  min-width: 0;
}

.resource-board-card__copy em {
  color: #725238;
  font-size: 11px;
  font-style: normal;
}

.resource-board-card__copy > strong {
  font-size: 14px;
  line-height: 1.35;
}

.resource-page .resource-board-card__copy p {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  margin: 0;
  color: #604b3e;
  font-size: 13px;
  line-height: 1.65;
}

.resource-board-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-top: 3px;
  color: #745638;
  font-size: 11px;
}

.resource-board-card__foot > span:last-child {
  font-size: 15px;
  line-height: 1;
}

.deck-instruction {
  position: absolute;
  top: 50%;
  left: 50%;
  width: min(330px, 80%);
  transform: translate(-50%, -50%);
  color: rgba(215, 208, 219, 0.24);
  text-align: center;
}

.deck-instruction span {
  font-size: 10px;
  letter-spacing: 0.28em;
}

.deck-instruction strong {
  display: block;
  margin-top: 8px;
  font-size: clamp(24px, 4vw, 42px);
  line-height: 1.2;
}

.deck-instruction p {
  margin: 10px 0 0;
  font-size: 12px;
}

.resource-note {
  width: fit-content;
  margin: 10px 0 0;
  padding: 4px 8px;
  border-radius: 5px;
  background: #fff6e5ed;
  color: #59402d;
  font-size: 11px;
}

.resource-page .resource-collection-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-bottom: 5px;
  padding: 3px 12px 5px;
  color: #fff4df;
}

.resource-collection-row h1 {
  margin: 0;
  color: inherit;
  font-size: clamp(23px, 2.1vw, 32px);
  font-weight: 700;
  line-height: 1.2;
}

.resource-page .resource-collection-row .resource-count {
  margin-inline-start: auto;
}

.resource-page .collection-switch {
  display: flex;
  flex-wrap: wrap;
  gap: 9px;
}

.resource-page .collection-switch button {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 8px 16px;
  border: 1px solid rgba(255, 235, 196, .38);
  border-radius: var(--rb-pill);
  background: rgba(253, 247, 233, .9);
  box-shadow: 0 3px 0 rgba(120, 80, 42, .38), 0 8px 16px rgba(20, 12, 5, .28);
  color: #5b4632;
  font-size: 12.5px;
  cursor: pointer;
  transition: transform .16s ease, background .16s ease, box-shadow .16s ease;
}

.resource-page .collection-switch button svg {
  width: 15px;
  height: 15px;
  opacity: .82;
}

.resource-page .collection-switch button:hover {
  background: #fffaf0;
  transform: translateY(-1px);
}

.resource-page .collection-switch button:active {
  transform: translateY(2px);
  box-shadow: 0 1px 0 rgba(120, 80, 42, .38);
}

.resource-page .collection-switch button[aria-pressed="true"] {
  border-color: #f0c587;
  background: linear-gradient(160deg, #ffdfa5, #df9f5b);
  color: #422a17;
  font-weight: 700;
  box-shadow: 0 3px 0 #a86633, 0 8px 18px rgba(40, 20, 6, .34);
}

.resource-page .collection-switch button[aria-pressed="true"] svg {
  opacity: 1;
}

.resource-page .resource-count {
  display: block;
  align-self: center;
  padding: 6px 13px;
  border: 1px solid rgba(255, 235, 196, .38);
  border-radius: var(--rb-pill);
  background: rgba(253, 247, 233, .9);
  color: #6b4a2a;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  box-shadow: 0 4px 12px rgba(20, 12, 5, .24);
}


.reader-mask {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: 24px;
  width:100vw;
  height:100dvh;
  max-width:none;
  max-height:none;
  margin:0;
  border:0;
  background:transparent;
  color:#f4f2f6;
}
.reader-mask::backdrop { background:rgba(6,4,9,.86); backdrop-filter:blur(12px); }

.reader-dialog {
  display: grid;
  grid-template-rows: auto minmax(0, 1fr) auto;
  width: min(1100px, 100%);
  height: min(860px, calc(100vh - 48px));
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 18px;
  outline: none;
  background: #120e17;
  box-shadow: 0 40px 120px rgba(0, 0, 0, 0.72);
}

.reader-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 28px;
  padding: 22px 26px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.reader-head span {
  color: #ffad70;
  font-size: 10px;
  letter-spacing: 0.1em;
}

.reader-head h2 {
  margin: 6px 0 5px;
  color: #f8f4fa;
  font-size: clamp(19px, 2.4vw, 28px);
  line-height: 1.35;
}

.reader-head p {
  margin: 0;
  color: #938b98;
  font-size: 12px;
}

.reader-head button {
  flex: 0 0 auto;
  width: 36px;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.04);
  color: #ddd5e1;
  font-size: 24px;
  line-height: 1;
}

.reader-head button:hover {
  border-color: rgba(255, 151, 72, 0.5);
  color: #ffb67f;
}

.reader-head__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.reader-head__actions button:first-child {
  width: auto;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
}

.reader-body {
  min-height: 0;
  overflow: auto;
  background: #0c0910;
}

.reader-body iframe {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 520px;
  border: 0;
  background: #ecebea;
}

.reader-video-wrap {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  min-height: 420px;
  background: #000;
}

.reader-video {
  display: block;
  width: 100%;
  max-height: calc(100vh - 260px);
  background: #000;
}

.reader-image-wrap {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  min-height: 380px;
  padding: 12px;
  background: #fffdf8;
  overflow: auto;
}

.reader-image-wrap img {
  display: block;
  width: 100%;
  max-width: 1080px;
  height: auto;
  border-radius: 10px;
  background: #fffdf8;
}

.reader-external-link {
  padding: 12px 20px;
  border-radius: 999px;
  background: #ff7a18;
  color: #211008;
  font-size: 14px;
  font-weight: 700;
  text-decoration: none;
}

.reader-external-link:hover {
  background: #ffa063;
}

.reader-status {
  display: grid;
  min-height: 320px;
  place-items: center;
  color: #aaa2ae;
  font-size: 13px;
}

.reader-status.is-error {
  color: #ffaf7c;
}

.reader-video-actions { display: flex; gap: 14px; align-items: center; }
.reader-video-actions button, .reader-video-actions a { color: #ffad70; text-decoration: underline; background: none; border: 0; cursor: pointer; font-size: inherit; }
.reader-foot-hint { color: inherit; opacity: 0.65; font-size: 12px; }

.reader-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 14px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  color: #817a87;
  font-size: 11px;
}

.reader-foot a {
  padding: 9px 14px;
  border-radius: 8px;
  background: #ff7a18;
  color: #211008;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.reader-fade-enter-active,
.reader-fade-leave-active {
  transition: opacity 0.2s ease;
}

.reader-fade-enter-from,
.reader-fade-leave-to {
  opacity: 0;
}

/* 分类像夹在纸堆里的彩色索引贴——备课紫 / 试讲绿 / 课例黄 / 备考橙 */
.resource-board__legend button.tone-topic:not([aria-pressed="true"]):not(:hover) {
  background: #dbc7d5;
}

.resource-board__legend button.tone-review:not([aria-pressed="true"]):not(:hover) {
  background: #d5d2ae;
}

.resource-board__legend button.tone-case:not([aria-pressed="true"]):not(:hover) {
  background: #e9d7b3;
}

.resource-board__legend button.tone-official:not([aria-pressed="true"]):not(:hover) {
  background: #e1c4a5;
}

.resource-toolbar {
  border-color: #bd93636e;
  border-radius: 9px;
  background:
    repeating-linear-gradient(97deg, #9b73410d 0 1px, transparent 1px 5px),
    linear-gradient(165deg, #d8ba8d, #bc956b);
  box-shadow: 0 3px 0 #62472f, 0 8px 19px #2b1e1966, inset 0 1px #f9deb9;
}

.scene-select__trigger,
.reset-layout,
.view-toggle {
  border-radius: 6px;
  border-color: #97745570;
  background: linear-gradient(155deg, #f2e5cb, #e1caa8);
}

.scene-select__chevron {
  color: #795a39;
  filter: drop-shadow(0 1px #ffefcc);
}

.resource-search,
.resource-search:focus-within {
  border-radius: 6px;
  border-color: #9b7856;
  background: #fff5e1ba;
  box-shadow: inset 0 1px 3px #61462e35;
}

.view-toggle button {
  border-radius: 4px;
}

.view-toggle button.active {
  color: #3e2f3e;
  background: linear-gradient(145deg, #dfcbd8, #c2a6bb);
  box-shadow: 0 1px 2px #6e4c513f;
}

.resource-pager.resource-deck-pager {
  border-radius: 6px;
  border-color: #ad865f;
  background: linear-gradient(160deg, #ad865f, #745038);
  box-shadow: inset 0 1px #e0b686, 0 3px 0 #4d3327;
}

.resource-deck-pager .resource-pager__btn {
  border-color: #795933;
  border-radius: 5px;
  background: linear-gradient(#e1c49a, #bc956a);
  color: #392820;
  box-shadow: inset 0 1px #f3dfbb;
}

.resource-deck-pager .resource-pager__count,
.resource-deck-pager .resource-pager__count b {
  color: #fff3db;
}

.resource-page .resource-collection-row {
  gap: 8px 14px;
  padding: 6px 10px;
  border: 1px solid #b38a6760;
  border-radius: 12px;
  background: linear-gradient(158deg, #644630, #4c3327);
}

.resource-collection-row h1 {
  font-size: clamp(18px, 1.6vw, 24px);
}

.resource-page .collection-switch button {
  padding: 6px 10px;
  border-radius: 8px 8px 4px 4px;
  box-shadow: none;
}

.resource-header-tools {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 7px 10px;
  min-width: 0;
  margin-inline-start: auto;
}

.resource-header-tools .resource-search {
  width: clamp(155px, 15vw, 245px);
  height: 32px;
}

.resource-header-tools .resource-deck-pager {
  margin: 0;
  padding: 2px 4px;
  border-color: #b38a6760;
  background: #3e2a22;
  box-shadow: none;
}

.resource-header-tools .resource-pager__btn {
  padding: 4px 7px;
  border-color: transparent;
  background: transparent;
  box-shadow: none;
  color: #f8e7ce;
}

.resource-header-tools .resource-pager__btn:hover:not(:disabled),
.resource-header-tools .resource-pager__btn:focus-visible {
  background: #775438;
}

.resource-page .resource-collection-row .resource-count {
  margin-inline-start: 0;
}

.resource-showcase {
  gap: 7px;
  padding: 0;
  border: 0;
}

.resource-page .resource-collection-row {
  padding: 8px clamp(10px, 2.5vw, 36px);
  border-radius: 15px 15px 0 0;
  background: linear-gradient(105deg, #70503c, #5b3d31 65%, #67483a);
}

.resource-page .collection-switch button {
  border: 1px solid #e1b18355;
  border-radius: 7px;
  background: #805a46;
  color: #fff3df;
}

.resource-page .collection-switch button[aria-pressed="true"] {
  background: linear-gradient(#ffe0a5, #edbc7c);
  color: #4b2d1f;
}

.resource-header-tools .resource-search {
  background: #43271f45;
  border-color: #d0ae936d;
  color: #f9e8d5;
}

.resource-header-tools .resource-search input,
.resource-header-tools .resource-search input::placeholder {
  color: #f9e8d5;
}

.resource-deck { border-radius: 0 0 13px 13px; }

@media (max-width: 900px) {
  .resource-deck {
    aspect-ratio: auto;
    background: linear-gradient(150deg, #987358, #73503d);
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    min-height: 0;
    height: auto;
    padding: 16px;
    overflow: visible;
  }

  .resource-header-tools { margin-inline-start: 0; }

  .resource-board__grid {
    grid-template-columns: 1fr;
  }


  .resource-deck-empty {
    position: static;
    grid-column: 1 / -1;
    justify-self: center;
    margin: 12px 0;
    transform: none;
  }

  .resource-pager {
    position: static;
    grid-column: 1 / -1;
    justify-self: center;
    transform: none;
  }


  .resource-page {
    display: block;
    height: auto;
    min-height: calc(100dvh - 120px);
    padding-bottom: 32px;
  }

  .resource-head {
    align-items: flex-start;
  }

  .resource-toolbar {
    align-items: stretch;
    flex-direction: column;
    gap: 8px;
  }

  .facet-group {
    gap: 6px;
  }

  .scene-select {
    flex: 1 1 30%;
    min-width: 104px;
  }

  .scene-select__trigger {
    justify-content: center;
    width: 100%;
  }

  .scene-select__menu {
    width: 100%;
  }

  .resource-toolbar__tools {
    justify-content: space-between;
  }

  .resource-search {
    flex: 1;
    width: auto;
  }



  .deck-instruction {
    display: none;
  }

  .resource-board__head {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (max-width: 620px) {
  .resource-head {
    gap: 16px;
  }

  .resource-summary {
    display: none;
  }

  .resource-deck { grid-template-columns: 1fr; padding: 12px; }

  .resource-collection-row h1 {
    font-size: 32px;
  }

  .resource-count {
    font-size: 11px;
  }

  .facet-active-tag {
    max-width: 140px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .resource-toolbar__tools {
    gap: 8px;
  }

  .view-toggle button,
  .reset-layout {
    padding: 7px 10px;
    font-size: 11px;
  }

  .reset-layout svg {
    width: 13px;
    height: 13px;
  }

  .resource-pager__btn {
    padding: 5px 10px;
    font-size: 11px;
  }

  .reader-mask {
    padding: 0;
  }

  .reader-dialog {
    width: 100%;
    height: 100dvh;
    border: 0;
    border-radius: 0;
  }

  .reader-head {
    padding: 18px;
  }

  .reader-head p {
    display: none;
  }

  .reader-foot {
    padding: 12px 16px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .reader-fade-enter-active,
  .reader-fade-leave-active {
    transition: none;
  }
}
.shelf-preview-hint {position:absolute;bottom:max(10px,env(safe-area-inset-bottom));left:50%;translate:-50% 0;z-index:4;display:grid;place-items:center;width:48px;height:44px;border:1px solid #f7dbad90;border-radius:24px;background:#402d20ee;color:#fff2d6;cursor:pointer;box-shadow:0 3px 12px #38200a55;}
.shelf-preview-hint span {font:700 32px/1 system-ui;animation:shelf-nudge 1.5s ease-in-out infinite;}
@keyframes shelf-nudge {0%,100%{transform:translateY(-6px)}50%{transform:translateY(-1px)}}
@media(prefers-reduced-motion:reduce){.shelf-preview-hint span{animation:none;}}
</style>
