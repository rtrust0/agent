<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth'
import { useToast } from '@/composables/useToast'
import { authService } from '@/services/auth.service'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseCaptcha from '@/components/ui/BaseCaptcha.vue'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const { toast } = useToast()

const form = reactive({ username: 'admin', password: '123456', captcha: '' })
const captchaId = ref('')
const captchaText = ref('')
const submitting = ref(false)
const error = ref('')

const demoAccounts = [
  { username: 'admin', label: '超级管理员' },
  { username: 'ops', label: '运营管理员' },
  { username: 'viewer', label: '只读观察者' },
]

async function refreshCaptcha() {
  try {
    const captcha = await authService.captcha()
    captchaId.value = captcha.captchaId
    captchaText.value = captcha.text
    form.captcha = ''
  } catch (e) {
    error.value = e instanceof Error ? e.message : '验证码加载失败'
  }
}

onMounted(refreshCaptcha)

function fillAccount(username: string) {
  form.username = username
  form.password = '123456'
}

async function onSubmit() {
  error.value = ''
  if (!form.username.trim() || !form.password || !form.captcha.trim()) {
    error.value = '请填写用户名、密码与验证码'
    return
  }
  submitting.value = true
  try {
    await auth.login({
      username: form.username.trim(),
      password: form.password,
      captchaId: captchaId.value,
      captcha: form.captcha.trim(),
    })
    toast('success', '登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    await router.replace(redirect)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '登录失败'
    await refreshCaptcha()
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="login">
    <section class="login__brand">
      <div class="login__grid" aria-hidden="true" />
      <div class="login__brand-inner">
        <span class="login__mark" aria-hidden="true" />
        <h1 class="login__title">辰光 Agent 平台</h1>
        <p class="login__tagline">权限蓝图 · 可审计的访问控制</p>
        <ul class="login__points">
          <li>基于角色与权限码的细粒度授权</li>
          <li>菜单、按钮、路由三级权限控制</li>
          <li>权限矩阵一目了然的授权关系</li>
        </ul>
      </div>
    </section>

    <section class="login__panel">
      <div class="login__form">
        <h2 class="login__heading">登录</h2>
        <p class="login__subheading">使用演示账号登录 RBAC 管理后台</p>

        <form class="login__fields" @submit.prevent="onSubmit">
          <BaseInput v-model="form.username" label="用户名" placeholder="请输入用户名" />
          <BaseInput v-model="form.password" label="密码" type="password" placeholder="请输入密码" />
          <BaseCaptcha v-model="form.captcha" :text="captchaText" @refresh="refreshCaptcha" />

          <p v-if="error" class="login__error">{{ error }}</p>

          <BaseButton type="submit" :loading="submitting" class="login__submit">
            {{ submitting ? '登录中…' : '登录' }}
          </BaseButton>
        </form>

        <div class="login__demo">
          <span class="login__demo-label">演示账号（密码 123456）</span>
          <div class="login__demo-list">
            <button
              v-for="account in demoAccounts"
              :key="account.username"
              class="login__demo-btn"
              type="button"
              @click="fillAccount(account.username)"
            >
              {{ account.label }}
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login {
  min-height: 100dvh;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  background: var(--bg);
}
.login__brand {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  background: var(--navy-900);
  color: #c9d3e3;
}
.login__grid {
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: radial-gradient(circle at 30% 30%, #000 20%, transparent 75%);
}
.login__brand-inner {
  position: relative;
  padding: 64px;
  max-width: 520px;
}
.login__mark {
  display: block;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--dawn), #b57d24);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.35);
  margin-bottom: 24px;
}
.login__title {
  color: #fff;
  font-size: 32px;
  letter-spacing: -0.03em;
  margin-bottom: 8px;
}
.login__tagline {
  color: var(--dawn);
  font-size: 14px;
  letter-spacing: 0.08em;
  margin-bottom: 32px;
}
.login__points {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: #a9b6cc;
  font-size: 13.5px;
}
.login__points li {
  position: relative;
  padding-left: 18px;
}
.login__points li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--grant);
}
.login__panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}
.login__form {
  width: 100%;
  max-width: 360px;
}
.login__heading {
  font-size: 24px;
  letter-spacing: -0.02em;
}
.login__subheading {
  margin-top: 6px;
  margin-bottom: 26px;
  color: var(--ink-2);
  font-size: 13px;
}
.login__fields {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.login__error {
  color: var(--danger);
  font-size: 12.5px;
}
.login__submit {
  width: 100%;
  height: 38px;
}
.login__demo {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px dashed var(--line);
}
.login__demo-label {
  font-size: 12px;
  color: var(--ink-3);
}
.login__demo-list {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}
.login__demo-btn {
  flex: 1;
  height: 30px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  color: var(--ink-2);
  font-size: 12px;
}
.login__demo-btn:hover {
  border-color: var(--brand);
  color: var(--brand);
}
@media (max-width: 860px) {
  .login {
    grid-template-columns: 1fr;
  }
  .login__brand {
    display: none;
  }
}
</style>
