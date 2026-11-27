import { test } from 'node:test'
import assert from 'node:assert/strict'
import { usageLabel, yuan } from '../src/services/assistantUsage.js'

test('receipt distinguishes settled charge, pending reserve and balance',()=>{
  assert.equal(usageLabel({charged_cny:.001234,pending_cny:.01,remaining_cny:1.97}),
    '本次已结算 ¥0.001234 · 待结算预留 ¥0.01 · 剩余 ¥1.97')
  assert.equal(usageLabel({charged_cny:0,pending_cny:0,remaining_cny:2}),'本次已结算 ¥0 · 剩余 ¥2')
  assert.equal(yuan(undefined),'—')
})
