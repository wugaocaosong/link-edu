import test from 'node:test'
import assert from 'node:assert/strict'
import { unzipSync, strFromU8 } from 'fflate'
import { archive, blindFiles } from '../src/services/studyArchive.js'

test('blind bundle has only clip and scoring rows, including an absent first opportunity', async () => {
  const clip = 'ec7e9328fa434431aa8a745e9e4ad206'
  const blob = new Blob(['synthetic video'], {type:'video/webm'})
  const pack = await archive(blindFiles(clip, {blob,participant:'P01',stage:'post'}, [null,5000]))
  const files = unzipSync(new Uint8Array(await pack.arrayBuffer()))
  assert.deepEqual(Object.keys(files), [clip+'.webm',clip+'.csv'])
  const csv = strFromU8(files[clip+'.csv'])
  assert.match(csv,new RegExp(clip+',1,,,'))
  assert.match(csv,new RegExp(clip+',2,5.00,'))
  assert.doesNotMatch(csv,/P01|post|前测|后测|组别/)
})
