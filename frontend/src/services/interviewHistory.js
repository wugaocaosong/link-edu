export function loadInterviewHistory(userId) {
  if (!userId) return []
  try {
    const saved=JSON.parse(localStorage.getItem('link-interviews:'+userId) || '[]')
    return Array.isArray(saved) ? saved.filter(item=>item && item.assessment?.total>0) : []
  } catch { return [] }
}

export function saveInterviewHistory(userId, entry) {
  if (!userId) return false
  try {
    localStorage.setItem('link-interviews:'+userId,JSON.stringify([entry,...loadInterviewHistory(userId)].slice(0,60)))
    return true
  } catch { return false }
}

export function interviewGreeting(name, history, hour = new Date().getHours()) {
  const time = hour < 6 || hour >= 22 ? '这么晚还在备考，今晚选一项短练就好。'
    : hour < 12 ? '早上好，今天想先练哪一项？'
    : hour < 18 ? '下午好，来做一轮教资面试练习吧。' : '晚上好，今晚想练结构化还是试讲？'
  const recent = latestReviewTopic(history)
  const lesson = history.find(item=>item.id==='lesson')
  const continuation = recent ? `上次「${recent.topic}」还可以补一项：${recent.assessment.missing[0].advice}。要再练一道同类题吗？`
    : lesson ? `上次练过「${lesson.title}」，今天可以试试围绕它做答辩。` : ''
  return [name ? `${name}同学，${time}` : time, continuation].filter(Boolean).join('\n\n')
}


export function latestReviewTopic(history, now = Date.now()) {
  const latest = new Map()
  for (const item of history) {
    if (item.id === 'structured' && item.topic && item.at <= now &&
        now - item.at <= 14 * 864e5 && !latest.has(item.topic)) latest.set(item.topic, item)
  }
  return [...latest.values()].filter(item => item.assessment.missing?.length)
    .sort((a,b) => a.assessment.covered/a.assessment.total - b.assessment.covered/b.assessment.total)[0]
}
