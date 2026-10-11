<script setup>
import { ref, watch } from 'vue'
import { api } from '../api.js'
import { useToast } from '../composables/useToast.js'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  selected: { type: Array, default: () => [] }
})
const emit = defineEmits(['update:modelValue', 'pick', 'unpick', 'clear'])

const toast = useToast()
const cwd = ref('')
const parent = ref('')
const items = ref([])
const loading = ref(false)
const error = ref('')
const manual = ref('')
const checking = ref(false)

async function load (path) {
  loading.value = true
  error.value = ''
  try {
    const data = await api.browse(path)
    cwd.value = data.cwd
    parent.value = data.parent
    items.value = data.items
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

watch(() => props.modelValue, (open) => {
  if (open && !cwd.value) load('')
}, { immediate: true })

function close () {
  emit('update:modelValue', false)
}

const short = (p) => p.split('/').pop() || p

function isSelected (path) {
  return props.selected.includes(path)
}

/** 选中或取消选中，并用 toast 明确告知结果，避免点击后毫无反馈。 */
function pick (item) {
  if (isSelected(item.path)) {
    emit('unpick', item.path)
    toast.push(`已移除 ${item.name}`, 'info')
    return
  }
  emit('pick', item.path)
  toast.success(`已添加 ${item.name}`)
}

async function addManual () {
  if (checking.value) return

  const value = manual.value.trim()
  if (!value) {
    toast.warn('请先填写文件或目录路径')
    return
  }
  if (isSelected(value)) {
    toast.warn('该路径已在列表中')
    return
  }

  // 先校验路径是否可用，避免加进去之后评判时才报 404。
  checking.value = true
  error.value = ''
  try {
    await api.browse(value)
  } catch (e) {
    error.value = e.message
    toast.error('路径不可用，未添加')
    return
  } finally {
    checking.value = false
  }

  emit('pick', value)
  manual.value = ''
  toast.success(`已添加 ${short(value)}`)
}

function clearAll () {
  if (!props.selected.length) {
    toast.warn('当前没有已选路径')
    return
  }
  emit('clear')
  toast.push('已清空日志来源', 'info')
}
</script>

<template>
  <div v-if="modelValue" class="modal-mask" @click.self="close">
    <div class="modal">
      <header class="modal-head">
        <h3>选择日志</h3>
        <button class="icon-btn" @click="close">✕</button>
      </header>

      <div class="toolbar">
        <button class="btn ghost" :disabled="!parent || parent === cwd" @click="load(parent)">↑ 上一级</button>
        <button class="btn ghost" @click="load('')">当前工作目录</button>
        <span class="path crumb">{{ cwd }}</span>
      </div>

      <div class="toolbar">
        <input
          v-model="manual"
          class="input"
          placeholder="或直接粘贴文件/目录绝对路径"
          @keydown.enter="addManual"
        />
        <button class="btn" @click="addManual">
          {{ checking ? '校验中…' : '添加' }}
        </button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>

      <div class="list">
        <p v-if="loading" class="muted">加载中…</p>
        <p v-else-if="!items.length" class="muted">该目录下没有子目录或 .md 文件</p>
        <button
          v-for="item in items"
          :key="item.path"
          class="row"
          :class="{ picked: isSelected(item.path) }"
          :title="isSelected(item.path) ? '再次点击可移除' : item.type === 'dir' ? '打开该目录' : '添加该日志'"
          @click="item.type === 'dir' ? load(item.path) : pick(item)"
        >
          <span class="ico">{{ item.type === 'dir' ? '📁' : '📄' }}</span>
          <span class="name">{{ item.name }}</span>
          <span class="tag">{{
            isSelected(item.path) ? '已选 ✓' : item.type === 'dir' ? '打开' : '选取'
          }}</span>
        </button>
      </div>

      <footer class="modal-foot">
        <span class="muted">
          已选 <strong class="count-strong">{{ selected.length }}</strong> 项（点击文件可添加/移除）
        </span>
        <div class="actions">
          <button class="btn ghost" @click="clearAll">清空</button>
          <button class="btn primary" @click="close">完成</button>
        </div>
      </footer>
    </div>
  </div>
</template>
