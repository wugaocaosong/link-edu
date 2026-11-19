<script setup>
defineProps({ homeLink: Boolean })
</script>
<template>
  <component :is="homeLink ? 'router-link' : 'div'" :to="homeLink ? '/dashboard' : undefined" class="brand" :aria-label="homeLink ? '临客 LINK，返回标签墙' : '临客 LINK'">
    <img
      class="brand-icon"
      src="/assets/brand-icon.png"
      alt=""
      width="40"
      height="40"
      draggable="false"
    />
    <strong>临客 <em>LINK</em></strong>
  </component>
</template>

<style scoped>
a.brand {text-decoration:none;color:inherit}
a.brand strong {font-family:"Songti SC","SimSun",serif;letter-spacing:.055em}
a.brand em {font-family:"Segoe UI",sans-serif;font-weight:650;letter-spacing:.14em;font-size:.78em}
a.brand .brand-icon {transition:transform .36s cubic-bezier(.2,.8,.3,1),filter .3s}
a.brand:is(:hover,:focus-visible) .brand-icon {transform:rotate(-10deg) translateY(-2px);filter:drop-shadow(0 0 7px #ce9afb88)}
a.brand:active .brand-icon {transform:scale(.93)}
@media(prefers-reduced-motion:reduce){a.brand .brand-icon{transition:none;transform:none!important}}
</style>
