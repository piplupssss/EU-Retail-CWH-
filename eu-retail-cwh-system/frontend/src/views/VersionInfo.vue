<template>
  <section class="page">
    <PageHeader eyebrow="VERSION INFORMATION" title="版本信息" subtitle="当前版本、数据规则和更新记录" />
    <section class="panel">
      <h2>版本更新</h2>
      <div class="version-cards">
        <article><span>当前版本</span><strong>{{ current }}</strong></article>
        <article><span>最新版本</span><strong>{{ latest }}</strong></article>
        <article><span>更新源</span><strong>Qiteng 的 GitHub</strong></article>
      </div>
      <button class="btn primary" @click="check" :disabled="loading">{{ loading ? '检查中...' : '检查版本更新' }}</button>
      <p class="muted-text">{{ message }}</p>
    </section>
    <section class="panel">
      <h2>核心规则</h2>
      <div class="rule-grid">
        <article><span>库存主键</span><b>仓库 + Product Number</b></article>
        <article><span>图片匹配</span><b>Bom Code 优先 / Product No 兜底</b></article>
        <article><span>更新方式</span><b>仅下载更新包，不上传业务数据</b></article>
      </div>
    </section>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import PageHeader from '../components/PageHeader.vue'
import { apiFetch } from '../api/client'

const current = ref('VN62')
const latest = ref('未检查')
const loading = ref(false)
const message = ref('尚未检查更新')

async function check() {
  loading.value = true
  try {
    const data = await apiFetch('/api/update/check')
    current.value = data.current_version || current.value
    latest.value = data.latest_version || data.version || '未发现'
    message.value = data.update_available ? '发现新版本，可以下载更新。' : '当前已经是最新版本。'
  } catch {
    message.value = '检查失败，请确认网络或更新源。'
  } finally {
    loading.value = false
  }
}
</script>

