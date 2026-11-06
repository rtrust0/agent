<script setup lang="ts">
withDefaults(
  defineProps<{
    modelValue: string
    label?: string
    error?: string
    placeholder?: string
    type?: string
    disabled?: boolean
  }>(),
  { type: 'text', disabled: false },
)

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

function onInput(event: Event) {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
}
</script>

<template>
  <label class="field">
    <span v-if="label" class="field__label">{{ label }}</span>
    <input
      class="field__input"
      :class="{ 'field__input--error': error }"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="onInput"
    />
    <span v-if="error" class="field__error">{{ error }}</span>
  </label>
</template>
