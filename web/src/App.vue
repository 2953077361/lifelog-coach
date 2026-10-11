<script setup>
import { onMounted, ref } from 'vue'
import { api } from './api.js'
import FileBrowser from './components/FileBrowser.vue'
import ResultView from './components/ResultView.vue'
import HistoryPanel from './components/HistoryPanel.vue'
import ThemeToggle from './components/ThemeToggle.vue'
import Toast from './components/Toast.vue'
import { useToast } from './composables/useToast.js'

const toast = useToast()

const status = ref(null)
const paths = ref([])
const mode = ref('judge')
const week = ref('')
const loading = ref(false)
const error = ref('')
const record = ref(null)
const history = ref([])
const browserOpen = ref(false)

async function loadStatus () {
  try {
    status.value = await api.status()
  } catch (e) {
    error.value = `无法连接后端 API：${e.message}`
  }
}

async function loadHistory () {
  try {
    history.value = await api.listHistory()
  } catch (e) {
    error.value = e.message
  }
}

function addPath (path) {
  if (!path) return
  if (paths.value.includes(path)) {
    toast.warn('该路径已在列表中')
    return
  }
  paths.value.push(path)
  toast.success(`已添加 ${path.split('/').pop() || path}`)
}

function removePath (path) {
  paths.value = paths.value.filter((p) => p !== path)
}

function clearPaths () {
  paths.value = []
}

async function run () {
  if (!paths.value.length) {
    error.value = '请先选择至少一个日志文件或目录。'
    return
  }
  loading.value = true
  error.value = ''
  record.value = null
  try {
    const data = await api.run({ mode: mode.value, paths: paths.value, week: week.value })
    record.value = data.record
    toast.success('评判完成')
    await loadHistory()
  } catch (e) {
    error.value = e.message
    toast.error('评判失败：' + e.message)
  } finally {
    loading.value = false
  }
}

function openRecord (item) {
  record.value = item
}

async function removeRecord (id) {
  try {
    await api.deleteHistory(id)
    if (record.value?.id === id) record.value = null
    await loadHistory()
  } catch (e) {
    error.value = e.message
  }
}

async function clearRecords () {
  try {
    await api.clearHistory()
    record.value = null
    await loadHistory()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(() => {
  loadStatus()
  loadHistory()
})
</script>

<template>
  <div class="app">
    <header class="topbar">
      <div class="brand">
        <span class="logo">🍵</span>
        <div>
          <h1>lifelog-coach</h1>
          <p class="sub">读取 Markdown 生活日志，让 AI 判断趋势、揪出破防目标</p>
        </div>
      </div>

      <div class="status">
        <div v-if="status" class="chips">
          <span class="chip" :class="status.configured ? 'ok' : 'warn'">
            {{ status.configured ? 'API Key 已配置' : '未配置 API Key' }}
          </span>
          <span class="chip muted-chip">{{ status.model }}</span>
          <span class="chip muted-chip" :title="status.base_url">{{ status.base_url }}</span>
        </div>
        <ThemeToggle />
      </div>
    </header>

    <p v-if="error" class="banner">{{ error }}</p>

    <main class="layout">
      <aside class="side">
        <section class="panel">
          <header class="panel-head">
            <h2>日志来源</h2>
            <button class="btn ghost sm" @click="browserOpen = true">浏览…</button>
          </header>

          <ul v-if="paths.length" class="paths">
            <li v-for="p in paths" :key="p">
              <span class="src" :title="p">{{ p }}</span>
              <button class="icon-btn sm" @click="removePath(p)">✕</button>
            </li>
          </ul>
          <p v-else class="muted pad">未选择。可浏览目录，或直接粘贴一个包含日志的目录。</p>
        </section>

        <section class="panel">
          <header class="panel-head"><h2>评判方式</h2></header>

          <div class="segment">
            <button :class="{ on: mode === 'judge' }" @click="mode = 'judge'">单日评判 judge</button>
            <button :class="{ on: mode === 'review' }" @click="mode = 'review'">周复盘 review</button>
          </div>

          <label v-if="mode === 'review'" class="field">
            <span>周区间（MM-DD..MM-DD）</span>
            <input v-model="week" class="input" placeholder="10-05..10-11" />
          </label>

          <button class="btn primary block" :disabled="loading || !paths.length" @click="run">
            {{ loading ? '评判中…' : '开始评判' }}
          </button>
        </section>

        <HistoryPanel
          :items="history"
          :active-id="record?.id"
          @select="openRecord"
          @remove="removeRecord"
          @clear="clearRecords"
        />
      </aside>

      <ResultView :record="record" :loading="loading" />
    </main>

    <FileBrowser
      v-model="browserOpen"
      :selected="paths"
      @pick="addPath"
      @unpick="removePath"
      @clear="clearPaths"
    />

    <Toast />
  </div>
</template>
