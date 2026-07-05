<template>
  <section class="page">
    <PageHeader eyebrow="ACCEPTANCE LIST" title="验收清单" subtitle="点击发票号或 STT 查看详情" />
    <ListToolbar v-model:search="search" v-model:per-page="perPage" placeholder="搜索发票号 / STT..." @clear="clear" @update:search="load" @update:per-page="load">
      <template #filters>
        <select v-model="status" @change="load">
          <option value="">全部状态</option>
          <option value="verified">已验收</option>
          <option value="pending">待验收</option>
          <option value="rejected">异常</option>
        </select>
      </template>
      <template #actions>
        <button class="btn primary">导出验收清单</button>
      </template>
    </ListToolbar>
    <DataTable :columns="columns" :rows="filteredRows" id-key="id">
      <template #invoice_number="{ row }"><button class="link-button">{{ row.invoice_number }}</button></template>
      <template #stt_number="{ row }"><button class="link-button">{{ row.stt_number || '-' }}</button></template>
      <template #invoice_status="{ row }"><span :class="['badge', row.invoice_status === 'verified' ? 'success' : row.invoice_status === 'rejected' ? 'danger' : 'muted']">{{ label(row.invoice_status) }}</span></template>
    </DataTable>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import ListToolbar from '../components/ListToolbar.vue'
import DataTable from '../components/DataTable.vue'
import { apiFetch } from '../api/client'

const rows = ref([])
const search = ref('')
const status = ref('')
const perPage = ref(20)
const columns = [
  { key: 'invoice_number', label: '发票号', width: '150px' },
  { key: 'stt_number', label: 'STT', width: '150px' },
  { key: 'invoice_date', label: '日期', width: '120px' },
  { key: 'invoice_type', label: '类型', width: '100px' },
  { key: 'net_amount', label: '金额', width: '120px' },
  { key: 'matched_booking_id', label: '匹配运单', width: '150px' },
  { key: 'invoice_status', label: '状态', width: '110px' }
]
const filteredRows = computed(() => {
  if (!search.value) return rows.value
  const key = search.value.toLowerCase()
  return rows.value.filter((r) => JSON.stringify(r).toLowerCase().includes(key))
})
function label(value) {
  return value === 'verified' ? '已验收' : value === 'rejected' ? '异常' : '待验收'
}
function clear() {
  search.value = ''
  status.value = ''
  load()
}
async function load() {
  const qs = new URLSearchParams({ type: 'logistics', status: status.value })
  const data = await apiFetch(`/api/invoices/items?${qs}`)
  rows.value = data.items || []
}
onMounted(load)
</script>

