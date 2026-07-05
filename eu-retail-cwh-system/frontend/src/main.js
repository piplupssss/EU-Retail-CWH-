import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import LogisticsDashboard from './views/LogisticsDashboard.vue'
import InventoryDashboard from './views/InventoryDashboard.vue'
import InvoiceDashboard from './views/InvoiceDashboard.vue'
import LogisticsList from './views/LogisticsList.vue'
import InventoryList from './views/InventoryList.vue'
import MovementsList from './views/MovementsList.vue'
import AcceptanceList from './views/AcceptanceList.vue'
import DataManagement from './views/DataManagement.vue'
import VersionInfo from './views/VersionInfo.vue'
import './styles/design-system.css'

const routes = [
  { path: '/', redirect: '/logistics' },
  { path: '/logistics', component: LogisticsDashboard },
  { path: '/inventory', component: InventoryDashboard },
  { path: '/invoices', component: InvoiceDashboard },
  { path: '/shipments', component: LogisticsList },
  { path: '/stock', component: InventoryList },
  { path: '/movements', component: MovementsList },
  { path: '/acceptance', component: AcceptanceList },
  { path: '/data', component: DataManagement },
  { path: '/version', component: VersionInfo }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

createApp(App).use(router).mount('#app')

