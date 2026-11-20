import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { parse, compileScript } from '@vue/compiler-sfc'
import { transformSync } from 'esbuild'
import * as vue from 'vue'
import { useReducedMotion, useMotionReveal } from '../src/utils/useReducedMotion.js'
import * as uiTheme from '../src/utils/uiTheme.js'
import * as uiVersion from '../src/utils/uiVersion.js'
import * as studioPresentation from '../src/utils/studioPresentation.js'

const source = readFileSync(new URL('../src/views/GrowthArchiveView.vue', import.meta.url), 'utf8')

test('growth archive exposes real range loading and record navigation', () => {
  assert.match(source, /watch\(range, load\)/)
  assert.match(source, /@click="toggleHeatDay\(cell\)"/)
  assert.match(source, /router\.push\(/)
  assert.match(source, /query\.feedbackId = item\.id/)
  assert.doesNotMatch(source, /sum-demo/)
})

function createGrowth(fetchGrowth) {
  const { descriptor } = parse(source)
  const { code } = transformSync(compileScript(descriptor, { id: 'growth-sync-test' }).content, { format: 'cjs' })
  const navigation = []
  const imports = {
    '../components/fx/ModelShowcase.vue': {},
    '../utils/useReducedMotion.js': { useReducedMotion, useMotionReveal },
    '../utils/uiTheme.js': uiTheme,
    '../utils/uiVersion.js': uiVersion,
    '../utils/studioPresentation.js': studioPresentation,
    vue: { ...vue, onMounted() {}, watch() {} },
    'vue-router': { useRouter: () => ({ push: target => navigation.push(target) }) },
    'echarts/core': { use() {} },
    'echarts/renderers': {}, 'echarts/charts': {}, 'echarts/components': {}, 'vue-echarts': {},
    '../services/dashboard': { fetchGrowth },
    '../services/api': { api: { get: async () => ({ data: { items: [] } }) } },
  }
  const module = { exports: {} }
  new Function('require', 'module', 'exports', code)(name => {
    assert.ok(Object.hasOwn(imports, name), `Unexpected import ${name}`)
    return imports[name]
  }, module, module.exports)
  return { state: module.exports.default.setup({}, { expose() {} }), navigation }
}

test('growth heatmap filters the real records and toggles the date off', async () => {
  const data = {
    heatmap: [{ date: '2026-09-13', count: 1, minutes: 8 }],
    records: [{ id: 7, session_id: 3, when: '2026-09-13T10:00:00' }, { id: 8, when: '2026-09-12T10:00:00' }],
    journals: [{ id: 1, body: '真实日志' }],
  }
  const { state, navigation } = createGrowth(async () => data)
  await state.load()
  state.toggleHeatDay(data.heatmap[0])
  assert.deepEqual(state.visibleRecords.value.map(item => item.id), [7])
  state.openRecord(data.records[0])
  assert.deepEqual(navigation[0], { path: '/ai-review', query: { sessionId: 3, feedbackId: 7 } })
  state.toggleHeatDay(data.heatmap[0])
  assert.equal(state.visibleRecords.value.length, 2)
  assert.equal(state.visibleJournals.value[0].body, '真实日志')
})

test('growth loading failure clears old data and never fabricates scores or journals', async () => {
  const { state } = createGrowth(async () => { throw new Error('offline') })
  state.points.value = [{ score: 80 }]
  state.records.value = [{ id: 7 }]
  state.journals.value = [{ id: 1 }]
  await state.load()
  assert.match(state.loadError.value, /加载失败/)
  for (const key of ['points', 'records', 'journals', 'heatmap', 'milestones', 'summaries']) {
    assert.deepEqual(state[key].value, [])
  }
})

test('an older range response cannot replace the newest range', async () => {
  const pending = []
  const { state } = createGrowth(() => new Promise(resolve => pending.push(resolve)))
  const first = state.load()
  const second = state.load()
  pending[1]({ points: [{ score: 91 }], heatmap: [{ date: '2026-10-22', count: 1 }] })
  await second
  pending[0]({ points: [{ score: 65 }], heatmap: [{ date: '2026-09-22', count: 1 }] })
  await first
  assert.equal(state.points.value[0].score, 91)
  assert.equal(state.calendarMonth.value, '2026-10')
  assert.equal(state.growthLoading.value, false)
})

test('month calendar aligns Monday first and distinguishes missing coverage from zero activity', () => {
  const cells = studioPresentation.monthCalendar([{ date: '2026-10-09', count: 0 }, { date: '2026-10-22', count: 2 }], '2026-10')
  assert.equal(cells.length, 35)
  assert.equal(cells[0].placeholder, true)
  assert.equal(cells[3].date, '2026-10-01')
  assert.equal(cells.find(cell => cell.date === '2026-10-09').unavailable, false)
  assert.equal(cells.find(cell => cell.date === '2026-10-10').unavailable, true)
  assert.equal(cells.find(cell => cell.date === '2026-10-22').count, 2)
})

test('month calendar handles leap years and month lists crossing years', () => {
  const cells = studioPresentation.monthCalendar([], '2024-02')
  assert.equal(cells.filter(cell => !cell.placeholder).length, 29)
  assert.deepEqual(studioPresentation.calendarMonths([{ date: '2026-01-01' }, { date: '2025-12-31' }, { date: '2026-01-02' }]), ['2025-12', '2026-01'])
  assert.deepEqual(studioPresentation.monthCalendar([], '2026-13'), [])
})
