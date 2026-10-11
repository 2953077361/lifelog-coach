<script setup>
import { useToast } from '../composables/useToast.js'

const { items } = useToast()
</script>

<template>
  <Teleport to="body">
    <div class="toast-wrap">
      <div v-for="t in items" :key="t.id" class="toast" :class="t.type">{{ t.message }}</div>
    </div>
  </Teleport>
</template>
