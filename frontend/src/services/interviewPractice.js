const questions = [
  '公开课上，两名学生因为分组意见不同争执起来。作为任课教师，你会怎么处理？',
  '一位家长认为你的课堂活动占用了讲知识的时间，来找你沟通。你会怎么回应？',
  '你发现一名学生近期经常独坐，课堂参与明显减少。你会怎么做？',
  '有学生认为班级规则只对自己严格，当众提出质疑。你会怎么处理？',
  '课堂临时无法使用准备好的课件，你会怎样调整教学？',
  '小组展示时，一位学生答错后被同学取笑。你会如何应对？',
]

const scenarios = [
  ['应急应变', '先制止争执，明确分组讨论规则', '分别了解分歧，给双方一个有明确分工的任务', '下一次分组时观察两人的参与，必要时个别沟通', /制止|冷静|暂停/, /分工|角色|分别了解/, /观察|跟进|个别沟通/],
  ['家校沟通', '先请家长说出具体担忧并复述确认', '用例子说明活动对应的学习目标和学生作品', '约定反馈节点，展示学生独立完成任务的证据', /倾听|担忧|复述/, /目标|作品|证据/, /反馈|约定|跟进/],
  ['学生支持', '利用课后私下沟通，了解变化的原因', '按学情安排低压力的参与机会，必要时寻求支持', '持续观察参与和情绪变化，保护学生隐私', /私下|个别|课后/, /参与|支持|帮助/, /观察|跟进|隐私/],
  ['班级管理', '平静回应学生质疑，让课堂继续', '课后核对规则是否一致，发现偏差就明确纠正', '公开澄清共同规则，后续对同类行为一致处理', /平静|继续|课后/, /核对|一致|纠正/, /澄清|规则|后续/],
  ['应急应变', '用板书或口头示范把课堂继续下去', '保留核心学习任务，调整材料与活动顺序', '用一道任务检查目标达成，课后复盘设备与预案', /板书|示范|口头/, /目标|调整|任务/, /检查|复盘|预案/],
  ['学生支持', '当即制止取笑并给答题学生留出修正空间', '引导全班讨论错误背后的思路与改法', '跟进学生感受，和全班约定反馈规则', /制止|停止|尊重/, /思路|改正|引导/, /跟进|感受|规则/],
]

const sampleAnswers = [
  '我会先请两位同学暂停争执，让其他小组继续。我听完两人的意见后，把任务拆成记录和汇报两个角色，约定下轮互换。下一次活动我会观察他们能否独立完成分工，仍有摩擦就分别沟通。',
  '我先请家长举例说明担心哪部分知识没讲清，再拿学生作品说明活动练的是哪项目标。我会约好下周反馈，给家长看学生独立完成的同类任务，必要时补上针对性练习。',
  '我会找一个不被同伴围观的时间，先用观察到的变化开启交流。经学生同意，可以从两人搭档或书面发言开始。我会观察接下来两周的参与变化，必要时按校内流程寻求支持。',
  '我会先回应“我听到你觉得规则执行不一致”，再让课堂继续。课后与学生核对具体事例，如果我的处理有偏差，就明确承认并纠正。之后向全班重申共同规则，对照同类情况检查是否一致。',
  '我会用板书保留原来课件里最关键的图示，口头说明任务。原本依赖幻灯片的环节改成两人互讲，收尾用一道独立题确认理解，课后把板书和纸笔备用方案备好。',
  '我会当场制止取笑，说明课堂可以纠正想法。然后请学生说到目前为止是怎么想的，并让同伴指出哪一步可以改。课后关心当事学生的感受，下次展示前和全班约定反馈规则。',
]

export const structuredTopics = [...new Set(scenarios.map(([topic]) => topic))]
export const defenseInterruptions = [
  '考生，请暂停。如果板书上的关键词写错了，你会怎样当场纠正并确认学生没有跟着记错？',
  '考生，请暂停。你提到的活动如果只有少数学生参与，你会先改变哪一步？',
  '考生，请暂停。现在只剩一分钟，请说清你会保留的任务和判断依据。',
]

const lessonChecks = [
  ['教学目标', /目标|能够|学会|能用/, '学生完成什么任务时，你能判断目标已经达成？'],
  ['重点与难点', /重点|难点|易错|误区/, '哪一步最容易卡住？你打算怎样帮助学生跨过这一步？'],
  ['教学环节', /导入|探究|练习|总结|迁移/, '请说清每一环节由谁做什么，以及它如何为下一环节铺垫。'],
  ['师生互动', /提问|讨论|小组|回答|反馈|合作/, '补上一个具体提问、学生可能的回答，以及你接下来怎么回应。'],
  ['学习评价', /评价|检测|检查|达成|观察|出口条/, '你会收集什么课堂证据来判断学生学会了？'],
]

const defenseChecks = [
  ['直接回应', /因为|考虑|依据|基于|理由/, '先用一句话直接回答考官，再解释你作出这个选择的理由。'],
  ['教学依据', /学生|学情|目标|任务|证据|表现/, '把理由落到具体的学生表现、教学目标或课堂证据上。'],
  ['临场调整', /如果|调整|替代|改为|改用|改进/, '交代什么情况下会调整，以及调整后的第一步。'],
]

const expressionCheck = ['课堂表达', /请你|请大家|同学们|我们来|谁能|为什么|因为/, '把一段讲解拆成一句指令和一个问题，读一遍，检查学生能否听懂要做什么。']

const defenseRounds = [
  '如果时间只剩一分钟，你会保留哪个环节？请用两三句话说明理由。',
  '你会记录哪一种学生表现，作为这节课需要改进的证据？',
]

const followups = [
  [/小组|合作|讨论/, '如果小组活动中只有少数学生发言，你会怎么调整，并判断其他学生是否学会了？'],
  [/评价|练习|检测|反馈/, '如果多数学生能做对练习，却说不清理由，你会怎么判断他们是否理解？'],
  [/导入|情境|故事/, '如果导入超时，你会压缩哪个环节？怎样保住核心学习任务？'],
]

export const interviewModules = [
  { id: 'structured', label: '结构化问答', prompt: '请像在考场一样作答。提交后，我会检查答题思路、逻辑层次和内容完整性。', placeholder: '输入你的结构化作答' },
  { id: 'lesson', label: '试讲与说课', prompt: '请注明学段、学科、课题，以及是试讲还是说课，再粘贴一段稿子。稿件较长可以分段练习。', placeholder: '输入课题和试讲或说课片段' },
  { id: 'defense', label: '答辩模拟', prompt: '请先写下试讲课题和一个具体教学设计。我会作为考官提出追问，并在你回答后反馈。', placeholder: '输入课题和你的教学设计' },
  { id: 'plan', label: '教案设计', prompt: '请写下学段、学科、课题和已有构想。可以从这五项入手：学情与目标、重点与难点、活动流程、师生互动、评价证据。', placeholder: '输入课题、学情和初步教案' },
]

export function startInterview(id, previousQuestion, { pressure = false, topic = '' } = {}) {
  const module = interviewModules.find(item => item.id === id)
  const pool = questions.map((question, index) => ({question,index})).filter(({index}) => !topic || scenarios[index][0] === topic)
  const eligible = pool.length ? pool : questions.map((question,index)=>({question,index}))
  const alternatives = eligible.filter(({question})=>question !== previousQuestion)
  const candidates = alternatives.length ? alternatives : eligible
  const picked = id === 'structured' ? candidates[Math.floor(Math.random() * candidates.length)] : null
  const question = picked?.question || ''
  return { id, question, topic: picked ? scenarios[picked.index][0] : '', pressure, stage: 'initial',
    message: [pressure && picked ? '压力面试｜考生，请直接作答。答完后我会针对一个薄弱处追问。' : '', question, module.prompt].filter(Boolean).join('\n\n') }
}

const stuckAnswer = /^(?:(?:我)?(?:不知道(?:怎么(?:答|回答|写|说))?|不会(?:答|回答|写|说)?|卡住了?|卡壳了?|没思路|想不出来)|给(?:我)?(?:点|个)?提示)[\s。！？!?]*$/

function feedback(text, checks) {
  return checks.map(([label, pattern, advice]) => {
    const clue = text.match(pattern)?.[0]
    const evidence = clue ? `稿中提到“${clue}”，请把它落实到具体做法。 ` : '暂未识别到明确线索。 '
    return `${label}｜${evidence}${advice}`
  }).join('\n')
}

function feedbackReaction(text, checks) {
  return checks.every(([, pattern]) => pattern.test(text)) ? 'cheer' : 'encourage'
}

export function respondToInterview(practice, text) {
  if (stuckAnswer.test(text.trim())) {
    const hint = {
      structured: '先想想题目里最需要你处理的是什么，再写一句你会当场说的话。',
      lesson: '先写一个你会问学生的问题，再想一个学生可能给出的回答。',
      defense: '先用一句话说你的选择，再想想它能帮助学生完成什么。',
      plan: '先写下这节课结束时，你希望学生能独立完成的一件事。',
    }[practice.id]
    return { ...practice, assessment:null, reaction: 'encourage', message: hint }
  }
  if (practice.id === 'structured') {
    const index = Math.max(0,questions.indexOf(practice.question))
    const [, ...parts] = scenarios[index]
    const checks = parts.slice(0,3).map((point,index)=>[`要点 ${index+1}`,parts[index+3],point])
    if (practice.pressure && practice.stage==='initial') {
      const missing = checks.find(([,pattern])=>!pattern.test(text)) || checks[2]
      return {...practice,stage:'followup',reaction:'', firstAnswer:text,message:`考官追问｜考生，请具体说明这一步：${missing[2]}。请说出你会做的第一件事，以及如何判断它奏效。`}
    }
    const evidence = coverage([practice.firstAnswer,text].filter(Boolean).join('\n'),checks)
    return {...practice,stage:'complete',firstAnswer:'',assessment:evidence,reaction:evidence.missing.length?'encourage':'cheer',
      message:`采分点自查｜${evidence.covered}/${evidence.total} 项识别到线索\n${feedback([practice.firstAnswer,text].filter(Boolean).join('\n'),checks)}\n\n考官视角｜我会听你是否交代了处理优先级、具体行动和后续证据。先把最薄弱的一步说成能直接执行的一句话。\n\n参考作答｜${sampleAnswers[index]}`}
  }

  if (practice.id === 'defense' && practice.stage === 'initial') {
    const question = followups.find(([pattern]) => pattern.test(text))?.[1]
      ?? '你为什么选择这一教学安排？如果学生没有达到预期，你会依据什么调整？'
    return { ...practice, stage: 'answer', round: 0, activeQuestion:question, reaction: '', message: `考官追问｜${question}\n\n请先正面回应，再用教学依据说明你的选择。` }
  }

  if (practice.id === 'defense') {
    if (practice.stage === 'complete') return {...practice,assessment:null,reaction:'',message:'这一轮答辩已结束。点击「答辩模拟」可开启新一轮。'}
    const round = practice.round ?? 0
    const nextQuestion = defenseRounds[round]
    const interruptionFeedback = practice.interrupted && practice.activeQuestion
      ? '\n\n临场回应｜回看打断后的第一句，检查是否先回应刚才的新问题，再补充具体措施。'
      : ''
    const nextStep = nextQuestion
      ? `考官继续追问｜${nextQuestion}`
      : '本轮追问完成。请回看三次回答，选一句理由重写。也可以点击「答辩模拟」开始新一轮。'
    return { ...practice, stage:nextQuestion?'answer':'complete', round: round + 1, activeQuestion:nextQuestion||'', assessment:coverage(text,defenseChecks), reaction: feedbackReaction(text, defenseChecks), message: `${feedback(text, defenseChecks)}${interruptionFeedback}\n\n${nextStep}` }
  }

  const checks = {
    lesson: [...lessonChecks, expressionCheck],
    plan: lessonChecks,
  }[practice.id]
  const next = {
    lesson: /说课/.test(text) ? '请选一个教学环节，补充为什么这样安排，以及它怎样回应学情。' : '请选一个教学环节，用课堂上会说的话重写你的提问和反馈。',
    plan: '请先补上一个可观察的学习目标，再写一个能检验这个目标的课堂任务。',
  }[practice.id]

  return { ...practice, stage: 'answer', assessment:coverage(text,checks), reaction: feedbackReaction(text, checks), message: `${feedback(text, checks)}\n\n${next}` }
}


function coverage(text, checks) {
  const missing = checks.filter(([,pattern])=>!pattern.test(text)).map(([label,,advice])=>({label,advice}))
  return {covered:checks.length-missing.length,total:checks.length,missing}
}

export function lessonPlanFramework(input) {
  const [topic, stage, subject, ...keywords] = input.split(/[；;，,、\n]+/u).map(part=>part.trim()).filter(Boolean)
  const focus = keywords.length ? keywords.join('、') : topic
  return `《${topic}》教案框架${stage || subject ? `｜${[stage,subject].filter(Boolean).join(' · ')}` : ''}

教学目标｜学生能用自己的话说明“${focus}”中的核心概念，并独立完成一项应用任务，说明自己的依据。
重点｜理解“${focus}”的关键关系，并用具体实例解释。
难点｜辨析容易混淆的情况。备课时补入一组贴近学情的正反例。
教学过程｜用一个具体情境引出问题 → 示范一种解题或探究方式 → 学生独立尝试、交流理由 → 对比不同答案并修正 → 换一个情境独立应用。
评价证据｜收集一份学生作答和一句理由。若学生能做对但说不清依据，追加一道反例辨析题。
课后完善｜写出导入的具体提问、课堂任务和可接受答案，按学段调整难度。`
}
