<template>
  <div class="list-toolbar">
    <div class="toolbar-left">
      <input :value="search" :placeholder="placeholder" @input="$emit('update:search', $event.target.value)" />
      <button class="btn secondary" @click="$emit('clear')">清除筛选</button>
      <button class="btn secondary" @click="$emit('columns')">详细列</button>
      <select :value="perPage" @change="$emit('update:perPage', Number($event.target.value))">
        <option :value="20">20/页</option>
        <option :value="50">50/页</option>
        <option :value="100">100/页</option>
      </select>
      <slot name="filters" />
    </div>
    <div class="toolbar-right">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  search: { type: String, default: '' },
  perPage: { type: Number, default: 20 },
  placeholder: { type: String, default: '搜索...' }
})
defineEmits(['update:search', 'update:perPage', 'clear', 'columns'])
</script>

