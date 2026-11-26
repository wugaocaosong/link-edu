import { libraryResources } from '../data/libraryResources.js'

export function isToolRequest(text) {
  const query=text.trim().replace(/[。！!？?]+$/u,'')
  if(/^(?:请|帮我|请帮我)?打开/u.test(query))
    return !/打开\s*(?:档案袋|小书架|办公桌|标签墙|工作台|演绎厅|知识库|个人中心|设置|训练日志)$/u.test(query)
  return /^(?:请|帮我|请帮我)?(?:(?:把|将)?(?:(?:刚才|刚刚|当前|上)(?:的)?(?:这|那|一)?(?:道)?题|[这那]道题).{0,12}(?:错题本|错题库)|加入错题本|(?:生成|制定|创建|更新|调整).{0,14}(?:备考计划|复习计划)|(?:总结|概括|归纳)(?:一下)?(?:当前|本页|这份|这篇).{0,20}|(?:给我出|出|来)(?:一|下)?(?:道)?题|考考我|今天练什么|继续练习)$/u.test(query)
}

export function toolResourceRoute(card) {
  if(card?.name!=='open_resource'||card.status!=='ok')return null
  const item=libraryResources.find(item=>item.id===card.resource?.id)
  return item ? {path:'/resources',query:{resource:item.id}} : null
}
