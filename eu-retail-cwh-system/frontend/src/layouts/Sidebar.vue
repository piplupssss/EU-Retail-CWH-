<template>
  <aside class="sidebar">
    <div class="brand">
      <img src="../assets/cwh_logo.jpg" alt="CWH" />
      <div>
        <strong>EU CWH</strong>
        <span>Retail Operations</span>
      </div>
    </div>

    <nav v-for="group in navGroups" :key="group.label" class="nav-group">
      <p>{{ group.label }}</p>
      <RouterLink v-for="item in group.items" :key="item.to" :to="item.to" class="nav-item">
        <span>{{ item.icon }}</span>
        <span>{{ item.label }}</span>
        <small v-if="item.badge" :class="{ live: item.badge === 'LIVE' }">{{ item.badge }}</small>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup>
const navGroups = [
  {
    label: '工作台',
    items: [
      { to: '/logistics', icon: '🚚', label: '物流看板', badge: 'LIVE' },
      { to: '/inventory', icon: '📋', label: '库存看板', badge: '周度' },
      { to: '/invoices', icon: '💰', label: '发票看板', badge: '月度' }
    ]
  },
  {
    label: '清单',
    items: [
      { to: '/shipments', icon: '🚚', label: '物流清单', badge: 'LIVE' },
      { to: '/stock', icon: '📊', label: '库存清单', badge: '周度' },
      { to: '/movements', icon: '📄', label: '出入流水', badge: '月度' },
      { to: '/acceptance', icon: '🧾', label: '验收清单', badge: '月度' }
    ]
  },
  {
    label: '数据',
    items: [{ to: '/data', icon: '🗂️', label: '数据管理中心' }]
  },
  {
    label: '系统',
    items: [{ to: '/version', icon: 'ℹ️', label: '版本信息' }]
  }
]
</script>
