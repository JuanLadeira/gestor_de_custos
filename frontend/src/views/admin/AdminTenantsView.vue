<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-lg font-semibold text-white">Tenants</h1>
        <p class="text-sm text-slate-400 mt-0.5">{{ tenants.length }} grupo{{ tenants.length !== 1 ? 's' : '' }} cadastrado{{ tenants.length !== 1 ? 's' : '' }}</p>
      </div>
      <button
        @click="showCreate = true"
        class="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Novo Tenant
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <svg class="animate-spin w-6 h-6 text-violet-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-3 text-sm text-red-400">
      {{ error }}
    </div>

    <!-- Table -->
    <div v-else class="bg-slate-900 rounded-2xl border border-white/5 overflow-hidden">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-white/5">
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">ID</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Nome</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Descrição</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Criado em</th>
            <th class="px-5 py-3.5"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr v-if="tenants.length === 0">
            <td colspan="5" class="px-5 py-12 text-center text-slate-500 text-sm">Nenhum tenant cadastrado</td>
          </tr>
          <tr v-for="tenant in tenants" :key="tenant.id" class="hover:bg-white/[0.02] transition-colors">
            <td class="px-5 py-3.5 text-slate-500 font-mono text-xs">{{ tenant.id }}</td>
            <td class="px-5 py-3.5 font-medium text-white">{{ tenant.nome }}</td>
            <td class="px-5 py-3.5 text-slate-400">{{ tenant.descricao || '—' }}</td>
            <td class="px-5 py-3.5 text-slate-400">{{ formatDate(tenant.created_at) }}</td>
            <td class="px-5 py-3.5 text-right">
              <button
                @click="confirmDelete(tenant)"
                class="text-xs text-slate-500 hover:text-red-400 transition-colors"
              >
                Remover
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <Transition name="fade">
      <div v-if="showCreate" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div class="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-sm p-6 shadow-xl">
          <h3 class="text-base font-semibold text-white mb-5">Novo Tenant</h3>
          <form @submit.prevent="createTenant" class="space-y-4">
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1.5">Nome</label>
              <input
                v-model="newTenant.nome"
                required
                class="w-full bg-slate-800 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1.5">Descrição <span class="text-slate-600">(opcional)</span></label>
              <input
                v-model="newTenant.descricao"
                class="w-full bg-slate-800 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
              />
            </div>
            <p v-if="formError" class="text-xs text-red-400">{{ formError }}</p>
            <div class="flex gap-3 pt-1">
              <button
                type="button"
                @click="showCreate = false"
                class="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium py-2.5 rounded-xl text-sm transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="flex-1 bg-violet-600 hover:bg-violet-700 text-white font-medium py-2.5 rounded-xl text-sm transition-colors"
              >
                Criar
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import adminClient from '../../api/adminClient'

interface Tenant {
  id: number
  nome: string
  descricao: string | null
  created_at: string
}

const tenants = ref<Tenant[]>([])
const loading = ref(true)
const error = ref('')
const showCreate = ref(false)
const formError = ref('')
const newTenant = ref({ nome: '', descricao: '' })

async function load() {
  try {
    const res = await adminClient.get('/tenants')
    tenants.value = res.data
  } catch {
    error.value = 'Erro ao carregar tenants.'
  } finally {
    loading.value = false
  }
}

async function createTenant() {
  formError.value = ''
  try {
    const res = await adminClient.post('/tenants', newTenant.value)
    tenants.value.unshift(res.data)
    showCreate.value = false
    newTenant.value = { nome: '', descricao: '' }
  } catch (err: any) {
    formError.value = err.response?.data?.detail || 'Erro ao criar tenant.'
  }
}

async function confirmDelete(tenant: Tenant) {
  if (!confirm(`Remover tenant "${tenant.nome}"? Esta ação é irreversível.`)) return
  try {
    await adminClient.delete(`/tenants/${tenant.id}`)
    tenants.value = tenants.value.filter((t) => t.id !== tenant.id)
  } catch {
    alert('Erro ao remover tenant.')
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('pt-BR')
}

onMounted(load)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
