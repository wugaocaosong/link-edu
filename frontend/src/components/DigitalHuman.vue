<script setup>
import { computed,ref,onMounted,onUnmounted,watch } from 'vue'
import PixelSprite from './PixelSprite.vue'
import { subscribeMotionPreferences } from '../utils/motionPreferences.js'
import { characterState } from '../services/assistantPersona.js'
const props=defineProps({pose:String,role:String,level:{type:Number,default:0},quiet:Boolean,
  animated:{type:Boolean,default:true},look:{type:Number,default:null},lookY:{type:Number,default:0}})
const host=ref(null),ready=ref(false),reduced=ref(false),abort=new AbortController()
const animate=computed(()=>props.animated&&!reduced.value&&!props.quiet)
const state=computed(()=>characterState(props.pose,{...props,animated:animate.value}))
let engine,disposed=false,observer,unsubscribe,policy,visible=false,starting=false,timer,pointerTarget
function pointerMove(event){const rect=host.value?.getBoundingClientRect();if(rect&&props.look===null)engine?.setPointer((event.clientX-rect.left)/Math.max(1,rect.width)*2-1)}
function pointerLeave(){if(props.look===null)engine?.setPointer(0)}
async function load(){if(starting||disposed||!visible||!policy?.visible||!animate.value)return;starting=true;try{const {createDigitalHuman}=await import('./fx/digitalHumanEngine.js');if(disposed||!animate.value)return;engine=await createDigitalHuman(host.value,{policy,signal:abort.signal,onReady:()=>{ready.value=true}});if(disposed){engine.dispose();return}sync()}catch{ready.value=false}finally{starting=false}}
function sync(){engine?.setVisible(visible&&animate.value);engine?.setPolicy({...policy,reducedMotion:!animate.value});engine?.setState(state.value,props.level);if(props.look!==null)engine?.setPointer(props.look);if(!engine&&!starting&&animate.value&&visible&&policy?.visible){clearTimeout(timer);timer=setTimeout(load,120)}}
watch(()=>[state.value,props.level],()=>engine?.setState(state.value,props.level))
watch(animate,sync)
watch(()=>props.look,value=>engine?.setPointer(value??0))
onMounted(()=>{unsubscribe=subscribeMotionPreferences(p=>{policy=p;reduced.value=p.reducedMotion;sync()});observer=new IntersectionObserver(([entry])=>{visible=entry.isIntersecting;sync()});observer.observe(host.value);pointerTarget=host.value.closest('button');pointerTarget?.addEventListener('pointermove',pointerMove,{passive:true});pointerTarget?.addEventListener('pointerleave',pointerLeave)})
onUnmounted(()=>{disposed=true;abort.abort();clearTimeout(timer);unsubscribe?.();observer?.disconnect();pointerTarget?.removeEventListener('pointermove',pointerMove);pointerTarget?.removeEventListener('pointerleave',pointerLeave);engine?.dispose()})
</script>
<template><span class="digital-human" aria-hidden="true"><PixelSprite v-show="!ready||!animate" character="assistant" /><span ref="host" class="digital-human__canvas" :class="{ready:ready&&animate}" /></span></template>
<style scoped>
.digital-human{display:block;position:relative;width:100%;height:100%;pointer-events:none;filter:drop-shadow(0 5px 8px #40305a26)}
.digital-human > .pixel-sprite,.digital-human__canvas{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}.digital-human__canvas{opacity:0}.digital-human__canvas.ready{opacity:1}.digital-human__canvas :deep(canvas){display:block;width:100%;height:100%;image-rendering:pixelated}
</style>
