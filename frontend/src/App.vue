<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, RouterLink, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'

const route = useRoute()
const authStore = useAuthStore()

const isAdminRoute = computed(() => route.path.startsWith('/admin'))
const showSidebar = computed(() => !!route.meta.requiresAuth && authStore.isAuthenticated)

const navItems = [
  {
    to: '/custos',
    label: 'Custos',
    permission: 'custo:read',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />`,
  },
  {
    to: '/membros',
    label: 'Membros',
    permission: 'usuario:read',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />`,
  },
  {
    to: '/perfis',
    label: 'Perfis',
    permission: 'profile:read',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12c0 1.268-.63 2.39-1.593 3.068a3.745 3.745 0 01-1.043 3.296 3.745 3.745 0 01-3.296 1.043A3.745 3.745 0 0112 21c-1.268 0-2.39-.63-3.068-1.593a3.746 3.746 0 01-3.296-1.043 3.745 3.745 0 01-1.043-3.296A3.745 3.745 0 013 12c0-1.268.63-2.39 1.593-3.068a3.745 3.745 0 011.043-3.296 3.746 3.746 0 013.296-1.043A3.746 3.746 0 0112 3c1.268 0 2.39.63 3.068 1.593a3.746 3.746 0 013.296 1.043 3.746 3.746 0 011.043 3.296A3.745 3.745 0 0121 12z" />`,
  },
  {
    to: '/campanhas',
    label: 'Campanhas',
    permission: 'campanha:read',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M10.34 15.84c-.688-.06-1.386-.09-2.09-.09H7.5a4.5 4.5 0 110-9h.75c.704 0 1.402-.03 2.09-.09m0 9.18c.253.962.584 1.892.985 2.783.247.55.06 1.21-.463 1.511l-.657.38c-.551.318-1.26.117-1.527-.461a20.845 20.845 0 01-1.44-4.282m3.102.069a18.03 18.03 0 01-.59-4.59c0-1.586.205-3.124.59-4.59m0 9.18a23.848 23.848 0 018.835 2.535M10.34 6.66a23.847 23.847 0 008.835-2.535m0 0A23.74 23.74 0 0018.795 3m.38 1.125a23.91 23.91 0 011.014 5.395m-1.014 8.855c-.118.38-.245.754-.38 1.125m.38-1.125a23.91 23.91 0 001.014-5.395m0-3.46c.495.413.811 1.035.811 1.73 0 .695-.316 1.317-.811 1.73m0-3.46a24.347 24.347 0 010 3.46" />`,
  },
  {
    to: '/inbox',
    label: 'Inbox',
    permission: 'inbox:read',
    icon: `<path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />`,
  },
]

const visibleNav = computed(() =>
  navItems.filter((i) => !i.permission || authStore.can(i.permission)),
)
</script>

<template>
  <!-- Admin routes: layout handled by AdminLayoutView -->
  <RouterView v-if="isAdminRoute" />

  <!-- Authenticated app routes: sidebar layout -->
  <div v-else-if="showSidebar" style="display:flex;height:100vh;background:#f1f5f9;overflow:hidden;">

    <!-- Sidebar -->
    <aside style="width:232px;flex-shrink:0;background:#0f172a;display:flex;flex-direction:column;border-right:1px solid rgba(255,255,255,0.04);">

      <!-- Logo area -->
      <div style="padding:20px 18px 18px;border-bottom:1px solid rgba(255,255,255,0.06);">
        <div style="display:flex;align-items:center;gap:10px;">
          <div style="width:34px;height:34px;background:linear-gradient(135deg,#6366f1,#4f46e5);border-radius:10px;display:flex;align-items:center;justify-content:center;flex-shrink:0;box-shadow:0 4px 12px rgba(99,102,241,0.4);">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="white" style="width:17px;height:17px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33" />
            </svg>
          </div>
          <div>
            <p style="color:white;font-size:13px;font-weight:700;margin:0;letter-spacing:-0.01em;line-height:1.2;">Gestor</p>
            <p style="color:#64748b;font-size:11px;font-weight:500;margin:0;line-height:1.2;">de Custos</p>
          </div>
        </div>
      </div>

      <!-- Nav section -->
      <div style="padding:16px 12px 8px;flex:1;">
        <p style="font-size:10px;font-weight:600;color:#334155;text-transform:uppercase;letter-spacing:0.08em;margin:0 0 8px 8px;">Menu</p>
        <nav style="display:flex;flex-direction:column;gap:2px;">
          <RouterLink
            v-for="item in visibleNav"
            :key="item.to"
            :to="item.to"
            style="display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:9px;font-size:13px;font-weight:500;text-decoration:none;transition:background 0.15s,color 0.15s;"
            :style="route.path === item.to
              ? 'background:#4f46e5;color:white;box-shadow:0 2px 8px rgba(79,70,229,0.35);'
              : 'color:#94a3b8;'"
            @mouseenter="(e) => { if(route.path !== item.to) (e.currentTarget as HTMLElement).style.background='rgba(255,255,255,0.05)'; if(route.path !== item.to) (e.currentTarget as HTMLElement).style.color='#e2e8f0' }"
            @mouseleave="(e) => { if(route.path !== item.to) (e.currentTarget as HTMLElement).style.background=''; if(route.path !== item.to) (e.currentTarget as HTMLElement).style.color='#94a3b8' }"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.6" stroke="currentColor" style="width:16px;height:16px;flex-shrink:0;" v-html="item.icon" />
            {{ item.label }}
          </RouterLink>
        </nav>
      </div>

      <!-- User section -->
      <div style="padding:12px;border-top:1px solid rgba(255,255,255,0.06);">
        <div style="display:flex;align-items:center;gap:10px;padding:10px 10px;border-radius:10px;background:rgba(255,255,255,0.04);">
          <!-- Avatar -->
          <div style="width:32px;height:32px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <span style="color:white;font-size:12px;font-weight:700;line-height:1;">{{ authStore.username?.charAt(0).toUpperCase() }}</span>
          </div>
          <!-- Info -->
          <div style="flex:1;min-width:0;">
            <p style="color:#e2e8f0;font-size:12px;font-weight:600;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.3;">{{ authStore.username }}</p>
            <p style="color:#475569;font-size:10px;font-weight:500;margin:0;line-height:1.3;">Minha conta</p>
          </div>
          <!-- Logout -->
          <button
            @click="authStore.logout()"
            title="Sair"
            style="background:none;border:none;cursor:pointer;padding:4px;color:#475569;border-radius:6px;display:flex;flex-shrink:0;transition:color 0.15s;"
            @mouseenter="(e) => (e.currentTarget as HTMLElement).style.color='#f87171'"
            @mouseleave="(e) => (e.currentTarget as HTMLElement).style.color='#475569'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor" style="width:15px;height:15px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
            </svg>
          </button>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <main style="flex:1;overflow:auto;display:flex;flex-direction:column;">
      <RouterView />
    </main>
  </div>

  <!-- Public routes: full width, no wrapper -->
  <RouterView v-else />
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>
