<template>
  <section class="page">
    <PageHeader eyebrow="DATA MANAGEMENT" title="数据管理中心" subtitle="集中导入、导出、备份和源文件" />
    <div class="info-grid">
      <article class="info-card"><h3>数据管理</h3><p>物流、库存、流水、发票、图片的导入与导出集中在同一块。</p></article>
      <article class="info-card"><h3>备份与恢复</h3><p>完整包用于换电脑、同步给同事和灾备恢复。</p></article>
      <article class="info-card"><h3>源文件管理</h3><p>清理源文件只释放体积，不撤销已导入数据。</p></article>
    </div>
    <section class="panel">
      <h2>一、数据管理</h2>
      <div class="maintenance-grid">
        <article v-for="card in dataCards" :key="card.title" class="maintenance-card">
          <span class="card-icon">{{ card.icon }}</span>
          <h3>{{ card.title }}</h3>
          <p>{{ card.desc }}</p>
          <small>{{ card.hint }}</small>
          <div class="card-actions">
            <button class="btn danger">{{ card.importText }}</button>
            <button class="btn primary">{{ card.exportText }}</button>
          </div>
        </article>
      </div>
    </section>
    <section class="panel">
      <h2>二、备份与恢复</h2>
      <div class="maintenance-grid two">
        <article class="maintenance-card">
          <span class="card-icon">💾</span>
          <h3>导出全部仓库完整包</h3>
          <p>导出 core backup Excel 和 images 文件夹，用于迁移和同步。</p>
          <div class="card-actions"><button class="btn primary">导出完整包</button></div>
        </article>
        <article class="maintenance-card danger-card">
          <span class="card-icon">🧯</span>
          <h3>恢复完整包</h3>
          <p>选择完整包后恢复结构化数据和图片，属于谨慎操作。</p>
          <div class="card-actions"><button class="btn secondary">选择文件</button><button class="btn danger">恢复完整包</button></div>
        </article>
      </div>
    </section>
  </section>
</template>

<script setup>
import PageHeader from '../components/PageHeader.vue'

const dataCards = [
  { icon: '🚚', title: '物流数据管理', desc: '导入物流数据 / 导出物流清单', hint: '历史重传不覆盖人工核实状态', importText: '导入物流', exportText: '导出' },
  { icon: '📦', title: '库存数据管理', desc: '刷新库存 / 导出库存清单', hint: '只刷新库存数，主数据由校准和维护控制', importText: '刷新库存', exportText: '导出' },
  { icon: '📅', title: '库存流水管理', desc: '导入 Specyfikacja / 导出流水', hint: '自动识别出入库流水', importText: '导入流水', exportText: '导出' },
  { icon: '💳', title: '发票数据管理', desc: '上传发票生成明细，回传验收明细写入系统', hint: '发票类型自动识别', importText: '导入发票', exportText: '导出明细' },
  { icon: '🖼', title: '图片管理', desc: 'SKU 产品图片', hint: '按文件名匹配 Bom Code；Bom Code 为空时匹配 Product No', importText: '上传图片', exportText: '查看' }
]
</script>

