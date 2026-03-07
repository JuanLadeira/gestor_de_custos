<template>
  <div style="min-height:100vh;display:flex;font-family:'Inter',sans-serif;">

    <!-- Painel esquerdo (decorativo) -->
    <div style="display:none;width:50%;background:#0c0a1e;flex-direction:column;justify-content:space-between;padding:48px;" class="lg-flex">
      <!-- Logo -->
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="width:36px;height:36px;background:#4f46e5;border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="white" style="width:18px;height:18px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33" />
          </svg>
        </div>
        <span style="color:white;font-weight:600;font-size:15px;">Gestor de Custos</span>
      </div>

      <!-- Quote + stats -->
      <div>
        <!-- Glow decorativo -->
        <div style="width:200px;height:200px;background:rgba(99,102,241,0.15);border-radius:50%;filter:blur(60px);margin-bottom:32px;"></div>

        <p style="color:#94a3b8;font-size:20px;line-height:1.6;font-weight:300;margin:0 0 40px;">
          "Chega de planilha. Divida as despesas do grupo com clareza e sem stress."
        </p>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0;border:1px solid rgba(255,255,255,0.06);border-radius:14px;overflow:hidden;">
          <div style="background:rgba(255,255,255,0.03);padding:18px;text-align:center;border-right:1px solid rgba(255,255,255,0.06);">
            <p style="font-size:24px;font-weight:700;color:white;margin:0;">100%</p>
            <p style="font-size:11px;color:#475569;margin:4px 0 0;">transparente</p>
          </div>
          <div style="background:rgba(255,255,255,0.03);padding:18px;text-align:center;border-right:1px solid rgba(255,255,255,0.06);">
            <p style="font-size:24px;font-weight:700;color:white;margin:0;">0</p>
            <p style="font-size:11px;color:#475569;margin:4px 0 0;">conflitos</p>
          </div>
          <div style="background:rgba(255,255,255,0.03);padding:18px;text-align:center;">
            <p style="font-size:24px;font-weight:700;color:white;margin:0;">∞</p>
            <p style="font-size:11px;color:#475569;margin:4px 0 0;">membros</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Painel direito (formulário) -->
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:40px 24px;background:white;">
      <div style="width:100%;max-width:360px;">

        <!-- Logo mobile -->
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:40px;" class="hide-on-large">
          <div style="width:32px;height:32px;background:#4f46e5;border-radius:9px;display:flex;align-items:center;justify-content:center;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="white" style="width:16px;height:16px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33" />
            </svg>
          </div>
          <span style="font-weight:600;color:#0f172a;font-size:14px;">Gestor de Custos</span>
        </div>

        <h1 style="font-size:24px;font-weight:700;color:#0f172a;margin:0 0 6px;">Bem-vindo de volta</h1>
        <p style="font-size:14px;color:#64748b;margin:0 0 32px;">Digite suas credenciais para acessar.</p>

        <!-- Erro -->
        <div v-if="error" style="display:flex;align-items:flex-start;gap:10px;background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:12px 14px;margin-bottom:20px;">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="#ef4444" style="width:16px;height:16px;flex-shrink:0;margin-top:1px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <p style="font-size:13px;color:#b91c1c;margin:0;">{{ error }}</p>
        </div>

        <form @submit.prevent="handleLogin" style="display:flex;flex-direction:column;gap:18px;">
          <div>
            <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:7px;letter-spacing:0.01em;">Usuário</label>
            <input
              v-model="username"
              type="text"
              required
              autocomplete="username"
              placeholder="seu.usuario"
              style="width:100%;border:1.5px solid #e5e7eb;border-radius:10px;padding:11px 14px;font-size:14px;color:#111827;background:white;outline:none;transition:border-color 0.15s;box-sizing:border-box;"
              @focus="e => (e.target as HTMLInputElement).style.borderColor='#4f46e5'"
              @blur="e => (e.target as HTMLInputElement).style.borderColor='#e5e7eb'"
            />
          </div>

          <div>
            <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:7px;letter-spacing:0.01em;">Senha</label>
            <input
              v-model="password"
              type="password"
              required
              autocomplete="current-password"
              placeholder="••••••••"
              style="width:100%;border:1.5px solid #e5e7eb;border-radius:10px;padding:11px 14px;font-size:14px;color:#111827;background:white;outline:none;transition:border-color 0.15s;box-sizing:border-box;"
              @focus="e => (e.target as HTMLInputElement).style.borderColor='#4f46e5'"
              @blur="e => (e.target as HTMLInputElement).style.borderColor='#e5e7eb'"
            />
          </div>

          <button
            type="submit"
            :disabled="loading"
            style="width:100%;background:#4f46e5;color:white;font-size:14px;font-weight:600;padding:13px;border-radius:10px;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;margin-top:4px;transition:background 0.15s;box-shadow:0 4px 14px rgba(79,70,229,0.3);"
            :style="loading ? 'opacity:0.6;cursor:not-allowed;' : ''"
            @mouseenter="e => { if (!loading) (e.target as HTMLButtonElement).style.background='#4338ca' }"
            @mouseleave="e => (e.target as HTMLButtonElement).style.background='#4f46e5'"
          >
            <svg v-if="loading" class="animate-spin" style="width:16px;height:16px;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle style="opacity:0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path style="opacity:0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            {{ loading ? 'Entrando...' : 'Entrar' }}
          </button>
        </form>

        <p style="margin-top:28px;text-align:center;font-size:13px;color:#94a3b8;">
          Ainda não tem conta?
          <a href="/" style="color:#4f46e5;font-weight:600;text-decoration:none;">Ver planos</a>
        </p>
      </div>
    </div>
  </div>
</template>

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
  if (!result.success) error.value = result.error
}
</script>

<style scoped>
@media (min-width: 1024px) {
  .lg-flex { display: flex !important; }
  .hide-on-large { display: none !important; }
}
</style>
