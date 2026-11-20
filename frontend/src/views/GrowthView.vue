<template>
  <main class="growth-entry" aria-label="成长档案入口">
    <section class="growth-entry__art" aria-label="成长档案袋">
      <img class="growth-entry__image" src="/assets/growth-archive-desk.png" alt="木桌上的档案袋，点击打开成长档案" />
      <router-link class="growth-entry__hotspot" to="/growth/archive" aria-label="打开档案袋，进入成长档案">
        <span class="growth-entry__hint">打开档案袋 <span aria-hidden="true">↗</span></span>
      </router-link>
    </section>
  </main>
</template>
<style scoped>
.growth-entry{flex:1;display:grid;min-width:0;min-height:0;width:100%;place-items:center;overflow:hidden}
.growth-entry__art{position:relative;width:100%;height:100%;overflow:hidden;background:#423326;isolation:isolate}
.growth-entry__image{display:block;width:100%;height:100%;object-fit:cover;object-position:center}
.growth-entry__art::after{position:absolute;z-index:1;inset:0;background:radial-gradient(ellipse at center,transparent 48%,rgba(7,6,10,.12) 72%,rgba(7,6,10,.72) 100%),linear-gradient(90deg,rgba(7,6,10,.38),transparent 13%,transparent 87%,rgba(7,6,10,.38));content:'';pointer-events:none}
.growth-entry__hotspot{position:absolute;z-index:2;left:32.5%;top:20%;width:46.5%;height:37%;display:grid;place-items:end center;border-radius:4%;color:#fff7e8;text-decoration:none;outline:0;cursor:pointer}
.growth-entry__hotspot::before{position:absolute;inset:0;border:2px solid transparent;border-radius:inherit;background:transparent;content:'';transition:border-color .18s ease,background-color .18s ease,box-shadow .18s ease}
.growth-entry__hint{position:relative;z-index:1;margin-bottom:8%;padding:9px 15px;border:1px solid rgba(255,235,199,.5);border-radius:999px;background:rgba(77,45,23,.78);color:#fff7e8;font-size:clamp(12px,1vw,16px);font-weight:650;opacity:.82;transition:opacity .18s ease,transform .18s ease}
.growth-entry__hotspot:hover::before,.growth-entry__hotspot:focus-visible::before{border-color:rgba(255,244,216,.78);background:rgba(255,213,155,.08);box-shadow:inset 0 0 28px rgba(255,235,199,.18),0 0 22px rgba(255,219,164,.3)}
.growth-entry__hotspot:hover .growth-entry__hint,.growth-entry__hotspot:focus-visible .growth-entry__hint{opacity:1;transform:translateY(-4px)}
@media(prefers-reduced-motion:reduce){.growth-entry__hotspot::before,.growth-entry__hint{transition:none}}
</style>
