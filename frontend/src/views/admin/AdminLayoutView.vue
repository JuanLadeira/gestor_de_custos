<template>
  <div style="display:flex;height:100vh;overflow:hidden;font-family:'Inter',sans-serif;">

    <!-- Sidebar -->
    <aside style="width:228px;flex-shrink:0;background:#0c0a1e;display:flex;flex-direction:column;border-right:1px solid rgba(255,255,255,0.06);">

      <!-- Brand -->
      <div style="height:64px;display:flex;align-items:center;padding:0 18px;border-bottom:1px solid rgba(255,255,255,0.06);flex-shrink:0;">
        <div style="display:flex;align-items:center;gap:10px;">
          <div style="width:32px;height:32px;background:#7c3aed;border-radius:9px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="white" style="width:16px;height:16px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
            </svg>
          </div>
          <div>
            <p style="color:white;font-size:13px;font-weight:600;margin:0;line-height:1.2;">Admin Panel</p>
            <p style="color:#6b7280;font-size:11px;margin:0;margin-top:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:130px;">{{ adminStore.username }}</p>
          </div>
        </div>
      </div>

      <!-- Nav -->
      <nav style="flex:1;padding:12px 10px;display:flex;flex-direction:column;gap:2px;">
        <p style="font-size:10px;font-weight:600;color:#374151;text-transform:uppercase;letter-spacing:.08em;padding:6px 8px 4px;margin:0;">Gestão</p>
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          style="display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;text-decoration:none;font-size:13px;font-weight:500;transition:background .15s,color .15s;"
          :style="route.path === item.to
            ? 'background:#7c3aed;color:white;'
            : 'color:#9ca3af;'"
          @mouseenter="e => { if (route.path !== item.to) (e.currentTarget as HTMLElement).style.background='rgba(255,255,255,0.05)'; (e.currentTarget as HTMLElement).style.color='white' }"
          @mouseleave="e => { if (route.path !== item.to) { (e.currentTarget as HTMLElement).style.background=''; (e.currentTarget as HTMLElement).style.color='#9ca3af' } }"
        >
          <span style="width:16px;height:16px;display:flex;flex-shrink:0;" v-html="item.icon" />
          {{ item.label }}
        </RouterLink>
      </nav>

      <!-- Logout -->
      <div style="padding:10px;border-top:1px solid rgba(255,255,255,0.06);flex-shrink:0;">
        <button
          @click="adminStore.logout()"
          style="display:flex;align-items:center;gap:10px;padding:8px 10px;width:100%;background:none;border:none;cursor:pointer;border-radius:8px;color:#6b7280;font-size:13px;font-weight:500;transition:background .15s,color .15s;font-family:inherit;"
          @mouseenter="e => { (e.currentTarget as HTMLElement).style.background='rgba(255,255,255,0.05)'; (e.currentTarget as HTMLElement).style.color='white' }"
          @mouseleave="e => { (e.currentTarget as HTMLElement).style.background=''; (e.currentTarget as HTMLElement).style.color='#6b7280' }"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor" style="width:16px;height:16px;flex-shrink:0;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
          </svg>
          Sair
        </button>
      </div>
    </aside>

    <!-- Main -->
    <main style="flex:1;overflow:auto;background:#f8fafc;">
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
  {
    to: '/admin/tenants',
    label: 'Tenants',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" /></svg>`,
  },
  {
    to: '/admin/planos',
    label: 'Planos',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M21 11.25v8.25a1.5 1.5 0 01-1.5 1.5H5.25a1.5 1.5 0 01-1.5-1.5v-8.25M12 4.875A2.625 2.625 0 109.375 7.5H12m0-2.625V7.5m0-2.625A2.625 2.625 0 1114.625 7.5H12m0 0V21m-8.625-9.75h18c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125h-18c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" /></svg>`,
  },
  {
    to: '/admin/assinaturas',
    label: 'Assinaturas',
    icon: `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" /></svg>`,
  },
]
</script>
