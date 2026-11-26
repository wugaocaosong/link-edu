const rubricLabels={content:'内容',structure:'结构',language:'语言（文字表达）',time:'时间（估算）'}

export function formatInterviewRubric(result) {
  const citation=result.citation
  const reference=citation.number ? `${citation.source} · PDF 第 ${citation.page} 页 · 第 ${citation.number} 题` : citation.source
  const dimensions=Object.entries(rubricLabels).map(([key,label])=>{
    const {score,advice}=result.dimensions[key]
    return `${label} ${score}/100｜${advice}`
  })
  const points=citation.points.map((point,index)=>`${index+1}. ${point}${result.missing.includes(index+1)?'（待补）':''}`)
  return [result.feedback,...dimensions,`评分依据｜${reference}（练习参考，非官方评分）`,...points].join('\n')
}

export class InterviewOnline {
  constructor(client) { this.client=client;this.pending=null }

  receive(event) {
    const pending=this.pending
    if(!pending)return false
    if(event.type==='closed'){pending.finish(new Error('连接已关闭'));return false}
    if(!event.type.startsWith('interview_'))return false
    if(event.request_id!==pending.id)return true
    if(event.type==='interview_delta')pending.onDraft(event.text)
    if(event.type==='interview_result')pending.finish(null,{...event.result,usage:event.usage})
    if(event.type==='interview_error')pending.finish(Object.assign(new Error(event.message),{usage:event.usage}))
    return true
  }

  request(data, signal, onDraft=()=>{}) {
    if(signal.aborted)return Promise.reject(new DOMException('已取消','AbortError'))
    return new Promise((resolve,reject)=>{
      if(this.pending){reject(new Error('已有在线练习在运行'));return}
      const id=crypto.randomUUID()
      const finish=(error,result)=>{
        if(this.pending?.id!==id)return
        this.pending=null
        clearTimeout(timer)
        signal.removeEventListener('abort',abort)
        if(error)reject(error);else resolve(result)
      }
      const abort=()=>{this.client.interrupt();finish(new DOMException('已取消','AbortError'))}
      const timer=setTimeout(()=>{this.client.interrupt();finish(new Error('在线练习超时'))},55000)
      this.pending={id,finish,onDraft}
      signal.addEventListener('abort',abort,{once:true})
      try{this.client.send('interview',{...data,request_id:id})}catch(error){finish(error)}
    })
  }
}
