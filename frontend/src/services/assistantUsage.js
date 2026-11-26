export function yuan(value) {
  return Number.isFinite(value) ? `¥${value.toFixed(6).replace(/\.?0+$/u,'')}` : '—'
}

export function usageLabel(usage) {
  if(!usage)return ''
  const pending=usage.pending_cny>0 ? ` · 待结算预留 ${yuan(usage.pending_cny)}` : ''
  return `本次已结算 ${yuan(usage.charged_cny)}${pending} · 剩余 ${yuan(usage.remaining_cny)}`
}
