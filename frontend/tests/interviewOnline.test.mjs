import { test } from 'node:test'
import assert from 'node:assert/strict'
import { formatInterviewRubric, InterviewOnline } from '../src/services/interviewOnline.js'
import { respondToInterview, startInterview } from '../src/services/interviewPractice.js'

test('streams matching drafts, cancels and ignores late interview results', async () => {
  let data
  let interrupts=0
  const stream=new InterviewOnline({send:(type,payload)=>{data=payload},interrupt:()=>interrupts++})
  const controller=new AbortController()
  const drafts=[]
  const result=stream.request({action:'grade'},controller.signal,text=>drafts.push(text))
  stream.receive({type:'interview_delta',request_id:'stale',text:'stale'})
  stream.receive({type:'interview_delta',request_id:data.request_id,text:'草稿'})
  controller.abort()
  await assert.rejects(result,{name:'AbortError'})
  assert.equal(interrupts,1)
  assert.deepEqual(drafts,['草稿'])
  assert.equal(stream.receive({type:'interview_result',request_id:data.request_id,result:{}}),false)
})

test('renders four scores and real question references; local practice remains usable', () => {
  const dimensions=Object.fromEntries(['content','structure','language','time'].map(key=>[key,{score:72,advice:'重练'}]))
  const text=formatInterviewRubric({dimensions,feedback:'反馈',missing:[1],
    citation:{source:'结构化总题库',page:4,number:7,points:['了解原因']}})
  assert.equal(text.match(/72\/100/g).length,4)
  assert.match(text,/第 7 题/)
  assert.match(text,/了解原因（待补）/)
  const offline=respondToInterview(startInterview('structured'),'我会了解原因并跟进。')
  assert.equal(offline.stage,'complete')
  assert.ok(offline.assessment.total)
})
