<script setup lang="ts">
const layers = [
  { name: 'apis', desc: '封装 axios 异步请求（拦截器、统一解包）' },
  { name: 'services', desc: '业务逻辑层（业务校验、数据加工）' },
  { name: 'router', desc: '路由配置（懒加载页面）' },
  { name: 'store', desc: 'Pinia 状态仓库（组合式写法）' },
  { name: 'pages', desc: '页面组件（路由级）' },
  { name: 'components', desc: '公共组件' },
]
</script>

<template>
  <main class="page">
    <h1 class="page__title">关于本项目</h1>
    <p class="page__intro">
      基于 Vue3 + TypeScript + Vite + Pinia + Vue Router 的前端工程化分层框架，mock 接口由本地开发服务器中间件提供。
    </p>
    <ul class="layers">
      <li v-for="layer in layers" :key="layer.name" class="layer">
        <code class="layer__name">{{ layer.name }}</code>
        <span class="layer__desc">{{ layer.desc }}</span>
      </li>
    </ul>
  </main>
</template>

<style scoped>
.page {
  max-width: 720px;
  margin: 0 auto;
  padding: 32px 24px;
}
.page__title {
  font-size: 28px;
  letter-spacing: -0.03em;
  margin-bottom: 16px;
}
.page__intro {
  color: #4b5563;
  line-height: 1.7;
  margin-bottom: 24px;
}
.layers {
  list-style: none;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.layer {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
}
.layer__name {
  min-width: 110px;
  padding: 4px 10px;
  background: #eef2ff;
  color: #4338ca;
  border-radius: 6px;
  font-size: 13px;
}
.layer__desc {
  color: #4b5563;
  font-size: 14px;
}
</style>
