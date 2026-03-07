<template>
  <div class="flex flex-col h-full">
    <div class="h-16 border-b border-slate-200 bg-white flex items-center px-6 shrink-0">
      <div>
        <h1 class="text-base font-semibold text-slate-900">Início</h1>
        <p class="text-xs text-slate-500">Bem-vindo, {{ authStore.username }}</p>
      </div>
    </div>
    <div class="flex-1 overflow-auto p-6 flex flex-col items-center justify-center">
      <div class="text-center max-w-sm">
        <div class="w-14 h-14 bg-indigo-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-7 h-7 text-indigo-600">
            <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
          </svg>
        </div>
        <h2 class="text-lg font-semibold text-slate-900 mb-1">Use o menu lateral</h2>
        <p class="text-sm text-slate-500">Acesse Custos ou Rateios para gerenciar as despesas do grupo.</p>
        <div class="flex gap-3 mt-6 justify-center">
          <RouterLink to="/custos" class="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
            Ver Custos
          </RouterLink>
          <RouterLink to="/rateios" class="bg-white hover:bg-slate-50 text-slate-700 text-sm font-medium px-4 py-2 rounded-lg border border-slate-200 transition-colors">
            Ver Rateios
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth'
const authStore = useAuthStore()
</script>
