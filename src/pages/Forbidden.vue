<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import BaseButton from '@/components/ui/BaseButton.vue'

const router = useRouter()
const auth = useAuthStore()

function switchAccount() {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="forbidden">
    <div class="forbidden__card">
      <span class="forbidden__code">403</span>
      <h1 class="forbidden__title">无权访问该页面</h1>
      <p class="forbidden__desc">
        当前账号没有访问此页面的权限。如需继续，请联系管理员分配对应权限，或切换其他身份。
      </p>
      <div class="forbidden__actions">
        <BaseButton @click="router.replace('/')">返回工作台</BaseButton>
        <BaseButton variant="ghost" @click="switchAccount">切换账号</BaseButton>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forbidden {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--bg);
}
.forbidden__card {
  width: 100%;
  max-width: 460px;
  padding: 40px;
  text-align: center;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  box-shadow: var(--shadow);
}
.forbidden__code {
  display: block;
  font-family: var(--font-mono);
  font-size: 56px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--dawn);
  line-height: 1;
  margin-bottom: 12px;
}
.forbidden__title {
  font-size: 20px;
  letter-spacing: -0.02em;
  margin-bottom: 10px;
}
.forbidden__desc {
  color: var(--ink-2);
  font-size: 13px;
  line-height: 1.7;
  margin-bottom: 26px;
}
.forbidden__actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}
</style>
