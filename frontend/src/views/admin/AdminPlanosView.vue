<template>
  <div class="p-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-lg font-semibold text-white">Planos</h1>
        <p class="text-sm text-slate-400 mt-0.5">{{ planos.length }} plano{{ planos.length !== 1 ? 's' : '' }} cadastrado{{ planos.length !== 1 ? 's' : '' }}</p>
      </div>
      <button
        @click="openCreate"
        class="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Novo Plano
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
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Nome</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Mensal</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Anual</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Usuários</th>
            <th class="px-5 py-3.5 text-left text-xs font-medium text-slate-500 uppercase tracking-wide">Status</th>
            <th class="px-5 py-3.5"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/5">
          <tr v-if="planos.length === 0">
            <td colspan="6" class="px-5 py-12 text-center text-slate-500 text-sm">Nenhum plano cadastrado</td>
          </tr>
          <tr v-for="plano in planos" :key="plano.id" class="hover:bg-white/[0.02] transition-colors">
            <td class="px-5 py-3.5 font-medium text-white">{{ plano.nome }}</td>
            <td class="px-5 py-3.5 text-slate-300">R$ {{ formatPreco(plano.preco_mensal) }}</td>
            <td class="px-5 py-3.5 text-slate-300">R$ {{ formatPreco(plano.preco_anual) }}</td>
            <td class="px-5 py-3.5 text-slate-400">{{ plano.max_usuarios }}</td>
            <td class="px-5 py-3.5">
              <span
                :class="plano.ativo
                  ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20'
                  : 'bg-slate-700/50 text-slate-400 ring-1 ring-white/5'"
                class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
              >
                <span
                  :class="plano.ativo ? 'bg-emerald-400' : 'bg-slate-500'"
                  class="w-1.5 h-1.5 rounded-full mr-1.5"
                />
                {{ plano.ativo ? 'Ativo' : 'Inativo' }}
              </span>
            </td>
            <td class="px-5 py-3.5 text-right space-x-3">
              <button @click="openEdit(plano)" class="text-xs text-slate-500 hover:text-violet-400 transition-colors">Editar</button>
              <button @click="confirmDelete(plano)" class="text-xs text-slate-500 hover:text-red-400 transition-colors">Remover</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create/Edit Modal -->
    <Transition name="fade">
      <div v-if="showModal" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
        <div class="bg-slate-900 rounded-2xl border border-white/10 w-full max-w-md p-6 shadow-xl">
          <h3 class="text-base font-semibold text-white mb-5">{{ editingId ? 'Editar' : 'Novo' }} Plano</h3>
          <form @submit.prevent="savePlano" class="space-y-4">
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1.5">Nome</label>
              <input
                v-model="form.nome"
                required
                class="w-full bg-slate-800 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
              />
            </div>
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-medium text-slate-400 mb-1.5">Preço mensal (R$)</label>
                <input
                  v-model.number="form.preco_mensal"
                  type="number"
                  step="0.01"
                  required
                  class="w-full bg-slate-800 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-400 mb-1.5">Preço anual (R$)</label>
                <input
                  v-model.number="form.preco_anual"
                  type="number"
                  step="0.01"
                  required
                  class="w-full bg-slate-800 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                />
              </div>
              <div>
                <label class="block text-xs font-medium text-slate-400 mb-1.5">Máx. usuários</label>
                <input
                  v-model.number="form.max_usuarios"
                  type="number"
                  required
                  class="w-full bg-slate-800 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
                />
              </div>
              <div class="flex items-end pb-0.5">
                <label class="flex items-center gap-2.5 cursor-pointer">
                  <div
                    @click="form.ativo = !form.ativo"
                    :class="form.ativo ? 'bg-violet-600' : 'bg-slate-700'"
                    class="relative w-9 h-5 rounded-full transition-colors"
                  >
                    <span
                      :class="form.ativo ? 'translate-x-4' : 'translate-x-0.5'"
                      class="absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform shadow-sm"
                    />
                  </div>
                  <span class="text-sm text-slate-300">Ativo</span>
                </label>
              </div>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1.5">Stripe Price ID Mensal</label>
              <input
                v-model="form.stripe_price_id_mensal"
                placeholder="price_..."
                class="w-full bg-slate-800 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white font-mono placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
              />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-400 mb-1.5">Stripe Price ID Anual</label>
              <input
                v-model="form.stripe_price_id_anual"
                placeholder="price_..."
                class="w-full bg-slate-800 border border-white/10 rounded-xl px-3.5 py-2.5 text-sm text-white font-mono placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent"
              />
            </div>
            <p v-if="formError" class="text-xs text-red-400">{{ formError }}</p>
            <div class="flex gap-3 pt-1">
              <button
                type="button"
                @click="showModal = false"
                class="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium py-2.5 rounded-xl text-sm transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                class="flex-1 bg-violet-600 hover:bg-violet-700 text-white font-medium py-2.5 rounded-xl text-sm transition-colors"
              >
                Salvar
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

interface Plano {
  id: number
  nome: string
  preco_mensal: number
  preco_anual: number
  max_usuarios: number
  ativo: boolean
  stripe_price_id_mensal: string | null
  stripe_price_id_anual: string | null
}

const planos = ref<Plano[]>([])
const loading = ref(true)
const error = ref('')
const showModal = ref(false)
const formError = ref('')
const editingId = ref<number | null>(null)

const defaultForm = () => ({
  nome: '',
  preco_mensal: 0,
  preco_anual: 0,
  max_usuarios: 5,
  ativo: true,
  stripe_price_id_mensal: '',
  stripe_price_id_anual: '',
})

const form = ref(defaultForm())

async function load() {
  try {
    const res = await adminClient.get('/planos')
    planos.value = res.data
  } catch {
    error.value = 'Erro ao carregar planos.'
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  form.value = defaultForm()
  formError.value = ''
  showModal.value = true
}

function openEdit(plano: Plano) {
  editingId.value = plano.id
  form.value = {
    nome: plano.nome,
    preco_mensal: plano.preco_mensal,
    preco_anual: plano.preco_anual,
    max_usuarios: plano.max_usuarios,
    ativo: plano.ativo,
    stripe_price_id_mensal: plano.stripe_price_id_mensal || '',
    stripe_price_id_anual: plano.stripe_price_id_anual || '',
  }
  formError.value = ''
  showModal.value = true
}

async function savePlano() {
  formError.value = ''
  try {
    if (editingId.value) {
      const res = await adminClient.put(`/planos/${editingId.value}`, form.value)
      const idx = planos.value.findIndex((p) => p.id === editingId.value)
      if (idx !== -1) planos.value[idx] = res.data
    } else {
      const res = await adminClient.post('/planos', form.value)
      planos.value.push(res.data)
    }
    showModal.value = false
  } catch (err: any) {
    formError.value = err.response?.data?.detail || 'Erro ao salvar plano.'
  }
}

async function confirmDelete(plano: Plano) {
  if (!confirm(`Remover plano "${plano.nome}"?`)) return
  try {
    await adminClient.delete(`/planos/${plano.id}`)
    planos.value = planos.value.filter((p) => p.id !== plano.id)
  } catch {
    alert('Erro ao remover plano.')
  }
}

function formatPreco(valor: number) {
  return Number(valor).toFixed(2).replace('.', ',')
}

onMounted(load)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
