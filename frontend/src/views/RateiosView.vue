<template>
  <div style="display:flex;flex-direction:column;height:100%;background:#f8fafc;">
    <!-- Header -->
    <div style="height:64px;background:#fff;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;justify-content:space-between;padding:0 24px;flex-shrink:0;">
      <div>
        <h1 style="font-size:15px;font-weight:600;color:#0f172a;margin:0;">Rateios</h1>
        <p style="font-size:12px;color:#94a3b8;margin:2px 0 0;">Distribuição de pagamentos por membro</p>
      </div>
      <!-- Month filter -->
      <div style="display:flex;align-items:center;gap:12px;">
        <select
          v-model="mesSelecionadoId"
          @change="carregarDados"
          style="border:1px solid #e2e8f0;border-radius:8px;padding:6px 32px 6px 12px;font-size:13px;color:#334155;background:#f8fafc;appearance:none;cursor:pointer;outline:none;min-width:160px;"
        >
          <option :value="null" disabled>Selecione o mês</option>
          <option v-for="mes in meses" :key="mes.id" :value="mes.id">
            {{ nomeMes(mes.mes) }}/{{ mes.ano }}
            <span v-if="mes.status === 'FECHADO'"> (fechado)</span>
          </option>
        </select>
      </div>
    </div>

    <!-- Content -->
    <div style="flex:1;overflow:auto;padding:24px;">
      <!-- Loading -->
      <div v-if="loading" style="display:flex;align-items:center;justify-content:center;height:200px;gap:10px;color:#94a3b8;">
        <svg style="width:18px;height:18px;animation:spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle style="opacity:.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path style="opacity:.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
        <span style="font-size:14px;">Carregando...</span>
      </div>

      <!-- No month selected -->
      <div v-else-if="!mesSelecionadoId" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:200px;text-align:center;">
        <div style="width:48px;height:48px;background:#f1f5f9;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:12px;">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="#94a3b8" style="width:24px;height:24px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 9v7.5" />
          </svg>
        </div>
        <p style="font-size:14px;font-weight:500;color:#475569;margin:0;">Selecione um mês de referência</p>
        <p style="font-size:12px;color:#94a3b8;margin:6px 0 0;">Use o seletor acima para filtrar os rateios.</p>
      </div>

      <!-- Empty -->
      <div v-else-if="!loading && rateios.length === 0" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:200px;text-align:center;">
        <div style="width:48px;height:48px;background:#f1f5f9;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:12px;">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="#94a3b8" style="width:24px;height:24px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21l3-9m0 0l3 9M10.5 12L21 3M3 18l4.5-4.5 3 3 4.5-4.5" />
          </svg>
        </div>
        <p style="font-size:14px;font-weight:500;color:#475569;margin:0;">Nenhum rateio encontrado</p>
        <p style="font-size:12px;color:#94a3b8;margin:6px 0 0;">Os rateios aparecerão aqui após criar custos com rateio.</p>
      </div>

      <!-- Main content -->
      <div v-else style="display:flex;flex-direction:column;gap:20px;">
        <!-- Summary -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;">
            <p style="font-size:11px;color:#94a3b8;margin:0;font-weight:500;text-transform:uppercase;letter-spacing:.05em;">Total rateado</p>
            <p style="font-size:20px;font-weight:700;color:#0f172a;margin:6px 0 0;font-variant-numeric:tabular-nums;">{{ formatCurrency(totalRateado) }}</p>
          </div>
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;">
            <p style="font-size:11px;color:#94a3b8;margin:0;font-weight:500;text-transform:uppercase;letter-spacing:.05em;">Pago</p>
            <p style="font-size:20px;font-weight:700;color:#059669;margin:6px 0 0;font-variant-numeric:tabular-nums;">{{ formatCurrency(totalPago) }}</p>
          </div>
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;">
            <p style="font-size:11px;color:#94a3b8;margin:0;font-weight:500;text-transform:uppercase;letter-spacing:.05em;">Pendente</p>
            <p style="font-size:20px;font-weight:700;color:#d97706;margin:6px 0 0;font-variant-numeric:tabular-nums;">{{ formatCurrency(totalPendente) }}</p>
          </div>
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:18px 20px;">
            <p style="font-size:11px;color:#94a3b8;margin:0;font-weight:500;text-transform:uppercase;letter-spacing:.05em;">% Pago</p>
            <p style="font-size:20px;font-weight:700;color:#0f172a;margin:6px 0 0;">{{ percentualPago }}%</p>
            <div style="margin-top:8px;height:4px;background:#f1f5f9;border-radius:999px;overflow:hidden;">
              <div :style="{ width: percentualPago + '%' }" style="height:100%;background:#059669;border-radius:999px;transition:width .3s;"></div>
            </div>
          </div>
        </div>

        <!-- Table -->
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;overflow:hidden;">
          <!-- Group by custo -->
          <div v-for="custo in custosComRateios" :key="custo.id">
            <!-- Custo subheader -->
            <div style="background:#f8fafc;border-bottom:1px solid #e2e8f0;padding:10px 20px;display:flex;align-items:center;gap:12px;">
              <span style="font-size:13px;font-weight:600;color:#334155;">{{ custo.descricao }}</span>
              <span style="font-size:11px;color:#94a3b8;font-variant-numeric:tabular-nums;">{{ formatCurrency(custo.valor) }}</span>
              <span
                style="margin-left:auto;font-size:11px;font-weight:500;padding:2px 8px;border-radius:999px;"
                :style="custo.status === 'PAGO' ? 'background:#d1fae5;color:#065f46;' : 'background:#fef3c7;color:#92400e;'"
              >{{ custo.status === 'PAGO' ? 'Pago' : 'Pendente' }}</span>
            </div>
            <!-- Rateios for this custo -->
            <table style="width:100%;border-collapse:collapse;">
              <tbody>
                <tr
                  v-for="rateio in rateiosPorCusto(custo.id)"
                  :key="rateio.id"
                  style="border-bottom:1px solid #f1f5f9;"
                  @mouseenter="(e) => (e.currentTarget as HTMLElement).style.background='#f8fafc'"
                  @mouseleave="(e) => (e.currentTarget as HTMLElement).style.background=''"
                >
                  <td style="padding:12px 20px;font-size:13px;color:#334155;width:200px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                      <div style="width:28px;height:28px;background:#e0e7ff;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                        <span style="font-size:11px;font-weight:700;color:#4338ca;">{{ usuarioInicial(rateio.usuario_id) }}</span>
                      </div>
                      <span style="font-weight:500;">{{ usuarioNome(rateio.usuario_id) }}</span>
                    </div>
                  </td>
                  <td style="padding:12px 20px;font-size:13px;color:#64748b;">
                    <div style="display:flex;align-items:center;gap:8px;">
                      <div style="width:64px;height:4px;background:#e2e8f0;border-radius:999px;overflow:hidden;">
                        <div :style="{ width: rateio.porcentagem + '%' }" style="height:100%;background:#6366f1;border-radius:999px;"></div>
                      </div>
                      <span style="font-size:12px;font-variant-numeric:tabular-nums;">{{ formatPct(rateio.porcentagem) }}</span>
                    </div>
                  </td>
                  <td style="padding:12px 20px;font-size:13px;font-weight:600;color:#0f172a;font-variant-numeric:tabular-nums;text-align:right;">
                    {{ formatCurrency(rateio.valor_calculado) }}
                  </td>
                  <td style="padding:12px 20px;white-space:nowrap;">
                    <span
                      style="display:inline-flex;align-items:center;gap:5px;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:500;"
                      :style="rateio.status === 'PAGO' ? 'background:#d1fae5;color:#065f46;' : 'background:#fef3c7;color:#92400e;'"
                    >
                      <span style="width:6px;height:6px;border-radius:50%;" :style="rateio.status === 'PAGO' ? 'background:#059669;' : 'background:#d97706;'"></span>
                      {{ rateio.status === 'PAGO' ? 'Pago' : 'Pendente' }}
                    </span>
                  </td>
                  <td style="padding:12px 20px;white-space:nowrap;text-align:right;">
                    <button
                      v-if="rateio.status === 'PENDENTE'"
                      @click="marcarPago(rateio)"
                      title="Marcar como pago"
                      style="background:none;border:none;cursor:pointer;padding:4px;color:#059669;display:inline-flex;align-items:center;border-radius:6px;"
                      @mouseenter="(e) => (e.currentTarget as HTMLElement).style.background='#d1fae5'"
                      @mouseleave="(e) => (e.currentTarget as HTMLElement).style.background='none'"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:16px;height:16px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </button>
                    <button
                      @click="confirmarDelete(rateio)"
                      title="Remover rateio"
                      style="background:none;border:none;cursor:pointer;padding:4px;color:#94a3b8;display:inline-flex;align-items:center;border-radius:6px;margin-left:4px;"
                      @mouseenter="(e) => (e.currentTarget as HTMLElement).style.background='#fee2e2';(e.currentTarget as HTMLElement).style.color='#dc2626'"
                      @mouseleave="(e) => (e.currentTarget as HTMLElement).style.background='none';(e.currentTarget as HTMLElement).style.color='#94a3b8'"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width:16px;height:16px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete confirm modal -->
    <div v-if="rateioParaDelete" style="position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;">
      <div style="position:absolute;inset:0;background:rgba(15,23,42,.5);backdrop-filter:blur(4px);" @click="rateioParaDelete=null"></div>
      <div style="position:relative;background:#fff;border-radius:16px;padding:28px;width:360px;box-shadow:0 25px 50px rgba(0,0,0,.15);">
        <h3 style="font-size:16px;font-weight:600;color:#0f172a;margin:0 0 8px;">Remover rateio?</h3>
        <p style="font-size:13px;color:#64748b;margin:0 0 20px;">
          Rateio de <strong>{{ usuarioNome(rateioParaDelete.usuario_id) }}</strong> — {{ formatCurrency(rateioParaDelete.valor_calculado) }}.
          Esta ação não pode ser desfeita.
        </p>
        <div style="display:flex;gap:10px;justify-content:flex-end;">
          <button @click="rateioParaDelete=null" style="padding:8px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;font-weight:500;color:#64748b;background:#fff;cursor:pointer;">Cancelar</button>
          <button @click="deletarRateio" style="padding:8px 16px;border:none;border-radius:8px;font-size:13px;font-weight:500;color:#fff;background:#dc2626;cursor:pointer;">Remover</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type PagamentoRateio, type Custo, type MesReferencia, type Usuario } from '../api/client'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const meses = ref<MesReferencia[]>([])
const custos = ref<Custo[]>([])
const rateios = ref<PagamentoRateio[]>([])
const usuarios = ref<Usuario[]>([])
const mesSelecionadoId = ref<number | null>(null)
const loading = ref(false)
const rateioParaDelete = ref<PagamentoRateio | null>(null)

// Maps for quick lookup
const usuariosMap = computed(() => {
  const m: Record<number, Usuario> = {}
  usuarios.value.forEach((u) => (m[u.id] = u))
  return m
})

const custosComRateios = computed(() =>
  custos.value.filter((c) => rateios.value.some((r) => r.custo_id === c.id))
)

function rateiosPorCusto(custoId: number) {
  return rateios.value.filter((r) => r.custo_id === custoId)
}

function usuarioNome(userId: number) {
  return usuariosMap.value[userId]?.nome ?? `#${userId}`
}

function usuarioInicial(userId: number) {
  const nome = usuariosMap.value[userId]?.nome
  return nome ? nome.charAt(0).toUpperCase() : '?'
}

onMounted(async () => {
  if (!authStore.tenantId) return
  const [mesesRes, usuariosRes] = await Promise.all([
    api.getMeses(authStore.tenantId),
    api.getUsuarios(authStore.tenantId),
  ])
  meses.value = mesesRes.data.sort((a, b) => {
    if (a.ano !== b.ano) return b.ano - a.ano
    return b.mes - a.mes
  })
  usuarios.value = usuariosRes.data
  if (meses.value.length > 0) {
    mesSelecionadoId.value = meses.value[0].id
    await carregarDados()
  }
})

async function carregarDados() {
  if (!mesSelecionadoId.value) return
  loading.value = true
  try {
    const custosRes = await api.getCustos(mesSelecionadoId.value)
    custos.value = custosRes.data
    const custoIds = custos.value.map((c) => c.id)
    if (custoIds.length === 0) {
      rateios.value = []
    } else {
      const responses = await Promise.all(custoIds.map((id) => api.getRateios({ custo_id: id })))
      rateios.value = responses.flatMap((r) => r.data)
    }
  } finally {
    loading.value = false
  }
}

async function marcarPago(rateio: PagamentoRateio) {
  await api.updateRateio(rateio.id, { status: 'PAGO' })
  rateio.status = 'PAGO'
}

function confirmarDelete(rateio: PagamentoRateio) {
  rateioParaDelete.value = rateio
}

async function deletarRateio() {
  if (!rateioParaDelete.value) return
  await api.deleteRateio(rateioParaDelete.value.id)
  rateios.value = rateios.value.filter((r) => r.id !== rateioParaDelete.value!.id)
  rateioParaDelete.value = null
}

// Computed totals
const totalRateado = computed(() =>
  rateios.value.reduce((s, r) => s + parseFloat(r.valor_calculado), 0)
)
const totalPago = computed(() =>
  rateios.value.filter((r) => r.status === 'PAGO').reduce((s, r) => s + parseFloat(r.valor_calculado), 0)
)
const totalPendente = computed(() =>
  rateios.value.filter((r) => r.status === 'PENDENTE').reduce((s, r) => s + parseFloat(r.valor_calculado), 0)
)
const percentualPago = computed(() => {
  if (!totalRateado.value) return 0
  return Math.round((totalPago.value / totalRateado.value) * 100)
})

function formatCurrency(value: string | number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(
    typeof value === 'string' ? parseFloat(value) : value,
  )
}

function formatPct(value: string | number) {
  return `${parseFloat(String(value)).toFixed(1)}%`
}

const MESES = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
function nomeMes(mes: number) {
  return MESES[mes - 1] ?? mes
}
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
