<template>
  <div style="display:flex;flex-direction:column;height:100%;">

    <!-- Header -->
    <div style="height:64px;border-bottom:1px solid #e2e8f0;background:white;display:flex;align-items:center;justify-content:space-between;padding:0 24px;flex-shrink:0;">
      <div>
        <h1 style="font-size:15px;font-weight:600;color:#0f172a;margin:0;">Custos</h1>
        <p style="font-size:12px;color:#64748b;margin:0;">Despesas do grupo</p>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <!-- Filtro de mês -->
        <select
          v-model="mesSelecionadoId"
          @change="carregarCustos"
          style="border:1px solid #e2e8f0;border-radius:8px;padding:7px 12px;font-size:13px;color:#334155;background:white;cursor:pointer;outline:none;"
        >
          <option v-for="m in meses" :key="m.id" :value="m.id">
            {{ nomeMes(m.mes) }}/{{ m.ano }}
            <template v-if="m.status === 'ABERTO'"> · Aberto</template>
          </option>
        </select>
        <button
          @click="abrirCreate"
          style="display:flex;align-items:center;gap:6px;background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:8px 14px;border-radius:9px;border:none;cursor:pointer;"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" style="width:14px;height:14px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Novo custo
        </button>
      </div>
    </div>

    <!-- Content -->
    <div style="flex:1;overflow:auto;padding:24px;">

      <!-- Loading -->
      <div v-if="loading" style="display:flex;align-items:center;justify-content:center;height:200px;">
        <svg class="animate-spin" style="width:22px;height:22px;color:#4f46e5;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle style="opacity:.25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path style="opacity:.75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      </div>

      <template v-else>
        <!-- Summary bar -->
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;">
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Total</p>
            <p style="font-size:20px;font-weight:700;color:#0f172a;margin:0;font-variant-numeric:tabular-nums;">{{ fmt(totalGeral) }}</p>
          </div>
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Pagos</p>
            <p style="font-size:20px;font-weight:700;color:#059669;margin:0;font-variant-numeric:tabular-nums;">{{ fmt(totalPago) }}</p>
          </div>
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Pendentes</p>
            <p style="font-size:20px;font-weight:700;color:#d97706;margin:0;font-variant-numeric:tabular-nums;">{{ fmt(totalPendente) }}</p>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="custos.length === 0" style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:56px 32px;text-align:center;">
          <div style="width:48px;height:48px;background:#f1f5f9;border-radius:12px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="#94a3b8" style="width:24px;height:24px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75" />
            </svg>
          </div>
          <p style="font-size:14px;font-weight:600;color:#334155;margin:0 0 4px;">Nenhum custo neste mês</p>
          <p style="font-size:13px;color:#94a3b8;margin:0;">Crie o primeiro custo ou importe os custos fixos.</p>
        </div>

        <!-- Table -->
        <div v-else style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;">
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
              <tr style="border-bottom:1px solid #f1f5f9;">
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Descrição</th>
                <th style="text-align:right;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Valor</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Vencimento</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Tipo</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Status</th>
                <th style="padding:11px 20px;width:96px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in custos"
                :key="c.id"
                style="border-bottom:1px solid #f8fafc;transition:background .1s;"
                @mouseenter="e => (e.currentTarget as HTMLElement).style.background='#f8fafc'"
                @mouseleave="e => (e.currentTarget as HTMLElement).style.background=''"
              >
                <td style="padding:13px 20px;font-weight:500;color:#0f172a;">{{ c.descricao }}</td>
                <td style="padding:13px 20px;text-align:right;font-weight:600;color:#0f172a;font-variant-numeric:tabular-nums;font-family:monospace;">{{ fmt(c.valor) }}</td>
                <td style="padding:13px 20px;color:#475569;">{{ fmtData(c.data_vencimento) }}</td>
                <td style="padding:13px 20px;">
                  <span :style="c.tipo === 'FIXO'
                    ? 'background:#f1f5f9;color:#475569;'
                    : 'background:#ede9fe;color:#6d28d9;'"
                    style="padding:3px 9px;border-radius:6px;font-size:11px;font-weight:600;">
                    {{ c.tipo === 'FIXO' ? 'Fixo' : 'Variável' }}
                  </span>
                </td>
                <td style="padding:13px 20px;">
                  <span :style="c.status === 'PAGO'
                    ? 'background:#d1fae5;color:#065f46;'
                    : 'background:#fef3c7;color:#92400e;'"
                    style="display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:600;">
                    <span :style="c.status === 'PAGO' ? 'background:#10b981' : 'background:#f59e0b'"
                      style="width:5px;height:5px;border-radius:50%;display:inline-block;"></span>
                    {{ c.status === 'PAGO' ? 'Pago' : 'Pendente' }}
                  </span>
                </td>
                <td style="padding:13px 20px;">
                  <div style="display:flex;align-items:center;justify-content:flex-end;gap:4px;">
                    <!-- Marcar pago/pendente -->
                    <button
                      v-if="c.status === 'PENDENTE'"
                      @click="marcarPago(c)"
                      title="Marcar como pago"
                      style="background:none;border:none;cursor:pointer;padding:5px;border-radius:6px;color:#94a3b8;display:flex;"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                    <!-- Editar -->
                    <button
                      @click="abrirEdit(c)"
                      title="Editar"
                      style="background:none;border:none;cursor:pointer;padding:5px;border-radius:6px;color:#94a3b8;display:flex;"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                      </svg>
                    </button>
                    <!-- Deletar -->
                    <button
                      @click="deletar(c)"
                      title="Remover"
                      style="background:none;border:none;cursor:pointer;padding:5px;border-radius:6px;color:#94a3b8;display:flex;"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>

    <!-- Modal Create/Edit -->
    <div v-if="showModal" style="position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:50;padding:16px;" @click.self="showModal=false">
      <div style="background:white;border-radius:16px;width:100%;max-width:420px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.15);">
        <div style="padding:20px 24px;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:15px;font-weight:700;color:#0f172a;margin:0;">{{ editando ? 'Editar custo' : 'Novo custo' }}</h3>
          <button @click="showModal=false" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:4px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px;"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <form @submit.prevent="salvar" style="padding:20px 24px;display:flex;flex-direction:column;gap:14px;">
          <div>
            <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Descrição</label>
            <input v-model="form.descricao" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Valor (R$)</label>
              <input v-model="form.valor" type="number" step="0.01" min="0" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
            </div>
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Vencimento</label>
              <input v-model="form.data_vencimento" type="date" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Tipo</label>
              <select v-model="form.tipo" style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;background:white;outline:none;box-sizing:border-box;">
                <option value="VARIAVEL">Variável</option>
                <option value="FIXO">Fixo</option>
              </select>
            </div>
            <div v-if="editando">
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Status</label>
              <select v-model="form.status" style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;background:white;outline:none;box-sizing:border-box;">
                <option value="PENDENTE">Pendente</option>
                <option value="PAGO">Pago</option>
              </select>
            </div>
          </div>
          <p v-if="formError" style="font-size:12px;color:#dc2626;margin:0;">{{ formError }}</p>
          <div style="display:flex;gap:10px;padding-top:4px;">
            <button type="button" @click="showModal=false" style="flex:1;background:#f1f5f9;color:#334155;font-size:14px;font-weight:600;padding:11px;border-radius:10px;border:none;cursor:pointer;">Cancelar</button>
            <button type="submit" :disabled="salvando" style="flex:1;background:#4f46e5;color:white;font-size:14px;font-weight:600;padding:11px;border-radius:10px;border:none;cursor:pointer;">
              {{ salvando ? 'Salvando...' : 'Salvar' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type Custo, type MesReferencia } from '../api/client'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const meses = ref<MesReferencia[]>([])
const mesSelecionadoId = ref<number | null>(null)
const custos = ref<Custo[]>([])
const loading = ref(true)
const showModal = ref(false)
const editando = ref<Custo | null>(null)
const salvando = ref(false)
const formError = ref('')

const form = ref({
  descricao: '',
  valor: '',
  data_vencimento: '',
  tipo: 'VARIAVEL' as 'FIXO' | 'VARIAVEL',
  status: 'PENDENTE' as 'PENDENTE' | 'PAGO',
})

const totalGeral = computed(() => custos.value.reduce((s, c) => s + parseFloat(c.valor), 0))
const totalPago = computed(() => custos.value.filter(c => c.status === 'PAGO').reduce((s, c) => s + parseFloat(c.valor), 0))
const totalPendente = computed(() => custos.value.filter(c => c.status === 'PENDENTE').reduce((s, c) => s + parseFloat(c.valor), 0))

function fmt(v: string | number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(typeof v === 'string' ? parseFloat(v) : v)
}
function fmtData(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString('pt-BR')
}
const MESES_NOME = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
function nomeMes(m: number) { return MESES_NOME[m - 1] }

async function carregarCustos() {
  loading.value = true
  try {
    const r = await api.getCustos(mesSelecionadoId.value ?? undefined)
    custos.value = r.data
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (!authStore.tenantId) return
  const r = await api.getMeses(authStore.tenantId)
  // Ordena do mais recente ao mais antigo
  meses.value = r.data.sort((a, b) => b.ano !== a.ano ? b.ano - a.ano : b.mes - a.mes)
  if (meses.value.length) {
    mesSelecionadoId.value = meses.value[0].id
  }
  await carregarCustos()
})

function abrirCreate() {
  editando.value = null
  form.value = { descricao: '', valor: '', data_vencimento: '', tipo: 'VARIAVEL', status: 'PENDENTE' }
  formError.value = ''
  showModal.value = true
}

function abrirEdit(c: Custo) {
  editando.value = c
  form.value = { descricao: c.descricao, valor: c.valor, data_vencimento: c.data_vencimento, tipo: c.tipo, status: c.status }
  formError.value = ''
  showModal.value = true
}

async function salvar() {
  salvando.value = true
  formError.value = ''
  try {
    if (editando.value) {
      const r = await api.updateCusto(editando.value.id, form.value)
      const idx = custos.value.findIndex(c => c.id === editando.value!.id)
      if (idx !== -1) custos.value[idx] = r.data
    } else {
      if (!mesSelecionadoId.value) return
      const r = await api.createCusto({ ...form.value, mes_referencia_id: mesSelecionadoId.value })
      custos.value.unshift(r.data)
    }
    showModal.value = false
  } catch (e: any) {
    formError.value = e.response?.data?.detail || 'Erro ao salvar'
  } finally {
    salvando.value = false
  }
}

async function marcarPago(c: Custo) {
  const r = await api.updateCusto(c.id, { status: 'PAGO' })
  const idx = custos.value.findIndex(x => x.id === c.id)
  if (idx !== -1) custos.value[idx] = r.data
}

async function deletar(c: Custo) {
  if (!confirm(`Remover "${c.descricao}"?`)) return
  await api.deleteCusto(c.id)
  custos.value = custos.value.filter(x => x.id !== c.id)
}
</script>
