<template>
  <section class="page">
    <PageHeader eyebrow="LOGISTICS WORKSPACE" title="物流看板" subtitle="实时运单数据概览 · 状态、类型、国家和费用趋势" />
    <div class="filter-strip">
      <label>月份</label>
      <select v-model="month" @change="load">
        <option value="">全部</option>
        <option v-for="m in months" :key="m" :value="m">{{ m }}</option>
      </select>
    </div>
    <div class="kpi-grid">
      <article v-for="card in cards" :key="card.label" class="kpi-card">
        <span>{{ card.label }}</span>
        <strong :class="card.tone">{{ card.value }}</strong>
        <small>{{ card.hint }}</small>
      </article>
    </div>
    <div class="dashboard-grid">
      <article class="panel">
        <h2>运单结构</h2>
        <div class="simple-bars">
          <div v-for="item in statusRows" :key="item.shipment_status" class="bar-row">
            <span>{{ item.shipment_status }}</span>
            <div><i :style="{ width: pct(item.count, totalShipments) + '%' }" /></div>
            <b>{{ item.count }}</b>
          </div>
        </div>
      </article>
      <article class="panel">
        <h2>类型分布</h2>
        <div class="simple-bars">
          <div v-for="item in typeRows" :key="item.shipment_type" class="bar-row">
            <span>{{ item.label }}</span>
            <div><i :style="{ width: pct(item.count, totalShipments) + '%' }" /></div>
            <b>{{ item.count }}</b>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import { apiFetch } from '../api/client'

const month = ref('')
const summary = ref({})
const statusRows = ref([])
const typeRows = ref([])
const months = ref(['2026-04', '2026-03', '2026-02', '2026-01'])

const totalShipments = computed(() => Number(summary.value.total_shipments || 0))
const cards = computed(() => [
  { label: '总运单数', value: summary.value.total_shipments || 0, hint: '当前筛选范围', tone: 'blue' },
  { label: '已交付', value: summary.value.delivered || 0, hint: '已完成配送', tone: 'green' },
  { label: '待核实', value: summary.value.pending_verify || 0, hint: '需要批量核实', tone: 'purple' },
  { label: '异常单', value: summary.value.exception || 0, hint: '需要人工处理', tone: 'red' },
  { label: '费用', value: money(summary.value.total_price), hint: '不含税金额', tone: 'blue' }
])

function money(value) {
  return `$${Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}`
}

function pct(value, total) {
  if (!total) return 0
  return Math.max(4, Math.round((Number(value || 0) / total) * 100))
}

async function load() {
  const qs = month.value ? `?month=${month.value}` : ''
  summary.value = await apiFetch(`/api/dashboard/summary${qs}`)
  statusRows.value = await apiFetch(`/api/dashboard/status_distribution${qs}`)
  typeRows.value = await apiFetch(`/api/dashboard/type_distribution${qs}`)
}

onMounted(load)
</script>

