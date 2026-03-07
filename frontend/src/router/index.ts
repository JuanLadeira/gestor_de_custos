import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useAdminAuthStore } from '../stores/adminAuth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: () => import('../views/LandingView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
    },
    {
      path: '/assinatura/sucesso',
      name: 'assinatura-sucesso',
      component: () => import('../views/AssinaturaSucessoView.vue'),
    },
    {
      path: '/custos',
      name: 'custos',
      component: () => import('../views/CustosView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/membros',
      name: 'membros',
      component: () => import('../views/UsuariosView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/campanhas',
      name: 'campanhas',
      component: () => import('../views/CampanhasView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/campanhas/:id',
      name: 'campanha-detalhe',
      component: () => import('../views/CampanhaDetalheView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/inbox',
      name: 'inbox',
      component: () => import('../views/InboxView.vue'),
      meta: { requiresAuth: true },
    },
    // Admin routes
    {
      path: '/admin/login',
      name: 'admin-login',
      component: () => import('../views/admin/AdminLoginView.vue'),
    },
    {
      path: '/admin',
      component: () => import('../views/admin/AdminLayoutView.vue'),
      meta: { requiresAdmin: true },
      children: [
        {
          path: '',
          redirect: '/admin/tenants',
        },
        {
          path: 'tenants',
          name: 'admin-tenants',
          component: () => import('../views/admin/AdminTenantsView.vue'),
        },
        {
          path: 'planos',
          name: 'admin-planos',
          component: () => import('../views/admin/AdminPlanosView.vue'),
        },
        {
          path: 'assinaturas',
          name: 'admin-assinaturas',
          component: () => import('../views/admin/AdminAssinaturasView.vue'),
        },
      ],
    },
  ],
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const adminStore = useAdminAuthStore()

  if (to.meta.requiresAdmin && !adminStore.isAuthenticated) {
    next('/admin/login')
  } else if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})

export default router
