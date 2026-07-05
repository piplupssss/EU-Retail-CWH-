<template>
  <section class="page">
    <PageHeader eyebrow="SHIPMENT LIST" title="物流清单" subtitle="点击 STT / Booking 查看单条详情；勾选多条进入批量维护" />
    <ListToolbar v-model:search="search" v-model:per-page="perPage" placeholder="搜索 Booking ID / 国家 / 收件人..." @clear="clear" @update:search="load" @update:per-page="load">
      <template #filters>
        <select v-model="status" @change="load">
          <option value="">全部状态</option>
          <option>已交付</option>
          <option>待核实</option>
          <option>运输中</option>
          <option>异常单</option>
        </select>
      </template>
      <template #actions>
        <button class="btn success">批量核实</button>
        <button class="btn secondary">维护所选</button>
        <button class="btn secondary">回收站</button>
        <button class="btn primary">导出物流清单</button>
      </template>
    </ListToolbar>
    <DataTable :columns="columns" :rows="rows" id-key="booking_id">
      <template #stt_number="{ row }">
        <button class="link-button">{{ row.stt_number || row.booking_id }}</button>
      </template>
      <template #display_status="{ row }"><span :class="statusClass(row.display_status)">{{ row.display_status }}</span></template>
      <template #shipment_type_label="{ row }"><span class="plain-cell">{{ row.shipment_type_label }}</span></template>
      <template #accepted_amount="{ row }">{{ row.accepted_amount ?? '-' }}</template>
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
const status = ref('')
const columns = [
  { key: 'stt_number', label: 'STT / Booking', width: '160px' },
  { key: 'display_status', label: '物流状态', width: '110px' },
  { key: 'shipment_type_label', label: '类型', width: '130px' },
  { key: 'demand_country', label: '国家', width: '80px' },
  { key: 'pickup_date', label: '发货日期', width: '120px' },
  { key: 'actual_delivery_date', label: '实际交付', width: '120px' },
  { key: 'verify_status', label: '验收状态', width: '120px' },
  { key: 'accepted_amount', label: '验收金额', width: '120px' }
]

function statusClass(value) {
  return ['badge', value === '已交付' ? 'success' : value === '异常单' ? 'danger' : value === '运输中' ? 'info' : 'muted']
}

function clear() {
  search.value = ''
  status.value = ''
  load()
}

async function load() {
  const qs = new URLSearchParams({ page: page.value, per_page: perPage.value, search: search.value, ds: status.value })
  const data = await apiFetch(`/api/shipments?${qs}`)
  rows.value = data.shipments || []
  total.value = data.total || 0
}
onMounted(load)
</script>

