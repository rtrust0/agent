<script setup lang="ts">
defineProps<{ modelValue: string; text: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string]; refresh: [] }>()

function onInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <div class="captcha">
    <label class="field captcha__field">
      <span class="field__label">验证码</span>
      <input
        class="field__input"
        type="text"
        maxlength="4"
        placeholder="请输入验证码"
        :value="modelValue"
        @input="onInput"
      />
    </label>
    <button class="captcha__box" type="button" title="点击刷新验证码" @click="emit('refresh')">
      {{ text || '加载中' }}
    </button>
  </div>
</template>

<style scoped>
.captcha {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}
.captcha__field {
  flex: 1;
}
.captcha__box {
  width: 96px;
  height: 34px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--navy-800);
  color: #f3e2bd;
  font-family: var(--font-mono);
  font-size: 17px;
  letter-spacing: 0.24em;
  text-indent: 0.24em;
}
</style>
