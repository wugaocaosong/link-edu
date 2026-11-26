import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { isToolRequest, toolResourceRoute } from '../src/services/assistantTools.js'
import { libraryResources } from '../src/data/libraryResources.js'

test('resource cards can only navigate to a catalog ID', () => {
  const id=libraryResources.find(item=>item.title.includes('结构化真题')).id
  assert.deepEqual(toolResourceRoute({name:'open_resource',status:'ok',resource:{id,url:'invalid'}}),
    {path:'/resources',query:{resource:id}})
  assert.equal(toolResourceRoute({name:'open_resource',status:'ok',resource:{id:'unknown'}}),null)
  assert.equal(isToolRequest('打开结构化真题'),true)
  assert.equal(isToolRequest('打开档案袋'),false)
  assert.equal(isToolRequest('把刚才那道题记进错题本'),true)
})

test('backend resource index matches frontend catalog IDs and labels', () => {
  const index=JSON.parse(readFileSync(new URL('../../backend/data/assistant-resources.json',import.meta.url),'utf8'))
  assert.deepEqual(index,libraryResources.map(({id,title,category})=>({id,title,category})))
})
