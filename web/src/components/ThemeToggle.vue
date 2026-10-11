<script setup>
import { useTheme } from '../composables/useTheme.js'

const { theme, toggle, label, icon } = useTheme()
</script>

<template>
  <button
    class="theme-toggle"
    :title="`切换到${label()}`"
    :aria-label="`切换到${label()}`"
    @click="toggle"
  >
    <span class="dot">{{ icon() }}</span>
    <span>{{ theme === 'dark' ? '夜间' : '日间' }}</span>
  </button>
</template>
