<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => (route.meta.title as string | undefined) ?? '功能建设中')
const permission = computed(() => (route.meta.permission as string | undefined) ?? '')
</script>

<template>
  <div class="page">
    <header class="page__head">
      <div>
        <h1 class="page__title">{{ title }}</h1>
        <p class="page__subtitle">该模块仅用于演示菜单级权限过滤，功能建设中</p>
      </div>
    </header>

    <section class="panel placeholder">
      <span class="placeholder__icon" aria-hidden="true">⌁</span>
      <h2 class="placeholder__title">功能建设中</h2>
      <p class="placeholder__desc">
        访问本页面需要权限码 <code v-if="permission">{{ permission }}</code>，
        说明当前身份已通过菜单级权限校验。
      </p>
    </section>
  </div>
</template>

<style scoped>
.placeholder {
  padding: 56px 24px;
  text-align: center;
}
.placeholder__icon {
  display: block;
  font-size: 40px;
  color: var(--ink-3);
  line-height: 1;
  margin-bottom: 14px;
}
.placeholder__title {
  font-size: 16px;
  margin-bottom: 8px;
}
.placeholder__desc {
  color: var(--ink-2);
  font-size: 13px;
}
.placeholder__desc code {
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--brand-weak);
  color: var(--brand);
  font-size: 12px;
}
</style>
