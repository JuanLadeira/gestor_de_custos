<template>
  <div class="flex h-screen bg-slate-50 overflow-hidden">
    <!-- Sidebar -->
    <aside class="w-60 shrink-0 bg-slate-900 flex flex-col">
      <div class="h-16 flex items-center px-5 border-b border-white/5">
        <div class="flex items-center gap-2.5">
          <div class="w-7 h-7 bg-violet-500 rounded-lg flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="white" class="w-4 h-4">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <div>
            <p class="text-white text-xs font-semibold leading-none">Admin Panel</p>
            <p class="text-slate-500 text-xs mt-0.5 truncate max-w-28">{{ adminStore.username }}</p>
          </div>
        </div>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-0.5">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all"
          :class="route.path === item.to
            ? 'bg-violet-600 text-white'
            : 'text-slate-400 hover:bg-white/5 hover:text-white'"
        >
          <span class="text-base leading-none">{{ item.emoji }}</span>
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="px-3 py-4 border-t border-white/5">
        <button
          @click="adminStore.logout()"
          class="flex items-center gap-2 px-3 py-2 w-full text-slate-500 hover:text-white text-sm transition-colors rounded-lg hover:bg-white/5"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
          </svg>
          Sair
        </button>
      </div>
    </aside>

    <!-- Main -->
    <main class="flex-1 overflow-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'
import { useAdminAuthStore } from '../../stores/adminAuth'

const adminStore = useAdminAuthStore()
const route = useRoute()

const navItems = [
  { to: '/admin/tenants', label: 'Tenants', emoji: '🏠' },
  { to: '/admin/planos', label: 'Planos', emoji: '📦' },
  { to: '/admin/assinaturas', label: 'Assinaturas', emoji: '💳' },
]
</script>
