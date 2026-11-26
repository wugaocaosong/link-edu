import { libraryResources } from '../data/libraryResources.js'

const pages = [
  ['/resources', '小书架', /小?书架|资源库|本页资源/, '小书架收录教资面试大纲、试讲与教案素材、观摩案例等。用搜索框查找标题或关键词，也可以按场景、模块和篇幅筛选，点卡片打开对应资料。'],
  ['/ai-review', '档案袋', /档案袋?|AI\s*评课|评课报告/, '档案袋用于回看训练记录和 AI 评课。进入一份报告后，可以查看综合反馈、证据和下一步建议。具体结论以你打开的报告为准。'],
  ['/dashboard', '标签墙', /工作表现墙|表现墙|标签墙|工作台|训练日志/, '标签墙展示近期训练、继续训练、评课反馈与成长轨迹。点击对应便签可展开详情，也可以用「新增便签」记下待办。'],
  ['/courses', '办公桌', /办公桌|课程中心|选课/, '办公桌是课程入口。可以浏览或搜索课程，查看课程对应的练习内容，再进入训练。'],
  ['/classroom', '演绎厅', /演绎厅|模拟课堂|课前准备/, '演绎厅用于模拟授课。先完成课前准备和设备检查，再开始训练。授课结束后可在档案袋回看评课结果。'],
  ['/knowledge', '知识库', /知识库|检索与语料/, '知识库用于检索平台已收录的教学资料。输入教学主题或关键词，再打开检索结果核对来源。'],
  ['/profile', '个人中心', /个人中心|我的设置|留言板/, '右上角头像菜单可以进入个人中心、设置或留言板。'],
  ['/adaptive', '自适应学习', /自适应学习|学习路径/, '这里展示自适应学习路径。请根据当前页面给出的诊断和任务选择下一项练习。'],
]

export function platformPageLabel(path) {
  return pages.find(([url]) => path === url)?.[1] || ''
}

function getResourceResults(question, path) {
  const normalize = value => value.replace(/[\s“”《》「」]/gu, '').toLowerCase()
  const text = normalize(question)
  const named = libraryResources.filter(item => item.title.length >= 4 && text.includes(normalize(item.title)))
  if (named.length) return named.sort((a, b) => b.title.length - a.title.length).slice(0, 3)
  const asksShelf = path === '/resources' || pages[0][2].test(question)
  const topic = question.match(/(?:有?关于|有关|和|找|搜|推荐)(.{2,35}?)(?:相关|的资料|的资源|的教案|的书|有什么|[？?。]|$)/u)?.[1]?.replace(/^(?:一下|一份|一本|一些|一套)/u, '').trim()
  if (!asksShelf || !topic || topic.length < 2) return []
  const keyword = normalize(topic)
  return libraryResources.filter(item => [item.title,item.description,item.category,item.stage,item.coverTitle]
    .some(value => value && normalize(value).includes(keyword))).slice(0, 4)
}

export function answerPlatformQuestion(question, path, visible = {}, enabled = () => true) {
  const greeting = question.trim().replace(/[！!。．.？?～~，,\s]+$/u, '').toLowerCase()
  if (/^(?:hi+|hey+|hello|你好(?:呀|啊|哦)?|您好|嗨|哈[喽啰]|在吗|早上好|下午好|晚上好|阿贝(?:贝)?(?:老师)?[，, ]*(?:你好|在吗)?)$/u.test(greeting)) {
    const page = platformPageLabel(path)
    return {
      text: page === '小书架'
        ? '你好呀，我在这儿。你可以问我“小书架里有没有关于分数的资料？”，也可以选一项教资面试练习。'
        : `你好呀，我在这儿。${page ? `想了解「${page}」的哪个功能？` : '想了解哪个平台功能？'}也可以选一项教资面试练习。`,
    }
  }

  const resources = getResourceResults(question, path)
  if (resources.length) {
    return {
      text: resources.map(item => [item.title, item.description].filter(Boolean).join('｜')).join('\n\n'),
      sources: resources.map(item => ({ id:item.id, title:item.title, source:'小书架目录', to:{path:'/resources',query:{q:item.title}} })),
    }
  }
  const current = pages.find(([url]) => path === url)
  const names = pages.filter(([url, , pattern]) => enabled(url) && pattern.test(question))
  const explicitPage = names.length > 0
  const asksHere = /这(?:个|一)?(?:页面|界面|页|里|张报告|份报告|面墙|个功能)|当前(?:页面|这份报告)|本页/u.test(question)
  const chosen = explicitPage ? names : asksHere && current ? [current] : []
  if (!chosen.length && path !== '/dashboard' && path !== '/ai-review') return null

  const concerns = url => chosen.length ? chosen.some(page => page[0] === url) : path === url
  if (path === '/dashboard' && concerns('/dashboard') && /(?:本周|这周).*(?:多少|几次|多久|几分钟)|训练了(?:多少|几次|多久)/u.test(question)) {
    return {text:visible.weekly || '当前页面还没有显示本周训练次数和时长。请打开标签墙的「本周训练」查看。',sources:[{id:'dashboard-weekly',title:'本周训练',source:'当前页面',to:'/dashboard'}]}
  }
  if (path === '/ai-review' && concerns('/ai-review') && /总结|结论|综合判断|主要问题|建议|怎么改|下一步/u.test(question)) {
    const wantsAdvice = /建议|怎么改|下一步/u.test(question)
    const text = wantsAdvice ? visible.reportAdvice : /主要问题/u.test(question) ? visible.reportProblems : visible.reportSummary
    if (text) return {text,sources:[{id:'current-report',title:'当前报告',source:'当前页面'}]}
    return {text:'当前页面没有显示对应的报告内容。请先在档案袋打开一份报告；看综合判断或主要问题时，可以展开「查看全部详情」。',sources:[{id:'report',title:'档案袋',to:'/ai-review'}]}
  }
  if (!chosen.length) return null
  if (explicitPage && !asksHere && !/在哪|哪里|怎么(?:用|找|看|打开|进去|进入|切换)|如何|有什么|是什么|做什么|能干嘛|介绍|有没有|资料|界面|页面|报告|档案|表现墙|标签墙|书架/u.test(question)) return null
  const asksLocation = /在哪|哪里|怎么(?:找|打开|进去|进入)|入口/u.test(question)
  const asksPersonal = /(?:我(?:的|之前|最近|本周)|这份|这张).*(?:报告|记录|评分|得分|反馈)|得了多少|评了多少|本周.*(?:多少|几次|多久|几分钟)/u.test(question)
  const sections = chosen.map(([url,label,,description]) => {
    if (asksLocation) return `点下方「打开${label}」进入。`
    if (asksPersonal && ['/dashboard','/ai-review'].includes(url)) return `打开${label}查看对应记录，再问我当前页面显示的内容。`
    return description
  })
  return {
    text:sections.join('\n\n'),
    sources:chosen.map(([url,label])=>({id:url,title:label,source:'平台功能说明',to:url})),
  }
}
