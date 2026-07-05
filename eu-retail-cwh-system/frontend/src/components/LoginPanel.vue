<template>
  <div class="login-page">
    <section class="login-card">
      <img src="../assets/cwh_logo.jpg" alt="CWH" class="login-logo" />
      <p class="eyebrow">EU RETAIL CWH SYSTEM</p>
      <h1>欧洲零售中央仓系统</h1>
      <p class="login-copy">物流、库存、发票和数据备份均在本地处理。</p>
      <form @submit.prevent="submit">
        <label>
          账号
          <input v-model.trim="username" autocomplete="username" placeholder="Qiteng" />
        </label>
        <label>
          密码
          <input v-model="password" type="password" autocomplete="current-password" />
        </label>
        <p v-if="error" class="form-error">{{ error }}</p>
        <button class="btn primary login-submit" :disabled="loading">
          {{ loading ? '登录中...' : '登录系统' }}
        </button>
      </form>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { login } from '../api/client'

const emit = defineEmits(['authenticated'])
const username = ref('Qiteng')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await login(username.value, password.value)
    emit('authenticated')
  } catch {
    error.value = '账号或密码不正确'
  } finally {
    loading.value = false
  }
}
</script>

