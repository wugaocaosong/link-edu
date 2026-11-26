import { Zip, ZipPassThrough, strToU8 } from 'fflate'

// Store the already-compressed video in chunks. Never include OS filenames or
// the export date in a blind rater's archive.
export async function archive(files) {
  const chunks = []
  const zip = new Zip((error, data) => {
    if (error) throw error
    chunks.push(data)
  })
  for (const [name, content] of files) {
    const file = new ZipPassThrough(name)
    file.mtime = new Date(2000, 0, 1)
    zip.add(file)
    if (content instanceof Blob) {
      for (let i = 0; i < content.size; i += 1024 * 1024)
        file.push(new Uint8Array(await content.slice(i, i + 1024 * 1024).arrayBuffer()))
      file.push(new Uint8Array(), true)
    } else file.push(strToU8(content), true)
  }
  zip.end()
  return new Blob(chunks, { type: 'application/zip' })
}

export function blindFiles(clip, recording, marks) {
  const ext = recording.blob.type.includes('mp4') ? 'mp4' : 'webm'
  const sheet = ['片段号,机会,录像时间（秒）,概念指向,理解诊断,追问承接,解释调整,依据或缺失原因,评分者编号,提交日期',
    ...[0, 1].map(i => [clip, i + 1, marks[i] == null ? '' : (marks[i] / 1000).toFixed(2), '', '', '', '', '', '', ''].join(','))]
  return [[clip + '.' + ext, recording.blob], [clip + '.csv', '\ufeff' + sheet.join('\r\n')]]
}

export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 60000)
}
