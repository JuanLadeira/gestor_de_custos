<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-lg font-semibold text-white">Assinaturas</h1>
        <p class="text-sm text-slate-400 mt-0.5">{{ assinaturas.length }} assinatura{{ assinaturas.length !== 1 ? 's' : '' }}</p>
      </div>
      <!-- Summary chips -->
      <div class="flex items-center gap-2">
        <span class="flex items-center gap-1.5 bg-emerald-500/10 text-emerald-400 text-xs font-medium px-3 py-1.5 rounded-full ring-1 ring-emerald-500/20">
          <span class="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
          {{ countByStatus('ATIVA') }} ativas
        </span>
        <span class="flex items-center gap-1.5 bg-amber-500/10 text-amber-400 text-xs font-medium px-3 py-1.5 rounded-full ring-1 ring-amber-500/20">
          <span class="w-1.5 h-1.5 bg-amber-400 rounded-full" />
          {{ countByStatus('SUSPENSA') }} suspensas
        </span>
        <span class="flex items-center gap-1.5 bg-red-500/10 text-red-400 text-xs font-medium px-3 py-1.5 rounded-full ring-1 ring-red-500/20">
          <span class="w-1.5 h-1.5 bg-red-400 rounded-full" />
          {{ countByStatus('CANCELADA') }} canceladas
        </span>
      </div>
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
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Tenant</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Plano</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Início</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Status</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Próx. cobrança</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Stripe ID</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Alterar</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr v-if="assinaturas.length === 0">
            <td colspan="8" class="px-5 py-12 text-center text-slate-500 text-sm">Nenhuma assinatura encontrada</td>
          </tr>
          <tr v-for="ass in assinaturas" :key="ass.id" class="hover:bg-white/[0.02] transition-colors">
            <td class="px-5 py-3.5 text-slate-500 font-mono text-xs">{{ ass.id }}</td>
            <td class="px-5 py-3.5 text-slate-300 text-sm">{{ ass.tenant_nome ?? ass.tenant_id }}</td>
            <td class="px-5 py-3.5 text-slate-400 text-sm">{{ ass.plano_nome ?? ass.plano_id }}</td>
            <td class="px-5 py-3.5 text-slate-400">
              {{ ass.data_inicio ? formatDate(ass.data_inicio) : '—' }}
            </td>
            <td class="px-5 py-3.5">
              <span :class="statusChip(ass.status)" class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ring-1">
                <span :class="statusDot(ass.status)" class="w-1.5 h-1.5 rounded-full" />
                {{ ass.status }}
              </span>
            </td>
            <td class="px-5 py-3.5 text-slate-400">
              {{ ass.data_proxima_cobranca ? formatDate(ass.data_proxima_cobranca) : '—' }}
            </td>
            <td class="px-5 py-3.5 text-slate-500 font-mono text-xs truncate max-w-36" :title="ass.stripe_subscription_id || ''">
              {{ ass.stripe_subscription_id ? ass.stripe_subscription_id.slice(0, 20) + '…' : '—' }}
            </td>
            <td class="px-5 py-3.5">
              <select
                :value="ass.status"
                @change="updateStatus(ass.id, ($event.target as HTMLSelectElement).value)"
                class="bg-slate-800 border border-white/10 text-slate-300 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-violet-500"
              >
                <option value="ATIVA">ATIVA</option>
                <option value="SUSPENSA">SUSPENSA</option>
                <option value="CANCELADA">CANCELADA</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import adminClient from '../../api/adminClient'

interface Assinatura {
  id: number
  status: string
  tenant_id: number
  tenant_nome: string
  plano_id: number
  plano_nome: string
  stripe_subscription_id: string | null
  data_inicio: string | null
  data_proxima_cobranca: string | null
}

const assinaturas = ref<Assinatura[]>([])
const loading = ref(true)
const error = ref('')

async function load() {
  try {
    const res = await adminClient.get('/assinaturas')
    assinaturas.value = res.data
  } catch {
    error.value = 'Erro ao carregar assinaturas.'
  } finally {
    loading.value = false
  }
}

async function updateStatus(id: number, status: string) {
  try {
    const res = await adminClient.put(`/assinaturas/${id}`, { status })
    const idx = assinaturas.value.findIndex((a) => a.id === id)
    if (idx !== -1) assinaturas.value[idx] = res.data
  } catch {
    alert('Erro ao atualizar status.')
  }
}

function countByStatus(status: string) {
  return assinaturas.value.filter((a) => a.status === status).length
}

function statusChip(status: string) {
  return {
    ATIVA: 'bg-emerald-500/10 text-emerald-400 ring-emerald-500/20',
    SUSPENSA: 'bg-amber-500/10 text-amber-400 ring-amber-500/20',
    CANCELADA: 'bg-red-500/10 text-red-400 ring-red-500/20',
  }[status] || 'bg-slate-700/50 text-slate-400 ring-white/5'
}

function statusDot(status: string) {
  return {
    ATIVA: 'bg-emerald-400',
    SUSPENSA: 'bg-amber-400',
    CANCELADA: 'bg-red-400',
  }[status] || 'bg-slate-500'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('pt-BR')
}

onMounted(load)
</script>
