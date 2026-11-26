// Transport owns no classroom records; every payload is scoped to one assistant session.
import { ClassroomAudio } from './classroomAudio.js'
export class AssistantClient {
  constructor({api,onEvent,Audio=ClassroomAudio,Socket=WebSocket,depth='brief'}) { this.api=api;this.onEvent=onEvent;this.Audio=Audio;this.Socket=Socket;this.style='warm';this.depth=depth==='detailed'?'detailed':'brief';this.epoch=0;this.attachmentEpoch=0;this.cancelled=new Set() }
  send(type,payload={}) { if(this.socket?.readyState===1&&this.session)this.socket.send(JSON.stringify({type,session_id:this.session,...payload})) }
  async sendAttachment(type,file,text,requestId) {
    if(!this.attachmentsAvailable)throw Error('当前助手后端未启用附件问答。')
    const socket=this.socket, epoch=this.epoch, upload=++this.attachmentEpoch, session=this.session
    const check=()=>{
      if(epoch!==this.epoch||upload!==this.attachmentEpoch||socket!==this.socket||socket?.readyState!==1||!session)
        throw new DOMException('附件发送已取消','AbortError')
    }
    const request_id=requestId
    check()
    this.send(type,{phase:'begin',request_id,name:file.name,size:file.size})
    const chunkSize=24*1024
    for(let offset=0;offset<file.size;offset+=chunkSize){
      const data=new Uint8Array(await file.slice(offset,offset+chunkSize).arrayBuffer())
      while(socket.bufferedAmount>256*1024){
        check()
        await new Promise(resolve=>setTimeout(resolve,20))
      }
      check()
      this.send(type,{phase:'chunk',request_id,offset,data:btoa(String.fromCharCode(...data))})
    }
    check()
    this.send(type,{phase:'end',request_id,text})
  }
  async start(mode='text',style=this.style) {
    this.stop();const epoch=this.epoch;this.mode=mode;this.style=style==='calm'?'calm':'warm'
    this.onEvent({type:'state',state:'connecting'})
    try {
      const cap=(await this.api.get('/assistant/capabilities',{skipBusy:true,timeout:8000})).data
      if(epoch!==this.epoch)return false
      if(!cap || typeof cap[mode+'_available']!=='boolean')throw new Error('助手接口未返回有效状态，请检查后端服务。')
      if(!cap[mode+'_available'])throw new Error(cap[mode+'_message']||cap.message||'该对话服务暂未启用，可先查看使用帮助。')
      this.attachmentsAvailable=cap.attachments_available===true
      const issuedDepth=this.depth
      const {data}=await this.api.post('/assistant/ticket',{mode,style:this.style,depth:issuedDepth},{skipBusy:true,timeout:8000})
      if(epoch!==this.epoch)return false
      await new Promise((resolve,reject)=>{
        const url=new URL('/api/assistant/live',location.href);url.protocol=url.protocol==='https:'?'wss:':'ws:'
        const socket=this.socket=new this.Socket(url)
        const timer=setTimeout(()=>reject(new Error('助手连接超时')),10000)
        this.rejectConnect=()=>{clearTimeout(timer);reject(new Error('连接已取消'))}
        socket.onopen=()=>{if(epoch===this.epoch)socket.send(JSON.stringify({ticket:data.ticket}))}
        socket.onmessage=({data:raw})=>{
          if(epoch!==this.epoch)return
          let event;try{event=JSON.parse(raw)}catch{return}
          if(event.type==='ready'){this.session=event.session_id;clearTimeout(timer);this.rejectConnect=null;this.send('style',{style:this.style});if(this.depth!==issuedDepth)this.send('depth',{depth:this.depth});resolve();return}
          if(event.type==='error'&&!this.session){clearTimeout(timer);reject(new Error(event.message));return}
          this.receive(event)
        }
        socket.onerror=()=>{clearTimeout(timer);reject(new Error('助手连接失败'))}
        socket.onclose=()=>{clearTimeout(timer);if(epoch!==this.epoch)return;reject(new Error('连接已关闭'));this.stop();this.onEvent({type:'closed',message:'助手连接已关闭，可重新开始'})}
      })
      if(epoch!==this.epoch)return false
      if(mode==='voice') {
        this.audio=new this.Audio((type,payload)=>this.send(type,payload),level=>this.onEvent({type:'level',level}),
          (turn,state)=>{if(turn!==this.turn||this.cancelled.has(turn))return;this.onEvent({type:'state',state:state==='playing'?'speaking':'listening'})},{playbackRate:1})
        await this.audio.start()
        if(epoch!==this.epoch)return false
      }
      this.onEvent({type:'state',state:mode==='voice'?'listening':'idle'});return true
    } catch(error) {
      if(epoch!==this.epoch)return false
      this.stop()
      const code=error.response?.status
      const message=error.name==='NotAllowedError'?'麦克风未授权，可使用文字问答'
        :code===401||code===422?'登录状态已失效，请重新登录后再试。'
        :code===404||code===502||code===504||error.code==='ERR_NETWORK'?'无法访问助手后端，请检查本地预览的 API 连接。'
        :error.response?.data?.message||error.message||'助手连接失败，请重试。'
      this.onEvent({type:'error',mode,message})
      return false
    }
  }
  receive(event) {
    if(!this.session||event.session_id!==this.session)return
    if(['interview_delta','interview_result','interview_error'].includes(event.type)){this.onEvent(event);return}
    if(event.type==='cancel'){const id=event.cancelled_turn_id;this.cancelled.add(id);this.audio?.cancel(id);if(id===this.turn)this.turn=null;this.onEvent(event);return}
    if(event.type==='recognition'&&event.final){if(this.turn)this.audio?.cancel(this.turn);this.turn=event.turn_id}
    if(event.turn_id&&(event.turn_id!==this.turn||this.cancelled.has(event.turn_id)))return
    if(event.type==='audio')this.audio?.chunk(event.turn_id,event.audio,event.rate)
    else if(event.type==='audio_end')this.audio?.end(event.turn_id)
    else if(event.type==='closed'){this.stop();this.onEvent(event)}
    else if(event.type==='error'){this.audio?.cancel(this.turn);this.onEvent(event)}
    else this.onEvent(event)
  }
  setStyle(style){this.style=style==='calm'?'calm':'warm';this.send('style',{style:this.style})}
  setDepth(depth){this.depth=depth==='detailed'?'detailed':'brief';this.send('depth',{depth:this.depth})}
  interrupt(){this.attachmentEpoch++;if(this.turn){this.cancelled.add(this.turn);this.audio?.cancel(this.turn)}this.send('cancel');this.onEvent({type:'state',state:this.mode==='voice'?'listening':'idle'})}
  stop(){this.epoch++;this.attachmentsAvailable=false;this.rejectConnect?.();this.rejectConnect=null;this.send('stop');this.session=null;this.turn=null;this.cancelled.clear();const socket=this.socket;this.socket=null;if(socket){socket.onclose=null;socket.close()}const audio=this.audio;this.audio=null;audio?.close();this.onEvent({type:'level',level:0})}
}
