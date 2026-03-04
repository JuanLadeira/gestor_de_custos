import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/client'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const username = ref<string | null>(localStorage.getItem('username'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(usernameInput: string, password: string) {
    try {
      const response = await api.login(usernameInput, password)
      token.value = response.data.access_token
      username.value = usernameInput
      localStorage.setItem('token', response.data.access_token)
      localStorage.setItem('username', usernameInput)
      router.push('/')
      return { success: true }
    } catch (error: any) {
      return {
        success: false,
        error: error.response?.data?.detail || 'Erro ao fazer login',
      }
    }
  }

  function logout() {
    token.value = null
    username.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    router.push('/login')
  }

  return {
    token,
    username,
    isAuthenticated,
    login,
    logout,
  }
})
