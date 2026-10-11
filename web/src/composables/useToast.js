import { ref } from 'vue'

// 全局单例：任何地方 push 一条提示，App.vue 里的 <Toast /> 负责渲染。
const items = ref([])
let seq = 0

function push (message, type = 'info', duration = 2200) {
  const id = ++seq
  items.value.push({ id, message, type })
  window.setTimeout(() => {
    items.value = items.value.filter((t) => t.id !== id)
  }, duration)
  return id
}

export function useToast () {
  return {
    items,
    push,
    success: (message) => push(message, 'success'),
    error: (message) => push(message, 'error'),
    warn: (message) => push(message, 'warn')
  }
}
