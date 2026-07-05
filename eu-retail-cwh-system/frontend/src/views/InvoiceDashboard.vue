<template>
  <section class="page">
    <PageHeader eyebrow="INVOICE ACCEPTANCE" title="发票看板" subtitle="费用预算、发票验收和匹配状态" />
    <div class="filter-strip">
      <label>费用类型</label>
      <select>
        <option>物流费用验收</option>
        <option disabled>仓储操作费用验收（开发中）</option>
      </select>
    </div>
    <div class="kpi-grid">
      <article class="kpi-card"><span>年度预算</span><strong class="blue">{{ money(data.budget_usd) }}</strong><small>USD</small></article>
      <article class="kpi-card"><span>已验收金额</span><strong class="green">{{ money(data.logistics_usd) }}</strong><small>{{ pln(data.logistics_pln) }}</small></article>
      <article class="kpi-card"><span>待验收金额</span><strong class="orange">{{ money(data.pending_logistics_usd) }}</strong><small>{{ pln(data.pending_logistics_pln) }}</small></article>
      <article class="kpi-card"><span>剩余预算</span><strong class="green">{{ money(data.remaining_usd) }}</strong><small>匹配率 {{ data.invoice_match_rate || 0 }}%</small></article>
    </div>
    <article class="panel">
      <h2>发票批次</h2>
      <DataTable :columns="columns" :rows="data.invoices || []" id-key="id" />
    </article>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import DataTable from '../components/DataTable.vue'
import { apiFetch } from '../api/client'

const data = ref({})
const columns = [
  { key: 'invoice_number', label: '发票号' },
  { key: 'invoice_date', label: '日期' },
  { key: 'invoice_type', label: '类型' },
  { key: 'total_net', label: '金额' },
  { key: 'status', label: '状态' },
  { key: 'matched_count', label: '已匹配' }
]

function money(v) { return `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}` }
function pln(v) { return `PLN ${Number(v || 0).toLocaleString()}` }
onMounted(async () => { data.value = await apiFetch('/api/invoices/budget') })
</script>

