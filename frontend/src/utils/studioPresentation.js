// Presentation mappings only: titles, scores and earned states still come from the service.
export function resourceCoverIndex(item) {
  const category = item?.category || ''
  const title = item?.title || ''
  if (/档案|成长/.test(category + title)) return 3
  if (/报告|评课|评分/.test(category + title)) return 2
  if (/导入/.test(title)) return 5
  if (/素材|提问|课题/.test(category + title)) return 1
  if (/10|分钟|清单/.test(title + category)) return 4
  return 0
}

export function badgeArtIndex(item) {
  const names = ['初次上台', '勤练不辍', '完整收束', '提问达人', '高分片段', '有迹可循']
  return Math.max(0, names.indexOf(item?.name))
}

export function matchesResource(item, query) {
  const needle = String(query || '').trim().toLocaleLowerCase()
  return !needle || [item.title, item.description, item.category].some(value => String(value || '').toLocaleLowerCase().includes(needle))
}

export function calendarMonths(cells) {
  return [...new Set(cells.map(cell => String(cell.date || '').slice(0, 7)).filter(month => /^\d{4}-\d{2}$/.test(month)))].sort()
}

export function monthCalendar(cells, month) {
  if (!/^\d{4}-\d{2}$/.test(month || '')) return []
  const [year, number] = month.split('-').map(Number)
  if (number < 1 || number > 12) return []
  const known = new Map(cells.map(cell => [cell.date, cell]))
  const start = (new Date(year, number - 1, 1).getDay() + 6) % 7
  const count = new Date(year, number, 0).getDate()
  const length = Math.ceil((start + count) / 7) * 7
  return Array.from({ length }, (_, index) => {
    const day = index - start + 1
    if (day < 1 || day > count) return { key: `pad-${index}`, placeholder: true }
    const date = `${month}-${String(day).padStart(2, '0')}`
    const cell = known.get(date)
    return { ...cell, key: date, date, dayLabel: String(day), placeholder: false, unavailable: !cell }
  })
}
