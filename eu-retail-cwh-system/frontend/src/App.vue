<template>
  <LoginPanel v-if="!authenticated" @authenticated="authenticated = true" />
  <div v-else class="app-shell">
    <Sidebar />
    <main class="app-main">
      <Topbar />
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { checkAuth, getToken, setToken } from './api/client'
import LoginPanel from './components/LoginPanel.vue'
import Sidebar from './layouts/Sidebar.vue'
import Topbar from './layouts/Topbar.vue'

const authenticated = ref(Boolean(getToken()))

function logoutToLogin() {
  setToken('')
  authenticated.value = false
}

onMounted(async () => {
  window.addEventListener('eucwh:unauthorized', logoutToLogin)
  if (authenticated.value) authenticated.value = await checkAuth()
})

onUnmounted(() => {
  window.removeEventListener('eucwh:unauthorized', logoutToLogin)
})
</script>
