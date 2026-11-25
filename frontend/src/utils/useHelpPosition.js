import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
export function boundHelpPosition(position, viewport, size, margin = 12) {
  return { x: Math.max(margin, Math.min(position.x, Math.max(margin, viewport.width - size.width - margin))),
    y: Math.max(margin, Math.min(position.y, Math.max(margin, viewport.height - size.height - margin))) }
}
export function placeHelpBeside(anchor, viewport, size) {
  const gap = 8
  const leftSpace = anchor.left - 12 - gap
  const rightSpace = viewport.width - anchor.right - 12 - gap
  const centerY = (anchor.top + anchor.bottom - size.height) / 2
  const x = leftSpace >= size.width || leftSpace >= rightSpace
    ? anchor.left - gap - size.width : anchor.right + gap
  if (Math.max(leftSpace,rightSpace) >= size.width) return boundHelpPosition({x,y:centerY},viewport,size)

  const above = anchor.top - gap - size.height
  const below = anchor.bottom + gap
  const centerX = (anchor.left + anchor.right - size.width) / 2
  if (above >= 12) return boundHelpPosition({x:centerX,y:above},viewport,size)
  if (below + size.height <= viewport.height - 12) return boundHelpPosition({x:centerX,y:below},viewport,size)
  return boundHelpPosition({x,y:centerY},viewport,size)
}

const sizeKey = 'link-assistant-panel-size'
function loadPanelSize() {
  try {
    const size = JSON.parse(localStorage.getItem(sizeKey) || 'null')
    if (size && Number.isFinite(size.width) && size.width > 0 && Number.isFinite(size.height) && size.height > 0) return size
  } catch { /* fall back to default dimensions */ }
  return null
}

export function boundHelpSize(size, viewport, right = viewport.width - 12, top = 12) {
  const maxWidth = Math.max(1, right - 12)
  const maxHeight = Math.max(1, viewport.height - top - 12)
  return {
    width: Math.round(Math.min(maxWidth, Math.max(310, size.width))),
    height: Math.round(Math.min(maxHeight, Math.max(400, size.height))),
  }
}

export function useHelpPosition(fab, panel) {
  const positions = ref({ fab: null, panel: null })
  const dragging = ref('')
  const panelSize = ref(loadPanelSize())
  let resizeDrag
  let drag, pending, frame = 0, flight = 0, suppressUntil = 0
  const viewport = () => ({ width: window.innerWidth, height: window.innerHeight })
  function toss(position, size, vx, vy) {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return
    let previous = performance.now(), elapsed = 0
    function step(now) {
      const dt = Math.min(now - previous, 32)
      previous = now
      elapsed += dt
      vy += .0018 * dt
      const requested = { x: position.x + vx * dt, y: position.y + vy * dt }
      position = boundHelpPosition(requested, viewport(), size)
      if (requested.x !== position.x) vx *= -.45
      if (requested.y !== position.y) {
        vy *= -.35
        vx *= .65
      }
      positions.value.fab = position
      flight = elapsed < 1000 && (position.y === requested.y || Math.abs(vy) > .1 || Math.abs(vx) > .05)
        ? requestAnimationFrame(step) : 0
    }
    flight = requestAnimationFrame(step)
  }
  const style = key => computed(() => positions.value[key] ? { left: `${positions.value[key].x}px`, top: `${positions.value[key].y}px`, right: 'auto', bottom: 'auto' } : {})
  const fabStyle = style('fab'), panelPosition = style('panel')
  const panelStyle = computed(() => ({
    ...panelPosition.value,
    ...(panelSize.value ? { '--help-width': `${panelSize.value.width}px`, '--help-height': `${panelSize.value.height}px` } : {}),
  }))
  function savePanelSize() {
    try { localStorage.setItem(sizeKey, JSON.stringify(panelSize.value)) } catch { /* storage may be unavailable */ }
  }
  function resizePanel(rect, dx, dy) {
    const narrow = window.innerWidth <= 600
    const size = boundHelpSize({ width:rect.width - dx, height:rect.height + dy },
      viewport(), rect.right, narrow ? 12 : rect.top)
    if (narrow) size.width = panelSize.value?.width || 390
    else positions.value.panel = { x:rect.right-size.width, y:rect.top }
    panelSize.value = size
  }
  function onResizeDown(event) {
    if (event.button !== 0 || !panel.value) return
    event.preventDefault()
    event.currentTarget.focus({preventScroll:true})
    event.currentTarget.setPointerCapture(event.pointerId)
    resizeDrag = { id:event.pointerId, rect:panel.value.getBoundingClientRect(), x:event.clientX, y:event.clientY }
  }
  function onResizeMove(event) {
    if (resizeDrag?.id !== event.pointerId) return
    resizePanel(resizeDrag.rect, event.clientX-resizeDrag.x, event.clientY-resizeDrag.y)
  }
  function onResizeEnd(event) {
    if (resizeDrag?.id !== event.pointerId) return
    resizeDrag = null
    savePanelSize()
  }
  function onResizeKey(event) {
    const offsets = { ArrowLeft:[-24,0], ArrowRight:[24,0], ArrowUp:[0,-24], ArrowDown:[0,24] }
    if (!panel.value || !offsets[event.key]) return
    event.preventDefault()
    resizePanel(panel.value.getBoundingClientRect(), ...offsets[event.key])
    savePanelSize()
  }
  function apply() {
    frame = 0
    if (!drag || !pending || !drag.moved) return
    positions.value[drag.kind] = boundHelpPosition({ x: drag.start.x + pending.x - drag.x, y: drag.start.y + pending.y - drag.y }, viewport(), drag.size)
  }
  function down(event, kind) {
    if (event.button !== 0 || (kind === 'panel' && event.target.closest('button,input,a,select,textarea'))) return
    const element = kind === 'fab' ? fab.value : panel.value
    if (!element) return
    cancelAnimationFrame(flight)
    const rect = element.getBoundingClientRect()
    drag = { kind, x: event.clientX, y: event.clientY, start: { x: rect.left, y: rect.top }, size: { width: rect.width, height: rect.height }, moved: false }
    event.currentTarget.setPointerCapture?.(event.pointerId)
  }
  function move(event) {
    if (!drag) return
    const now = performance.now()
    const prior = pending || { x: drag.x, y: drag.y, time: now - 16 }
    const dt = Math.max(8, now - prior.time)
    drag.vx = Math.max(-1.7, Math.min(1.7, (event.clientX - prior.x) / dt))
    drag.vy = Math.max(-1.7, Math.min(1.7, (event.clientY - prior.y) / dt))
    pending = { x: event.clientX, y: event.clientY, time: now }
    if (Math.abs(pending.x - drag.x) + Math.abs(pending.y - drag.y) > 4) drag.moved = true
    if (drag.moved) dragging.value = drag.kind
    if (!frame) frame = requestAnimationFrame(apply)
  }
  function up(event) {
    cancelAnimationFrame(frame)
    if (drag?.moved) {
      apply()
      if (drag.kind === 'fab') {
        suppressUntil = performance.now() + 400
        if (event?.type === 'pointerup' && pending && performance.now() - pending.time < 100 &&
            Math.hypot(drag.vx, drag.vy) > .1) {
          toss(positions.value.fab, drag.size, drag.vx, drag.vy)
        }
      }
    }
    dragging.value = ''
    drag = pending = null; cancelAnimationFrame(frame); frame = 0
  }
  function anchorPanel(){
    cancelAnimationFrame(flight)
    positions.value.panel = null
    if (!fab.value || !panel.value || window.innerWidth <= 600) return
    positions.value.panel = placeHelpBeside(fab.value.getBoundingClientRect(),viewport(),
      {width:panel.value.offsetWidth,height:panel.value.offsetHeight})
  }
  function clampAll() {
    up()
    for (const [key, element] of [['fab', fab.value], ['panel', panel.value]]) {
      if (!positions.value[key] || !element) continue
      const rect = element.getBoundingClientRect()
      positions.value[key] = boundHelpPosition(positions.value[key], viewport(), { width: rect.width, height: rect.height })
    }
    if (window.innerWidth < 600) positions.value.panel = null
  }
  function onViewportResize() { resizeDrag = null; nextTick(clampAll) }
  onMounted(() => {
    window.addEventListener('pointermove', move, { passive: true })
    window.addEventListener('pointerup', up); window.addEventListener('pointercancel', up); window.addEventListener('resize', onViewportResize)
  })
  onUnmounted(() => {
    up(); cancelAnimationFrame(flight); window.removeEventListener('pointermove', move); window.removeEventListener('pointerup', up)
    window.removeEventListener('pointercancel', up); window.removeEventListener('resize', onViewportResize)
  })
  return { fabStyle, panelStyle, onResizeDown, onResizeMove, onResizeEnd, onResizeKey, dragging, clampAll, anchorPanel, onFabDown: event => down(event, 'fab'), onPanelDown: event => down(event, 'panel'),
    suppressClick: event => event.detail !== 0 && performance.now() < suppressUntil }
}
