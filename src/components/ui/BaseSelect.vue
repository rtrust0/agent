<script setup lang="ts">
defineProps<{
  modelValue: string
  options: Array<{ label: string; value: string }>
  label?: string
  disabled?: boolean
}>()

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

function onChange(event: Event) {
  emit('update:modelValue', (event.target as HTMLSelectElement).value)
}
</script>

<template>
  <label class="field">
    <span v-if="label" class="field__label">{{ label }}</span>
    <select class="field__input" :value="modelValue" :disabled="disabled" @change="onChange">
      <option v-for="option in options" :key="option.value" :value="option.value">
        {{ option.label }}
      </option>
    </select>
  </label>
</template>
