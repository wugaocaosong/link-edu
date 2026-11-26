<script setup>
import {ref,computed,watch,onBeforeUnmount} from 'vue';
import {calibrationSummary,CALIBRATION_LABELS} from '../services/classroomCalibration.js';
const props=defineProps({enabled:Boolean,active:Boolean,motion:Object,study:Boolean});
const samples=ref([]),remaining=ref(0),dismissed=ref(false);
let timer;
const summary=computed(()=>calibrationSummary(samples.value));
function stop(){clearInterval(timer);remaining.value=0;}
function start(){stop();samples.value=[];dismissed.value=false;remaining.value=5;const began=performance.now();
  timer=setInterval(()=>{samples.value.push(props.motion||{});remaining.value=Math.max(0,Math.ceil(5-(performance.now()-began)/1000));if(!remaining.value)stop();},250);}
watch(()=>props.enabled && !props.active,on=>{if(on)start();else stop();});
onBeforeUnmount(stop);
</script>
<template>
  <section v-if="enabled && !active && !dismissed" class="calibration" aria-label="开课取景校准">
    <header><strong>取景检查</strong><span role="status" aria-live="polite">{{ remaining?`${remaining} 秒`:'检查完成，可继续授课' }}</span></header>
    <div class="calibration-modalities"><span v-for="(label,key) in {body:'身体',hands:'手势',face:'面部'}" :key="key">{{ label }} · {{ CALIBRATION_LABELS[summary[key].status] || '未知' }}</span></div>
    <small v-if="study">把双手和整张纸放进画面，试着折一下或指向其中一份。请主持人从预览确认能看清纸边、折痕和指向，并试听师生双方声音。</small>
    <small v-else>坐姿上半身即可。手不在画面内无需调整；不足项仅影响相关评价，不阻止授课。</small>
    <footer><button :disabled="remaining>0" @click="start">重新检查</button><button @click="stop();dismissed=true">继续</button></footer>
  </section>
</template>
<style scoped>
.calibration{padding:1rem;border:1px solid var(--line);border-radius:12px;margin-bottom:1rem;background:var(--class-surface-raised,#191520)}
header,footer,.calibration-modalities{display:flex;gap:1rem;flex-wrap:wrap;justify-content:space-between}small{display:block;color:var(--muted);margin:.75rem 0}button{padding:.5rem .75rem;background:transparent;color:inherit;border:1px solid var(--line);border-radius:8px;cursor:pointer}
</style>
