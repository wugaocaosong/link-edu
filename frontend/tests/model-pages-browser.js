// Dev-only visual acceptance. Real page components, in-memory identity, no API/device writes.
import {createApp} from 'vue'
import {createPinia} from 'pinia'
import {createRouter,createMemoryHistory} from 'vue-router'
import App from '../src/App.vue'
import AppShell from '../src/layouts/AppShell.vue'
import {useAuthStore} from '../src/stores/auth.js'
import {api} from '../src/services/api.js'
import '../src/styles.css'
import '../src/ambient-effects.css'
import '../src/functional-ui.css'
import '../src/themes/academy.css'
import '../src/themes/studio.css'
import '../src/themes/compact.css'
import '../src/themes/workspace.css'
import '../src/themes/warm-studio.css'
import { initializeTheme } from '../src/utils/uiTheme.js'
import { initializeUiVersion } from '../src/utils/uiVersion.js'
import { classroomEntry } from '../src/services/classroomEntry.js'
initializeTheme(); initializeUiVersion()
const fixtureTitles = ['导入技能','板书板画技能','演示技能','讲解技能','提问技能','强化技能','结束技能','组织技能','变化技能','综合模拟授课','综合教资试讲']
let fixtureCourses = fixtureTitles.map((title,i) => ({ id:i+1,title,stage:i<9 ? '专项0'+(i+1) : '综合'+(i+1),category:i<9?'专项':'综合',description:'课程详情示例',lesson_count:8,status:i===3?'in_progress':'not_started',status_label:i===3?'进行中':'未开始',progress_percent:i===3?38:0,outline:'教学目标\n课堂练习',source:'界面验收夹具' }))
let courseFailure = false, dashboardOverview = {}, ragFailure = false, ragDocuments = []
let fixtureProfile = {}, fixtureGrowth = {points:[],records:[],heatmap:[],milestones:[],summaries:[],journals:[]}, fixtureResources = [], fixtureFailures = {}, fixtureWrites = false
window.__studioFixture = { setOverview(value) { dashboardOverview = value }, setCourses(value) { fixtureCourses=value }, setCourseFailure(value) { courseFailure=value }, setRagFailure(value) { ragFailure=value }, setRagDocuments(value) { ragDocuments=value } }
Object.assign(window.__studioFixture, { setProfile(value) { fixtureProfile = value }, setGrowth(value) { fixtureGrowth = value }, setResources(value) { fixtureResources = value }, setFailures(value) { fixtureFailures = value }, allowMemoryWrites(value) { fixtureWrites = value }, writes: [] })
const pinia=createPinia(), auth=useAuthStore(pinia)
auth.$patch({token:'',user:{id:-1,name:'界面验收',role_label:'模拟数据'},hydrated:true,sessionStatus:'authenticated'})
navigator.mediaDevices.getUserMedia=async()=>{throw new Error('验收页面不访问真实设备')}
const service={configured:true,pricing_confirmed:true,status:'available',provider:'mock',model:'ui-fixture'}
api.defaults.adapter=async config=>{
  const key=config.url.split('?')[0]
  if (fixtureFailures[key]) throw {config,response:{status:503,data:{message:'验收：服务暂时不可用'}}}
  if(config.method!=='get') {
    if (!fixtureWrites) throw{config,response:{status:503,data:{message:'界面验收不写入数据'}}}
    const body = typeof config.data === 'string' ? JSON.parse(config.data) : config.data
    window.__studioFixture.writes.push({ key, body })
    await new Promise(resolve => setTimeout(resolve, 250))
    let data = {}
    if (key === '/profile') { fixtureProfile = { ...fixtureProfile, ...body }; data = fixtureProfile }
    else if (key === '/journals') data = {item:{id:-1,...body}}
    else throw{config,response:{status:503,data:{message:'此操作不在内存验收范围'}}}
    return{config,status:200,statusText:'OK',headers:{},data}
  }
  if (key.startsWith('/rag/') && ragFailure) throw {config,response:{status:503,data:{message:'知识库连接暂时不可用'}}}
  let data={items:[]}
  if (key==='/rag/status') data={indexed_chunks:0,can_manage:false,categories:{},hybrid_enabled:true,rerank_enabled:false}
  if (key==='/rag/documents') data={items:ragDocuments}
  if(key==='/classroom/capabilities')data={pose_assets:true,services:{dialogue:service,asr:service,tts:service,vision:service},budget:{pricing_confirmed:true,stopped:false,warning:false}}
  if(key==='/courses') { if(courseFailure) throw {config,response:{status:503,data:{message:'课程加载失败'}}}; data={items:fixtureCourses} }
  if(key==='/dashboard/overview')data=dashboardOverview
  if(key==='/growth')data=fixtureGrowth
  if(key==='/profile')data=fixtureProfile
  if(key==='/resources')data={items:fixtureResources}
  return{config,status:200,statusText:'OK',headers:{},data}
}
const router=createRouter({history:createMemoryHistory(),routes:[{path:'/',component:AppShell,children:[
  {path:'training',redirect:classroomEntry},
  {path:'profile',component:()=>import('../src/views/ProfileView.vue')},
  {path:'dashboard',component:()=>import('../src/views/DashboardView.vue')},
  {path:'knowledge',component:()=>import('../src/views/RagKnowledgeView.vue')},
  {path:'classroom',component:()=>import('../src/views/ClassroomView.vue'),meta:{crumb:'教学训练 / 模拟课堂'}},
  {path:'courses',component:()=>import('../src/views/CoursesView.vue'),meta:{crumb:'课程中心 / 选课'}},
  {path:'resources',component:()=>import('../src/views/ResourcesView.vue'),meta:{crumb:'资源库 / 教案与素材'}},
  {path:'growth',component:()=>import('../src/views/GrowthView.vue'),meta:{crumb:'成长档案 / 轨迹'}},
  {path:'ai-review',component:()=>import('../src/views/ClassroomReviewView.vue'),meta:{crumb:'AI 评课 / 报告'}},
  {path:':pathMatch(.*)*',redirect:'/classroom'},
]}]})
window.__studioFixture.router = router
await router.push(new URLSearchParams(location.search).get('page') || '/classroom')
createApp(App).use(pinia).use(router).mount('#app')
