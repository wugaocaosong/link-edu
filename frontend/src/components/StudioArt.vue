<script setup>
defineProps({ kind: { type: String, default: 'cover' }, index: { type: Number, default: 0 } })
</script>
<template>
  <span class="studio-art" :class="`studio-art--${kind}`" :style="{ backgroundPosition: `${(Math.max(0, index) % 3) * 50}% ${Math.floor((Math.max(0, index) % 6) / 3) * 100}%` }" aria-hidden="true"></span>
</template>
