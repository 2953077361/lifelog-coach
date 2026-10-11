<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  activeId: { type: String, default: '' }
})
const emit = defineEmits(['select', 'remove', 'clear'])

const label = (item) => (item.mode === 'judge' ? '单日' : '周复盘')
const preview = (item) => item.result.replace(/[#*>\-\s]+/g, ' ').trim().slice(0, 60)
</script>

<template>
  <section class="panel history">
    <header class="panel-head">
      <h2>历史记录 <span class="count">{{ items.length }}</span></h2>
      <button v-if="items.length" class="btn ghost sm" @click="emit('clear')">清空</button>
    </header>

    <p v-if="!items.length" class="muted pad">还没有记录。</p>

    <ul v-else class="hist-list">
      <li
        v-for="item in items"
        :key="item.id"
        :class="{ active: item.id === activeId }"
        @click="emit('select', item)"
      >
        <div class="line">
          <span class="chip tiny">{{ label(item) }}</span>
          <span class="time">{{ new Date(item.created_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }}</span>
          <button class="icon-btn sm" @click.stop="emit('remove', item.id)">🗑</button>
        </div>
        <p class="preview">{{ preview(item) || '（无内容）' }}</p>
      </li>
    </ul>
  </section>
</template>
