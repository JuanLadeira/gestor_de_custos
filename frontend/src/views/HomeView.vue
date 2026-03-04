<script setup lang="ts">
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
</script>

<template>
  <div class="home">
    <h1>Gestor de Custos Compartilhados</h1>
    <p>Sistema para gestao de custos compartilhados entre moradores.</p>

    <div v-if="authStore.isAuthenticated" class="welcome">
      <p>Bem-vindo, <strong>{{ authStore.username }}</strong>!</p>
      <div class="actions">
        <router-link to="/custos" class="btn btn-primary">Ver Custos</router-link>
        <router-link to="/rateios" class="btn btn-secondary">Ver Rateios</router-link>
      </div>
    </div>

    <div v-else class="login-prompt">
      <p>Faca login para acessar o sistema.</p>
      <router-link to="/login" class="btn btn-primary">Entrar</router-link>
    </div>
  </div>
</template>

<style scoped>
.home {
  text-align: center;
  padding: 40px 20px;
}

h1 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.welcome, .login-prompt {
  margin-top: 40px;
}

.actions {
  margin-top: 20px;
  display: flex;
  gap: 20px;
  justify-content: center;
}

.btn {
  display: inline-block;
  padding: 12px 24px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 500;
  transition: background-color 0.2s;
}

.btn-primary {
  background-color: #3498db;
  color: white;
}

.btn-primary:hover {
  background-color: #2980b9;
}

.btn-secondary {
  background-color: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background-color: #7f8c8d;
}
</style>
