<template>
  <section class="page">
    <PageHeader eyebrow="INVENTORY WORKSPACE" title="库存看板" subtitle="库存规模、货值、风险和提醒线" />
    <div class="filter-strip">
      <label>仓库</label>
      <select v-model="warehouse" @change="load">
        <option value="">全部仓库</option>
        <option value="Lodz warehouse">Lodz 仓库</option>
        <option value="Bydgoszcz warehouse">Bydgoszcz 仓库</option>
      </select>
    </div>
    <div class="kpi-grid">
      <article class="kpi-card"><span>SKU 总数</span><strong class="blue">{{ total }}</strong><small>当前库存条目</small></article>
      <article class="kpi-card"><span>库存总件数</span><strong class="green">{{ pcs }}</strong><small>PCS</small></article>
      <article class="kpi-card"><span>库存总货值</span><strong class="blue">{{ money(valueUsd) }}</strong><small>USD</small></article>
      <article class="kpi-card"><span>更新时间</span><strong>{{ lastUpdated || '-' }}</strong><small>最近库存刷新</small></article>
    </div>
    <article class="panel">
      <h2>库存风险 Top</h2>
      <DataTable :columns="columns" :rows="rows" id-key="product_number">
        <template #product_number="{ row }">
          <RouterLink :to="`/stock?q=${encodeURIComponent(row.product_number || '')}`">{{ row.product_number }}</RouterLink>
        </template>
      </DataTable>
    </article>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import DataTable from '../components/DataTable.vue'
import { apiFetch } from '../api/client'

const warehouse = ref('Lodz warehouse')
const rows = ref([])
const total = ref(0)
const lastUpdated = ref('')
const columns = [
  { key: 'product_number', label: 'Product No' },
  { key: 'product_description', label: 'Product Description' },
  { key: 'category', label: '物料品类' },
  { key: 'inventory', label: '库存' },
  { key: 'ttl_amount', label: '货值' }
]

const pcs = computed(() => rows.value.reduce((sum, r) => sum + Number(r.inventory || 0), 0))
const valueUsd = computed(() => rows.value.reduce((sum, r) => sum + Number(r.ttl_amount || 0), 0))
function money(v) { return `$${Number(v || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })}` }

async function load() {
  const qs = new URLSearchParams({ page: '1', per_page: '10', warehouse: warehouse.value, sort_by: 'ttl_amount', sort_dir: 'desc' })
  const data = await apiFetch(`/api/inventory?${qs}`)
  rows.value = data.data || []
  total.value = data.total || 0
  lastUpdated.value = data.last_updated_at || ''
}

onMounted(load)
</script>

