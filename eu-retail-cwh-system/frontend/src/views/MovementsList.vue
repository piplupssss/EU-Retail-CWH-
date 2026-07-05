<template>
  <section class="page">
    <PageHeader eyebrow="INVENTORY MOVEMENTS" title="出入流水" subtitle="点击 Product No 查看 SKU 详情" />
    <ListToolbar v-model:search="search" v-model:per-page="perPage" placeholder="搜索 Product No / 操作..." @clear="clear" @update:search="load" @update:per-page="load">
      <template #filters>
        <select v-model="movementType" @change="load">
          <option value="">全部类型</option>
          <option value="inbound">入库</option>
          <option value="outbound">出库</option>
        </select>
      </template>
      <template #actions>
        <button class="btn primary">导出流水</button>
      </template>
    </ListToolbar>
    <DataTable :columns="columns" :rows="rows" id-key="id">
      <template #product_number="{ row }"><button class="link-button">{{ row.product_number }}</button></template>
      <template #quantity="{ row }"><strong>{{ row.quantity }}</strong></template>
    </DataTable>
    <p class="pager">共 {{ total }} 条，第 {{ page }} 页</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import ListToolbar from '../components/ListToolbar.vue'
import DataTable from '../components/DataTable.vue'
import { apiFetch } from '../api/client'

const rows = ref([])
const total = ref(0)
const page = ref(1)
const perPage = ref(20)
const search = ref('')
const movementType = ref('')
const columns = [
  { key: 'movement_date', label: '出入库日期', width: '130px' },
  { key: 'movement_label', label: '类型', width: '90px' },
  { key: 'product_number', label: 'Product No', width: '150px' },
  { key: 'product_description', label: 'Product Description' },
  { key: 'operation_id', label: '操作编号', width: '180px' },
  { key: 'quantity', label: '数量', width: '90px' }
]

function clear() {
  search.value = ''
  movementType.value = ''
  load()
}
async function load() {
  const qs = new URLSearchParams({ page: page.value, per_page: perPage.value, q: search.value, movement_type: movementType.value })
  const data = await apiFetch(`/api/inventory/movements?${qs}`)
  rows.value = data.items || []
  total.value = data.total || 0
}
onMounted(load)
</script>

