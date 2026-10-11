<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'
import { useMarkdownActions } from '../composables/useMarkdownActions.js'

const props = defineProps({
  record: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })
const rendered = computed(() => (props.record?.result ? md.render(props.record.result) : ''))
const { copied, copy, download } = useMarkdownActions()
</script>

<template>
  <section class="panel result">
    <header class="panel-head">
      <h2>评判结果</h2>
      <div v-if="record" class="actions">
        <button class="btn ghost sm" @click="copy(record.result, 'judge')">
          {{ copied === 'judge' ? '已复制 ✓' : '复制' }}
        </button>
        <button class="btn ghost sm" @click="download(record)">下载 .md</button>
      </div>
    </header>

    <p v-if="loading" class="muted pad">正在读取日志并请求 AI 评判，通常需要几秒…</p>
    <p v-else-if="!record" class="muted pad empty">
      左侧选择日志后点击「开始评判」，结果会显示在这里。
    </p>

    <div v-else class="result-body">
      <div class="meta">
        <span class="chip">{{ record.mode === 'judge' ? '单日评判' : '周复盘' }}</span>
        <span v-if="record.week" class="chip">{{ record.week }}</span>
        <span class="chip muted-chip">{{ new Date(record.created_at).toLocaleString('zh-CN') }}</span>
      </div>

      <div class="sources">
        <span v-for="p in record.paths" :key="p" class="src" :title="p">{{ p.split('/').pop() }}</span>
      </div>

      <!-- AI 返回的是 markdown，这里渲染成排版后的结果 -->
      <div class="markdown" v-html="rendered"></div>

      <details class="raw">
        <summary>查看发送给 AI 的日志原文（{{ record.content.length }} 字符）</summary>
        <pre>{{ record.content }}</pre>
      </details>
    </div>
  </section>
</template>
