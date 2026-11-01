<script setup lang="ts">
import { RouterLink } from 'vue-router'

const navItems = [
  { to: '/', label: '首页' },
  { to: '/users', label: '用户管理' },
  { to: '/about', label: '关于' },
]
</script>

<template>
  <header class="app-header">
    <div class="app-header__inner">
      <span class="app-header__brand">辰光 Vue 前端</span>
      <nav class="app-header__nav">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="app-header__link"
          active-class="app-header__link--active"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 10;
  border-bottom: 1px solid #e5e7eb;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(8px);
}
.app-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 60px;
}
.app-header__brand {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.app-header__nav {
  display: flex;
  gap: 8px;
}
.app-header__link {
  padding: 6px 14px;
  border-radius: 8px;
  color: #4b5563;
  text-decoration: none;
  font-size: 14px;
  transition: background-color 0.15s;
}
.app-header__link:hover {
  background: #f3f4f6;
}
.app-header__link--active {
  background: #eef2ff;
  color: #4338ca;
}
</style>
