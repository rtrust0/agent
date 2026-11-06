<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => (route.meta.title as string | undefined) ?? '功能建设中')
</script>

<template>
  <main class="placeholder-page">
    <h1>{{ title }}</h1>
    <p>该功能建设中。</p>
  </main>
</template>
