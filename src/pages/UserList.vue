<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/store/user'
import { USER_STATUS_LABEL } from '@/services/user.service'

const userStore = useUserStore()
const { list, total, loading, error } = storeToRefs(userStore)

const form = reactive({ name: '', email: '', role: 'viewer' })
const submitting = ref(false)

onMounted(() => {
  userStore.fetchList()
})

async function handleCreate() {
  submitting.value = true
  try {
    await userStore.createUser({ ...form })
    form.name = ''
    form.email = ''
    form.role = 'viewer'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <main class="page">
    <h1 class="page__title">用户管理</h1>

    <section class="panel">
      <h2 class="panel__title">新增用户</h2>
      <form class="form" @submit.prevent="handleCreate">
        <label class="form__item">
          <span>用户名</span>
          <input v-model="form.name" type="text" placeholder="请输入用户名" />
        </label>
        <label class="form__item">
          <span>邮箱</span>
          <input v-model="form.email" type="email" placeholder="请输入邮箱" />
        </label>
        <label class="form__item">
          <span>角色</span>
          <select v-model="form.role">
            <option value="admin">管理员</option>
            <option value="operator">运营</option>
            <option value="viewer">访客</option>
          </select>
        </label>
        <button class="btn" type="submit" :disabled="submitting">
          {{ submitting ? '提交中…' : '创建' }}
        </button>
      </form>
    </section>

    <section class="panel">
      <h2 class="panel__title">用户列表（共 {{ total }} 条）</h2>
      <div v-if="loading" class="skeleton">加载中…</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>邮箱</th>
            <th>角色</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in list" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.name }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.role }}</td>
            <td>{{ USER_STATUS_LABEL[user.status] }}</td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>

<style scoped>
.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px;
}
.page__title {
  font-size: 28px;
  letter-spacing: -0.03em;
  margin-bottom: 24px;
}
.panel {
  margin-bottom: 24px;
  padding: 20px;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  background: #fff;
}
.panel__title {
  font-size: 16px;
  margin-bottom: 16px;
}
.form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}
.form__item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  color: #374151;
}
.form__item input,
.form__item select {
  height: 36px;
  padding: 0 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  min-width: 180px;
}
.btn {
  height: 36px;
  padding: 0 20px;
  border: none;
  border-radius: 8px;
  background: #4338ca;
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: transform 0.1s;
}
.btn:active {
  transform: scale(0.98);
}
.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.table th,
.table td {
  text-align: left;
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
}
.table th {
  color: #6b7280;
  font-weight: 500;
}
.skeleton,
.error {
  padding: 40px;
  text-align: center;
  color: #6b7280;
  border: 1px dashed #d1d5db;
  border-radius: 16px;
}
.error {
  color: #b91c1c;
  border-color: #fca5a5;
}
</style>
