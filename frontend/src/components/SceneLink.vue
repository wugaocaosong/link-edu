<script setup>
import { useRouter } from 'vue-router'
import { travelScene } from '../utils/sceneTransition.js'
defineProps({ to: { type: String, required: true }, direction: { type: String, required: true } })
const router = useRouter()
</script>

<template>
  <a :href="router.resolve(to).href" @click="travelScene($event, router, to, direction)"><slot /></a>
</template>
