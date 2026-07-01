<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

interface Campanha {
  id: number
  nome: string
  status: 'RASCUNHO' | 'ATIVA' | 'PAUSADA' | 'CONCLUIDA'
  rate_limit_por_hora: number
  horario_inicio: number
  horario_fim: number
  instancias_ids: number[] | null
  total_contatos: number
  pendentes: number
  enviados: number
  falhos: number
  created_at: string
}

const campanhas = ref<Campanha[]>([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)

const form = ref({
  nome: '',
  rate_limit_por_hora: 30,
  horario_inicio: 8,
  horario_fim: 20,
})

async function carregar() {
  loading.value = true
  try {
    const r = await apiClient.get<Campanha[]>('/campanhas')
    campanhas.value = r.data
  } finally {
    loading.value = false
  }
}

async function criar() {
  saving.value = true
  try {
    const r = await apiClient.post<Campanha>('/campanhas', form.value)
    campanhas.value.unshift(r.data)
    showModal.value = false
    form.value = { nome: '', rate_limit_por_hora: 30, horario_inicio: 8, horario_fim: 20 }
    router.push(`/campanhas/${r.data.id}`)
  } finally {
    saving.value = false
  }
}

function abrirModal() {
  form.value = { nome: '', rate_limit_por_hora: 30, horario_inicio: 8, horario_fim: 20 }
  showModal.value = true
}

const totalAtivas = computed(() => campanhas.value.filter(c => c.status === 'ATIVA').length)
const totalEnviados = computed(() => campanhas.value.reduce((s, c) => s + c.enviados, 0))

const statusInfo: Record<string, { label: string; bg: string; color: string; dot: string }> = {
  RASCUNHO: { label: 'Rascunho', bg: '#f1f5f9', color: '#475569', dot: '#94a3b8' },
  ATIVA:    { label: 'Ativa',    bg: '#d1fae5', color: '#065f46', dot: '#059669' },
  PAUSADA:  { label: 'Pausada',  bg: '#fef3c7', color: '#92400e', dot: '#d97706' },
  CONCLUIDA:{ label: 'Concluída',bg: '#e0e7ff', color: '#3730a3', dot: '#6366f1' },
}

function fmtHora(h: number) { return `${h.toString().padStart(2, '0')}:00` }

onMounted(carregar)
</script>

<template>
  <div style="display:flex;flex-direction:column;height:100%;position:relative;">

    <!-- Header -->
    <div style="height:64px;border-bottom:1px solid #e2e8f0;background:white;display:flex;align-items:center;justify-content:space-between;padding:0 24px;flex-shrink:0;">
      <div>
        <h1 style="font-size:15px;font-weight:600;color:#0f172a;margin:0;">Campanhas</h1>
        <p style="font-size:12px;color:#64748b;margin:0;">Disparos em massa via WhatsApp</p>
      </div>
      <button
        v-if="authStore.can('campanha:create')"
        @click="abrirModal"
        style="display:flex;align-items:center;gap:6px;background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:8px 14px;border-radius:9px;border:none;cursor:pointer;"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" style="width:14px;height:14px;">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Nova Campanha
      </button>
    </div>

    <!-- Content -->
    <div style="flex:1;overflow:auto;padding:24px;">

      <!-- Loading -->
      <div v-if="loading" style="display:flex;align-items:center;justify-content:center;height:200px;">
        <svg style="width:22px;height:22px;color:#4f46e5;animation:spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle style="opacity:.25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path style="opacity:.75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      </div>

      <template v-else>
        <!-- Summary cards -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Total</p>
            <p style="font-size:22px;font-weight:700;color:#0f172a;margin:0;">{{ campanhas.length }}</p>
          </div>
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Ativas</p>
            <p style="font-size:22px;font-weight:700;color:#059669;margin:0;">{{ totalAtivas }}</p>
          </div>
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Enviados (total)</p>
            <p style="font-size:22px;font-weight:700;color:#4f46e5;margin:0;">{{ totalEnviados }}</p>
          </div>
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Instâncias</p>
            <p style="font-size:22px;font-weight:700;color:#0f172a;margin:0;">
              {{ new Set(campanhas.flatMap(c => c.instancias_ids ?? [])).size }}
            </p>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="campanhas.length === 0" style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:56px 32px;text-align:center;">
          <div style="width:48px;height:48px;background:#f1f5f9;border-radius:12px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="#94a3b8" style="width:24px;height:24px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M10.34 15.84c-.688-.06-1.386-.09-2.09-.09H7.5a4.5 4.5 0 110-9h.75c.704 0 1.402-.03 2.09-.09m0 9.18c.253.962.584 1.892.985 2.783.247.55.06 1.21-.463 1.511l-.657.38c-.551.318-1.26.117-1.527-.461a20.845 20.845 0 01-1.44-4.282m3.102.069a18.03 18.03 0 01-.59-4.59c0-1.586.205-3.124.59-4.59m0 9.18a23.848 23.848 0 018.835 2.535M10.34 6.66a23.847 23.847 0 008.835-2.535m0 0A23.74 23.74 0 0018.795 3m.38 1.125a23.91 23.91 0 011.014 5.395m-1.014 8.855c-.118.38-.245.754-.38 1.125m.38-1.125a23.91 23.91 0 001.014-5.395m0-3.46c.495.413.811 1.035.811 1.73 0 .695-.316 1.317-.811 1.73m0-3.46a24.347 24.347 0 010 3.46" />
            </svg>
          </div>
          <p style="font-size:14px;font-weight:600;color:#334155;margin:0 0 4px;">Nenhuma campanha criada</p>
          <p style="font-size:13px;color:#94a3b8;margin:0;">Crie sua primeira campanha de disparo WhatsApp.</p>
        </div>

        <!-- Table -->
        <div v-else style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;">
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
              <tr style="border-bottom:1px solid #f1f5f9;">
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Nome</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Status</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Progresso</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Rate limit</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Horário</th>
                <th style="padding:11px 20px;width:60px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in campanhas"
                :key="c.id"
                style="border-bottom:1px solid #f8fafc;cursor:pointer;transition:background .1s;"
                @click="router.push(`/campanhas/${c.id}`)"
                @mouseenter="e => (e.currentTarget as HTMLElement).style.background='#f8fafc'"
                @mouseleave="e => (e.currentTarget as HTMLElement).style.background=''"
              >
                <td style="padding:13px 20px;font-weight:600;color:#0f172a;">{{ c.nome }}</td>
                <td style="padding:13px 20px;">
                  <span
                    :style="`background:${statusInfo[c.status].bg};color:${statusInfo[c.status].color};`"
                    style="display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:600;"
                  >
                    <span :style="`width:5px;height:5px;border-radius:50%;display:inline-block;background:${statusInfo[c.status].dot};`"></span>
                    {{ statusInfo[c.status].label }}
                  </span>
                </td>
                <td style="padding:13px 20px;">
                  <div style="display:flex;align-items:center;gap:8px;">
                    <div style="width:80px;height:5px;background:#f1f5f9;border-radius:999px;overflow:hidden;">
                      <div
                        :style="`width:${c.total_contatos ? Math.round(c.enviados/c.total_contatos*100) : 0}%;background:#4f46e5;`"
                        style="height:100%;border-radius:999px;transition:width .3s;"
                      ></div>
                    </div>
                    <span style="font-size:12px;color:#64748b;">{{ c.enviados }}/{{ c.total_contatos }}</span>
                  </div>
                </td>
                <td style="padding:13px 20px;color:#475569;">{{ c.rate_limit_por_hora }}/h</td>
                <td style="padding:13px 20px;color:#475569;">{{ fmtHora(c.horario_inicio) }}–{{ fmtHora(c.horario_fim) }}</td>
                <td style="padding:13px 20px;">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="#94a3b8" style="width:15px;height:15px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                  </svg>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>

    <!-- Modal nova campanha -->
    <div v-if="showModal" style="position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:50;padding:16px;" @click.self="showModal=false">
      <div style="background:white;border-radius:16px;width:100%;max-width:400px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.15);">
        <div style="padding:20px 24px;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:15px;font-weight:700;color:#0f172a;margin:0;">Nova Campanha</h3>
          <button @click="showModal=false" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:4px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px;"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <form @submit.prevent="criar" style="padding:20px 24px;display:flex;flex-direction:column;gap:14px;">
          <div>
            <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Nome</label>
            <input v-model="form.nome" required placeholder="Ex: Promoção Setembro" style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;">
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Rate limit/h</label>
              <input v-model.number="form.rate_limit_por_hora" type="number" min="1" max="200" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
            </div>
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Início</label>
              <input v-model.number="form.horario_inicio" type="number" min="0" max="23" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
            </div>
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Fim</label>
              <input v-model.number="form.horario_fim" type="number" min="0" max="23" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
            </div>
          </div>
          <button
            type="submit"
            :disabled="saving"
            style="background:#4f46e5;color:white;font-size:14px;font-weight:600;padding:11px;border-radius:10px;border:none;cursor:pointer;margin-top:4px;"
          >
            {{ saving ? 'Criando...' : 'Criar Campanha' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }
</style>
