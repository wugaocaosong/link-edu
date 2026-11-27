<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import AssistantAccount from '../components/AssistantAccount.vue'
import ClassroomDialog from '../components/ClassroomDialog.vue'
import StudioArt from '../components/StudioArt.vue'
import { api } from '../services/api.js'
import { yuan } from '../services/assistantUsage.js'
import { useAuthStore } from '../stores/auth.js'
import { badgeArtIndex } from '../utils/studioPresentation.js'

const auth = useAuthStore()
const profile = ref(null), quota = ref(null), drawer = ref('')
const profileLoading = ref(false), profileError = ref(false)
const controller = new AbortController()
const name = computed(() => auth.user?.name || '临客')
const role = computed(() => auth.user?.role_label || (auth.user?.role === 'teacher' ? '指导教师' : '师范生'))
const progress = computed(() => Math.max(0, Math.min(100, Number(profile.value?.xp_percent) || 0)))
const badges = computed(() => profile.value?.badges ?? [])
const earned = computed(() => badges.value.filter(item => item.earned).length)
const level = computed(() => profile.value?.level ?? null)
const milestones = computed(() => {
 const start = Math.max(1, Math.min(7, (level.value || 1) - 1))
 return [start, start + 1, start + 2]
})
const plans = [
 { key: 'basic', title: '基础会员', items: ['公共资料免费', '模拟课堂免费体验', '基础证据报告与复练'] },
 { key: 'advanced', title: '进阶会员', items: ['高阶教研资源', '更多复练任务', '报告 PDF 导出', '完整多模态回溯'] },
 { key: 'premium', title: '高级会员', items: ['权益尚未公布', '原型阶段暂未开放'] },
]
const titles = { quota: '阿贝贝额度与用量', advanced: '进阶会员 · 尚未开放', premium: '高级会员 · 尚未开放', orders: '我的订单', redeem: '兑换码与优惠券' }

async function refreshProfile() {
 const uid = auth.user?.id
 if (!uid || profileLoading.value) return
 profileLoading.value = true
 profileError.value = false
 try {
  const { data } = await api.get('/profile', { signal: controller.signal, timeout: 8000, skipBusy: true })
  if (uid === auth.user?.id && !controller.signal.aborted) profile.value = data
 } catch {
  if (uid === auth.user?.id && !controller.signal.aborted) profileError.value = true
 } finally {
  profileLoading.value = false
  if (uid !== auth.user?.id && !controller.signal.aborted) void refreshProfile()
 }
}

watch(() => auth.user?.id, () => {
 profile.value = null
 profileError.value = false
 void refreshProfile()
})
onMounted(() => {
 const options = { signal: controller.signal, timeout: 8000, skipBusy: true }
 void refreshProfile()
 window.addEventListener('focus', refreshProfile)
 api.get('/assistant/quota', options).then(({ data }) => {
  if (Number.isFinite(data?.remaining_cny)) quota.value = data
 }).catch(() => {})
})
onUnmounted(() => {
 window.removeEventListener('focus', refreshProfile)
 controller.abort()
})
</script>

<template>
 <div class="membership-page">
  <div class="membership-desk">
   <h1 id="membership-title">会员中心</h1>
   <section class="membership-identity" aria-label="当前学习账户">
    <div class="membership-avatar" aria-hidden="true">{{ name.slice(0, 1) }}</div>
    <div class="membership-identity__body">
     <div class="membership-identity__name"><strong>{{ name }} · {{ role }}</strong><span>✦ 基础会员</span></div>
     <p>{{ profile?.level_label || '基础训练免费开放' }}</p>
     <div v-if="profile" class="membership-progress" role="progressbar" aria-label="当前成长进度" :aria-valuenow="progress">
      <i :style="{ width: progress + '%' }"></i><span>成长值 {{ profile.xp ?? 0 }}</span>
     </div>
    </div>
    <span class="membership-identity__validity">基础版 · 免费开放</span>
   </section>

   <div class="membership-main-grid">
   <section class="membership-book" aria-labelledby="membership-book-title">
    <div class="membership-book__cover">
     <div class="membership-book__heading">
      <img class="membership-laurel" src="/assets/membership/laurel.png" alt="">
      <div>
       <h2 id="membership-book-title">基础会员</h2>
       <p>{{ profile?.level_label || '当前学习账户' }}</p>
      </div>
     </div>
     <div class="membership-book__footer">
      <ul class="membership-book__facts">
       <li><span aria-hidden="true">◈</span> 阿贝贝体验额度 <strong>{{ quota ? (quota.unlimited?'不限':yuan(quota.remaining_cny)) : '—' }}</strong></li>
       <li><span aria-hidden="true">▣</span> 公共资料免费下载</li>
       <li><span aria-hidden="true">▤</span> 模拟课堂免费体验</li>
       <li><span aria-hidden="true">✦</span> 基础证据报告与复练</li>
      </ul>
      <button class="membership-gold" type="button" @click="drawer='advanced'">查看进阶权益</button>
     </div>
    </div>
   </section>

   <section class="membership-tiers" aria-label="会员套餐对比">
    <article v-for="plan in plans" :key="plan.key" class="membership-tier" :class="'membership-tier--'+plan.key">
     <span v-if="plan.key==='basic'" class="membership-tier__current">当前套餐</span>
     <h2>{{ plan.title }}</h2>
     <ul><li v-for="item in plan.items" :key="item">{{ item }}</li></ul>
     <button v-if="plan.key!=='basic'" class="membership-gold" type="button" @click="drawer=plan.key">未开放 · 查看</button>
    </article>
   </section>

   <section class="membership-growth" aria-labelledby="membership-growth-title">
    <h2 id="membership-growth-title">我的成长等级</h2>
    <template v-if="profile">
     <div class="membership-growth__track">
      <div><strong>Lv.{{ level }}</strong><span>当前等级</span></div>
      <div class="membership-level-medal is-current" aria-hidden="true">Lv.{{ level }}</div>
      <div><strong>{{ level < 9 ? 'Lv.' + (level + 1) : '已达上限' }}</strong><span>成长目标</span></div>
     </div>
     <p class="membership-growth__hint"><span>成长值 {{ profile.xp ?? 0 }}</span><span>{{ profile.next_hint }}</span></p>
     <div class="membership-progress" role="progressbar" aria-label="当前等级成长进度" :aria-valuenow="progress"><i :style="{ width: progress + '%' }"></i></div>
     <div class="membership-level-shelf" aria-label="等级解锁状态">
      <span v-for="step in milestones" :key="step" class="membership-level-medal" :class="{ 'is-current': step === level, 'is-locked': step > level }">
       Lv.{{ step }} <small>{{ step > level ? '未解锁' : step === level ? '当前' : '已解锁' }}</small>
      </span>
     </div>
    </template>
    <p v-else role="status">{{ profileError?'暂时无法读取成长等级。':'正在读取成长等级…' }}</p>
   </section>

   <section class="membership-records" aria-labelledby="membership-records-title">
    <h2 id="membership-records-title">会员记录</h2>
    <div class="membership-shortcuts">
     <button type="button" @click="drawer='quota'">
      <span class="membership-record-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 6h16v13H4zM4 9h16M8 15h3m4-2h1m-1 3h1" /></svg></span>
      <span class="membership-record-label"><strong>阿贝贝额度与用量</strong><small>{{ quota ? (quota.unlimited?'demo 内测账号 · 单人额度不限':'剩余 ' + yuan(quota.remaining_cny)) : '查看体验金和使用明细' }}</small></span>
      <b aria-hidden="true">›</b>
     </button>
     <button type="button" @click="drawer='orders'">
      <span class="membership-record-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6m-6 4h6" /></svg></span>
      <span class="membership-record-label"><strong>我的订单</strong><small>查看订单记录</small></span>
      <b aria-hidden="true">›</b>
     </button>
     <button type="button" @click="drawer='redeem'">
      <span class="membership-record-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 7h16v3a2 2 0 0 0 0 4v3H4v-3a2 2 0 0 0 0-4zM13 8v2m0 2v1m0 2v1" /></svg></span>
      <span class="membership-record-label"><strong>兑换码与优惠券</strong><small>暂未开放</small></span>
      <b aria-hidden="true">›</b>
     </button>
    </div>
   </section>
   </div>

   <section class="membership-bottom" aria-label="成就徽章">
    <section class="membership-badges" aria-labelledby="membership-badges-title">
     <header>
      <div><h2 id="membership-badges-title">我的徽章墙</h2><p v-if="profile">已解锁 {{ earned }} / {{ badges.length }}</p></div>
      <RouterLink to="/profile">个人中心 <span aria-hidden="true">›</span></RouterLink>
     </header>
     <ul v-if="badges.length" class="membership-badge-grid">
      <li v-for="badge in badges" :key="badge.id" class="membership-badge-slot" :class="{ 'is-earned': badge.earned }">
       <div class="membership-medal">
        <StudioArt v-if="badge.earned" kind="badge" :index="badgeArtIndex(badge)" />
        <svg v-else viewBox="0 0 24 24" aria-hidden="true"><path d="M7.5 10V7a4.5 4.5 0 0 1 9 0v3M6 10h12a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-8a1 1 0 0 1 1-1Zm6 4v2" /></svg>
       </div>
       <strong>{{ badge.name }}</strong>
       <span class="membership-badge-state">{{ badge.earned ? '已解锁' : '未解锁' }}</span>
       <p>{{ badge.hint }}</p>
      </li>
     </ul>
     <p v-else class="membership-badge-empty" role="status">
      {{ profileLoading?'正在读取成长档案…':profileError?'暂时读不到徽章记录。':'没有可显示的徽章记录。' }}
      <button v-if="profileError" type="button" @click="refreshProfile">重试</button>
     </p>
    </section>
   </section>
  </div>

  <ClassroomDialog :model-value="!!drawer" :title="titles[drawer] || '会员中心'" @update:model-value="value => { if (!value) drawer='' }">
   <template v-if="drawer==='quota'"><AssistantAccount :key="auth.user?.id" /></template>
   <template v-else-if="drawer==='advanced'">
    <p>进阶会员暂未开放，不收费。高阶教研资源、报告 PDF 导出及完整多模态回溯仅作权益预览。</p>
    <button type="button" class="membership-gold" @click="drawer='quota'">查看额度与用量</button>
   </template>
   <template v-else-if="drawer==='orders'">
    <p>免费体验阶段没有付费订单。模型调用记录可以在「额度与用量」查看。</p>
    <button type="button" class="membership-gold" @click="drawer='quota'">查看额度与用量</button>
   </template>
   <p v-else-if="drawer==='premium'">高级会员为预留展示位，当前不开放购买，也没有已生效的权益。</p>
   <p v-else>兑换功能暂未开放。注册赠送的虚拟体验金不可充值或提现。</p>
  </ClassroomDialog>
 </div>
</template>

<style scoped>
.membership-page {
 --member-surface:#fff1da; --member-ink:#382319; --member-muted:#665043;
 --member-accent:#784324; --member-tint:#f2d7ab; --member-line:#c79d76;
 min-height:100%; color:#fff6ea; overflow:auto;
 background:#efab79 url('/assets/membership/sunlit-wall.png') center 68% / cover no-repeat;
}
.membership-desk { box-sizing:border-box; width:100%; margin:0 auto; padding:clamp(18px,3.2vw,54px) clamp(18px,3.6vw,64px) 28px; }
.membership-page h1,.membership-book h2,.membership-badges strong { font-family:"Songti SC","STSong","SimSun",serif; }
.membership-page h1 { margin:0 0 12px; color:#43281c; font-size:clamp(22px,2vw,33px); line-height:1.1; }
.membership-identity {
 position:relative; display:flex; align-items:flex-start; gap:clamp(12px,1.5vw,26px); padding:clamp(14px,1.55vw,26px) clamp(17px,2.05vw,38px);
 color:#3d251b; background:#f4dfc4 url('/assets/membership/parchment.png') center / cover;
 border:2px solid #f7e7cf; border-radius:16px; box-shadow:0 4px 5px #472c2070,inset 0 0 14px #aa724544;
}
.membership-identity:after { content:""; position:absolute; inset:7px; border:1px dashed #bd91686e; border-radius:10px; pointer-events:none; }
.membership-avatar { display:grid; place-items:center; flex:none; width:clamp(51px,5.05vw,92px); aspect-ratio:1; border:3px solid #fff1db; border-radius:50%; color:#fff; background:#875dab; font:700 clamp(25px,2.8vw,47px)/1 "Songti SC","SimSun",serif; box-shadow:0 3px 6px #4a294e65; }
.membership-identity__body { flex:1; min-width:0; }
.membership-identity__validity { align-self:flex-end; color:#5c3c29; font-size:13px; white-space:nowrap; }
.membership-identity__name { display:flex; flex-wrap:wrap; align-items:center; gap:8px 13px; }
.membership-identity__name strong { font:700 clamp(18px,1.55vw,29px)/1.3 "Songti SC","SimSun",serif; }
.membership-identity__name span { padding:1px 7px; border:1px solid #b6966f; color:#60391f; background:#f0d7b0; border-radius:99px; font-size:11px; }
.membership-identity p { margin:5px 0 11px; font-size:clamp(13px,1.1vw,19px); }
.membership-progress { position:relative; min-height:25px; overflow:hidden; border:1px solid #80513655; border-radius:99px; background:#dfbb9178; }
.membership-progress i { position:absolute; inset:0 auto 0 0; background:linear-gradient(100deg,#a66b42,#e5a766); border-radius:inherit; }
.membership-progress span { position:relative; z-index:1; display:inline-block; margin-left:8px; padding:1px 6px; color:#392318; font-size:13px; font-weight:700; }
.membership-main-grid { display:grid; grid-template-columns:minmax(0,.95fr) minmax(0,1.05fr); gap:clamp(14px,2vw,32px); margin-top:clamp(18px,2.1vw,34px); }
.membership-book { min-width:0; }
.membership-book__cover { box-sizing:border-box; position:relative; display:flex; flex-direction:column; height:100%; padding:clamp(17px,2.15vw,38px); border:3px solid #914e30; border-radius:23px; background:#8c4a2f url('/assets/membership/leather.png') center / cover; box-shadow:inset 0 0 18px #39150a82,0 6px 12px #6e37145a; }
.membership-book__cover:after { content:""; position:absolute; inset:7px; border:1px dashed #e1a976a3; border-radius:10px 16px 12px; pointer-events:none; }
.membership-book__heading { display:flex; align-items:center; gap:12px; }
.membership-book__heading p { margin:5px 0 0; color:#fae4c9; font-size:14px; }
.membership-book h2 { margin:0; color:#ffdc95; font-size:clamp(25px,2.6vw,43px); line-height:1.1; text-shadow:0 2px 5px #452213; }
.membership-laurel { width:clamp(36px,4.5vw,65px); mix-blend-mode:screen; mask-image:radial-gradient(ellipse 60% 61%,black 58%,transparent 99%); opacity:.9; }
.membership-book__footer { position:relative; display:flex; flex-wrap:wrap; align-items:flex-end; justify-content:space-between; gap:10px; margin-top:15px; padding-top:13px; border-top:1px solid #f1bf8677; }
.membership-book__facts { display:grid; gap:7px; list-style:none; margin:0; padding:0; color:#fff0db; font-size:clamp(13px,1.16vw,19px); }
.membership-book__facts li span { display:inline-block; width:1.25em; color:#ffd99a; }
.membership-book__facts strong { color:#ffe2a9; }
.membership-gold { flex:none; min-height:34px; padding:4px 12px; border:1px solid #855122; border-radius:999px; background:linear-gradient(#f6dfad,#dfb578); color:#45270f; font-size:13px; font-weight:700; box-shadow:inset 0 0 0 1px #ffd892a0,0 2px 4px #42271365; cursor:pointer; }
.membership-tiers { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:clamp(8px,1vw,16px); }
.membership-tier,.membership-growth,.membership-records { position:relative; min-width:0; color:#472c20; border:1px solid #fff2db; background:#f8e8d1 url('/assets/membership/parchment.png') center / cover; box-shadow:0 4px 8px #77503160; border-radius:14px; padding:clamp(12px,1.45vw,23px); }
.membership-tier { display:flex; flex-direction:column; gap:10px; }
.membership-tier--basic { border:3px solid #b47843; }
.membership-tier--basic h2 { color:#834a27; }
.membership-tier--premium { background:linear-gradient(135deg,#e9dfed,#dcd0e1); border-color:#f5eafa; }
.membership-tier__current { position:absolute; top:0; right:0; background:#9b5c32; color:#fff4df; border-radius:0 9px 0 10px; font-size:11px; padding:2px 6px; }
.membership-tier h2,.membership-growth h2,.membership-records h2 { margin:0; font:700 clamp(18px,1.7vw,29px)/1.25 "Songti SC","SimSun",serif; }
.membership-tier h2 { margin-top:7px; padding-bottom:8px; border-bottom:1px dashed #a7866c60; }
.membership-tier ul { padding-inline-start:1.1em; margin:0; display:grid; gap:7px; font-size:clamp(12px,1vw,16px); }
.membership-tier li::marker { color:#a38168; }
.membership-tier button { align-self:flex-end; margin-top:auto; font-size:12px; padding-inline:8px; }
.membership-growth { padding:clamp(16px,2vw,32px); border:2px solid #fff0d3; border-radius:20px; }
.membership-growth__track { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:9px; text-align:center; margin:12px 0; }
.membership-growth__track strong,.membership-growth__track span { display:block; }
.membership-growth__track strong { font:700 clamp(20px,2vw,34px)/1.2 "Songti SC","SimSun",serif; }
.membership-growth__track span,.membership-growth__hint { font-size:13px; color:#634934; }
.membership-growth__hint { display:flex; justify-content:space-between; gap:8px; margin:0 0 5px; }
.membership-growth .membership-progress { min-height:11px; }
.membership-level-shelf { display:flex; align-items:end; justify-content:center; gap:clamp(10px,3vw,40px); margin:12px auto 8px; width:min(91%,530px); border-bottom:12px ridge #c89054; border-radius:12px; }
.membership-level-medal { display:flex; flex-direction:column; justify-content:center; align-items:center; width:clamp(44px,5vw,72px); aspect-ratio:1; border-radius:50%; border:3px double #b49054; font:700 clamp(14px,1.4vw,22px)/1 "Songti SC","SimSun",serif; color:#67451e; background:radial-gradient(circle at 36% 25%,#ffefc5,#c8833a); box-shadow:0 3px 5px #643e2048; }
.membership-level-medal small { margin-top:4px; font:500 10px/1.1 system-ui,sans-serif; }
.membership-level-medal.is-current { border-color:#e0b15e; color:#fff2c2; background:radial-gradient(circle at 35% 25%,#ad86bd,#664477); }
.membership-level-medal.is-locked { border-color:#a69c91; color:#4d4543; background:radial-gradient(circle at 35% 25%,#eee5d7,#a99e92); }
.membership-growth__track .membership-level-medal { width:clamp(51px,6.8vw,98px); }
.membership-records { padding:clamp(16px,2vw,32px); border:2px solid #fff0d3; border-radius:20px; }
.membership-records h2 { margin-bottom:11px; }
.membership-bottom { display:grid; gap:18px; margin-top:clamp(20px,2.3vw,38px); }
.membership-badges { padding:clamp(14px,2.2vw,27px); border:1px solid #99785a; border-radius:15px; background:linear-gradient(160deg,#4b3c31,#312a24); box-shadow:inset 0 1px #b3967660,0 5px 12px #271b1359; color:#fff3e0; }
.membership-badges header { display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; }
.membership-badges h2 { margin:0; font:700 clamp(20px,1.6vw,29px)/1.25 "Songti SC","SimSun",serif; }
.membership-badges header p { margin:3px 0 0; color:#dfc9b2; font-size:13px; }
.membership-badges header a { color:#f3d8ae; text-underline-offset:4px; }
.membership-badge-grid { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:8px; margin:14px 0 0; padding:0; list-style:none; }
.membership-badge-slot { min-width:0; display:grid; justify-items:center; align-content:start; gap:4px; padding:11px 6px; border:1px solid #aa8a6652; border-radius:11px; text-align:center; background:#2a231d90; }
.membership-badge-slot.is-earned { border-color:#be9a5b91; background:#5b452c; }
.membership-medal { width:clamp(42px,4.8vw,74px); aspect-ratio:1; display:grid; place-items:center; overflow:hidden; border-radius:50%; border:2px solid #86817b; background:radial-gradient(circle at 35% 22%,#aaa39a,#57534f 72%); box-shadow:inset 0 0 0 3px #2926264a,0 4px 5px #140f0b6e; }
.membership-medal svg { width:50%; fill:none; stroke:#221e1a; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
.is-earned .membership-medal { border-color:#d7b16c; background:#704e2b; }
.membership-medal :deep(.studio-art--badge) { display:block; width:100%; aspect-ratio:1; background-image:url('/assets/warm-studio/badges.png'); background-size:300% 200%; background-repeat:no-repeat; }
.membership-badge-slot strong { font-size:clamp(13px,1vw,16px); }
.membership-badge-state { font-size:12px; color:#d7c5b4; }.is-earned .membership-badge-state { color:#ffe2a1; }
.membership-badge-slot p,.membership-badge-empty { margin:0; font-size:12px; color:#dfc9b2; }
.membership-badge-empty { margin-top:14px; }.membership-badge-empty button { margin-left:6px; }
.membership-shortcuts { display:grid; }
.membership-shortcuts button { display:grid; grid-template-columns:auto minmax(0,1fr) auto; align-items:center; gap:12px; min-height:58px; padding:8px; border:0; border-radius:8px; color:#412b1f; background:transparent; text-align:left; font:inherit; cursor:pointer; }
.membership-shortcuts button + button { border-top:1px solid #ab7e5538; }
.membership-shortcuts button:hover { background:#e3bb8850; }
.membership-record-icon { display:grid; place-items:center; width:34px; aspect-ratio:1; border:1px solid #b88c635e; border-radius:8px; color:#89552f; background:#eed2aa; }
.membership-record-icon svg { width:19px; fill:none; stroke:currentColor; stroke-width:1.55; stroke-linecap:round; stroke-linejoin:round; }
.membership-record-label { display:grid; gap:2px; line-height:1.3; }
.membership-record-label strong { font-size:14px; }
.membership-record-label small { color:#6b503d; font-size:12px; }
.membership-shortcuts b { color:#89552f; font-size:20px; }
.membership-page :is(a,button):focus-visible { outline:3px solid #ffdc91; outline-offset:4px; }
.membership-shortcuts button:focus-visible { outline-color:#89552f; outline-offset:0; }
@media(max-width:1050px) { .membership-main-grid{grid-template-columns:minmax(0,1fr)} }
@media(max-width:850px) { .membership-badge-grid{grid-template-columns:repeat(3,minmax(0,1fr))} }
@media(max-width:600px) { .membership-desk{padding-inline:15px}.membership-identity__validity{display:none}.membership-book__footer{align-items:center}.membership-tier h2{font-size:15px} }
@media(pointer:coarse) { .membership-gold,.membership-shortcuts button{min-height:44px} }
</style>
