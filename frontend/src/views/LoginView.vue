<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true

  const result = await authStore.login(username.value, password.value)

  loading.value = false

  if (!result.success) {
    error.value = result.error
  }
}
</script>

<template>
  <div class="login">
    <h2>Login</h2>

    <form @submit.prevent="handleLogin">
      <div v-if="error" class="error">{{ error }}</div>

      <div class="form-group">
        <label for="username">Usuario</label>
        <input
          id="username"
          v-model="username"
          type="text"
          required
          placeholder="Seu usuario"
        />
      </div>

      <div class="form-group">
        <label for="password">Senha</label>
        <input
          id="password"
          v-model="password"
          type="password"
          required
          placeholder="Sua senha"
        />
      </div>

      <button type="submit" :disabled="loading" class="btn-submit">
        {{ loading ? 'Entrando...' : 'Entrar' }}
      </button>
    </form>
  </div>
</template>

<style scoped>
.login {
  max-width: 400px;
  margin: 40px auto;
  padding: 30px;
}

h2 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 16px;
}

input:focus {
  outline: none;
  border-color: #3498db;
}

.error {
  background-color: #fee;
  color: #c00;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 20px;
}

.btn-submit {
  width: 100%;
  padding: 14px;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn-submit:hover:not(:disabled) {
  background-color: #2980b9;
}

.btn-submit:disabled {
  background-color: #95a5a6;
  cursor: not-allowed;
}
</style>
