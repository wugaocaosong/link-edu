export function analyzeLessonAudio(buffer, transcript) {
  const samples = buffer.getChannelData(0)
  const windowSize = Math.max(1, Math.floor(buffer.sampleRate * .05))
  const levels = []
  for(let start=0;start+windowSize<=samples.length;start+=windowSize){
    let sum=0
    for(let i=start;i<start+windowSize;i++)sum+=samples[i]**2
    levels.push(Math.sqrt(sum/windowSize))
  }
  const sorted=[...levels].sort((a,b)=>a-b)
  const threshold=Math.max(.008,(sorted[Math.floor(sorted.length*.85)]||0)*.13)
  const first=levels.findIndex(value=>value>=threshold)
  const last=levels.findLastIndex(value=>value>=threshold)
  if (first<0 || last-first<10) return null
  const active=levels.slice(first,last+1)
  const pauses=[]
  let silence=0
  for(const [index,level] of active.entries()){
    if(level<threshold)silence++
    else {
      if(silence>=8)pauses.push({at:(first+index-silence)*.05,duration:silence*.05})
      silence=0
    }
  }
  const voiced=active.filter(value=>value>=threshold).sort((a,b)=>a-b)
  const variation=20*Math.log10(voiced[Math.floor(voiced.length*.85)]/voiced[Math.floor(voiced.length*.25)])
  const seconds=active.length*.05
  const longPauses=pauses.filter(pause=>pause.duration>=1.2).length
  const units=(transcript.match(/\p{Script=Han}|[a-z0-9]+/giu)||[]).length
  const pace=units?Math.round(units*60/seconds):null
  const fillers=units?(transcript.match(/[嗯呃额啊]+/gu)||[]).length:null
  const cap = score=>Math.round(Math.max(0,Math.min(100,score)))
  const scores=[
    ['连贯性',cap(100-longPauses*120/Math.max(1,seconds/10))],
    ['停顿分布',cap(100-Math.abs(pauses.reduce((sum,pause)=>sum+pause.duration,0)/seconds-.14)*220)],
    ['音量起伏',cap(variation*10)],
  ]
  if(units>=10&&seconds>=5){
    scores.push(['语速',cap(100-Math.max(0,175-pace,pace-265)*.8)])
    scores.push(['语气词控制',cap(100-fillers*1000/units)])
  }
  return {seconds:Math.round(seconds),pauseMarkers:pauses.filter(pause=>pause.duration>=1.2).slice(0,4),pauses:pauses.length,longPauses,variation:variation.toFixed(1),pace,fillers,scores}
}
