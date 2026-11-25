import { test } from 'node:test'
import assert from 'node:assert/strict'
import { characterState, motionEnabled, replyPose } from '../src/services/assistantPersona.js'

test('reply intent maps to notebook, applause or thinking', () => {
  assert.equal(replyPose('记住一个要点：先听完学生的理由。'),'notes')
  assert.equal(replyPose('别灰心，卡住很正常。重点是先练一小步。'),'cheer')
  assert.equal(replyPose('无法确认',{tier:'unknown'}),'thinking')
  assert.equal(replyPose('',{failed:true}),'thinking')
  assert.equal(replyPose('你好。'),'')
  assert.equal(characterState('notes'),'formal')
  assert.equal(characterState('cheer'),'happy')
  assert.equal(characterState('thinking'),'thinking')
})

test('manual disable and system reduced motion each override reply pose', () => {
  for(const [preference,reduced] of [[false,false],[true,true],[false,true]]) {
    const animated=motionEnabled(preference,reduced)
    assert.equal(animated,false)
    assert.equal(characterState('cheer',{animated}),'idle')
  }
  assert.equal(motionEnabled(true,false),true)
})
