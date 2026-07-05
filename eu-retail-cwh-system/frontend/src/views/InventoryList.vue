<template>
  <section class="page">
    <PageHeader eyebrow="INVENTORY LIST" title="库存清单" subtitle="全部 SKU 库存明细" />
    <ListToolbar v-model:search="search" v-model:per-page="perPage" placeholder="搜索产品 / 描述..." @clear="clear" @update:search="load" @update:per-page="load">
      <template #filters>
        <select v-model="warehouse" @change="load">
          <option value="">全部仓库</option>
          <option value="Lodz warehouse">Lodz</option>
          <option value="Bydgoszcz warehouse">Bydgoszcz</option>
        </select>
      </template>
      <template #actions>
        <button class="btn primary">导出库存清单</button>
        <button class="btn primary">导出流水</button>
      </template>
    </ListToolbar>
    <DataTable :columns="columns" :rows="rows" id-key="id">
      <template #product_number="{ row }"><button class="link-button">{{ row.product_number }}</button></template>
      <template #image_path="{ row }">
        <img v-if="row.image_path" class="thumb" :src="`/static/images/${row.image_path}`" alt="Photo" />
        <span v-else>-</span>
      </template>
      <template #bom_code="{ row }">{{ row.bom_code || '/' }}</template>
      <template #inventory="{ row }"><strong>{{ row.inventory }}</strong></template>
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
const warehouse = ref('')
const columns = [
  { key: 'product_number', label: 'Product No', width: '150px' },
  { key: 'image_path', label: 'Photo', width: '72px' },
  { key: 'bom_code', label: 'BOM 编号', width: '120px' },
  { key: 'product_description', label: 'Product Description' },
  { key: 'category', label: '物料品类', width: '130px' },
  { key: 'category_2', label: '适用产品', width: '120px' },
  { key: 'instruction', label: '归属国家', width: '110px' },
  { key: 'inventory', label: 'Inventory', width: '110px' }
]

function clear() {
  search.value = ''
  warehouse.value = ''
  load()
}

async function load() {
  const qs = new URLSearchParams({ page: page.value, per_page: perPage.value, q: search.value, warehouse: warehouse.value })
  const data = await apiFetch(`/api/inventory?${qs}`)
  rows.value = data.data || []
  total.value = data.total || 0
}
onMounted(load)
</script>

