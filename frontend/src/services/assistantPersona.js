export function replyPose(text, { tier, failed = false } = {}) {
  if (failed || tier === 'unknown' || /^(?:抱歉[，,。 ]*)?(?:我不知道|暂时无法|未能完成|连接失败|操作失败)/u.test(text)) return 'thinking'
  if (/别着急|别灰心|不用自责|先别担心|你已经做得|慢慢来|给自己一点时间|卡住很正常|辛苦了/u.test(text)) return 'cheer'
  if (/重点|关键(?:是|在于|步骤)|记下|记住|要点|核心(?:是|在于)|(?:^|\n)\s*1[.、．]/u.test(text)) return 'notes'
  return ''
}

export function motionEnabled(preference, reduced) {
  return preference !== false && !reduced
}

const states = {
  notes: 'formal', thinking: 'thinking', sleep: 'nod', speaking: 'speaking',
  cheer: 'happy', encourage: 'presenting', invite: 'presenting', startled: 'error', brace: 'error',
}

export function characterState(pose, { animated = true, quiet = false, role, look = 0, lookY = 0 } = {}) {
  if (!animated || quiet) return 'idle'
  if (pose === 'curious') {
    if (Math.abs(lookY) > Math.max(.3, Math.abs(look))) return lookY < 0 ? 'thinking' : 'nod'
    return Math.abs(look) > .25 ? 'turn' : 'formal'
  }
  return states[pose] || (role === 'examiner' ? 'formal' : 'idle')
}
