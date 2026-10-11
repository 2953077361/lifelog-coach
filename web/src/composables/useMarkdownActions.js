import { ref } from 'vue'

export function useMarkdownActions () {
  const copied = ref('')

  async function copy (text, key) {
    try {
      await navigator.clipboard.writeText(text)
      copied.value = key
      setTimeout(() => { copied.value = '' }, 1500)
    } catch {
      // 剪贴板不可用时（非 HTTPS 场景）退回到临时 textarea
      const ta = document.createElement('textarea')
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
      copied.value = key
      setTimeout(() => { copied.value = '' }, 1500)
    }
  }

  function download (record) {
    const name = `lifelog-${record.mode}-${record.id}.md`
    const blob = new Blob([record.result], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = name
    a.click()
    URL.revokeObjectURL(url)
  }

  return { copied, copy, download }
}
