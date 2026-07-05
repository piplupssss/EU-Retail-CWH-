const TOKEN_KEY = 'eucwh_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

export async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const res = await fetch(path, { ...options, headers })
  if (!res.ok) {
    if (res.status === 401) {
      setToken('')
      window.dispatchEvent(new CustomEvent('eucwh:unauthorized'))
    }
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  const type = res.headers.get('content-type') || ''
  return type.includes('application/json') ? res.json() : res.blob()
}

export async function login(username, password) {
  const data = await apiFetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password })
  })
  setToken(data.token)
  return data
}

export async function checkAuth() {
  if (!getToken()) return false
  try {
    await apiFetch('/api/auth/check')
    return true
  } catch {
    return false
  }
}
