<script setup>
import { useUiVersion } from '../utils/uiVersion.js'
const { isStudio } = useUiVersion()
defineProps({ title: String, subtitle: String, variant: { type: String, default: 'study' } })
</script>

<template>
  <header v-if="isStudio" class="studio-banner" :class="`studio-banner--${variant}`">
    <div class="studio-banner__copy">
      <slot name="portrait" />
      <div><h1>{{ title }}</h1><p v-if="subtitle">{{ subtitle }}</p><slot /></div>
    </div>
  </header>
</template>
