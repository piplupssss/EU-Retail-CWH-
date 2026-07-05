<template>
  <div class="table-shell">
    <table>
      <thead>
        <tr>
          <th v-for="column in columns" :key="column.key" :style="{ width: column.width || undefined }">
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!rows.length">
          <td :colspan="columns.length" class="empty">暂无数据</td>
        </tr>
        <tr v-for="row in rows" :key="row[idKey] || JSON.stringify(row)">
          <td v-for="column in columns" :key="column.key" :class="column.className">
            <slot :name="column.key" :row="row">{{ row[column.key] ?? '-' }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  idKey: { type: String, default: 'id' }
})
</script>

