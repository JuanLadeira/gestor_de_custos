<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import apiClient from '../api/client'

interface Conversa {
  id: number
  numero: string
  nome: string | null
  status: 'AGUARDANDO' | 'EM_ATENDIMENTO' | 'ENCERRADA'
  instancia_id: number
  ultima_mensagem: string | null
  updated_at: string
}
interface Mensagem {
  id: number
  conteudo: string
  tipo: 'ENVIADA' | 'RECEBIDA'
  timestamp: string
}

const conversas = ref<Conversa[]>([])
const mensagens = ref<Mensagem[]>([])
const conversaSelecionada = ref<Conversa | null>(null)
const statusFiltro = ref<string>('')
const loading = ref(true)
const loadingMsgs = ref(false)
const novaMensagem = ref('')
const enviando = ref(false)

let refreshInterval: ReturnType<typeof setInterval> | null = null

async function carregarConversas() {
  try {
    const params: Record<string, string> = {}
    if (statusFiltro.value) params.status_filter = statusFiltro.value
    const r = await apiClient.get<Conversa[]>('/conversas', { params })
    conversas.value = r.data.sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
  } finally {
    loading.value = false
  }
}

async function selecionarConversa(c: Conversa) {
  conversaSelecionada.value = c
  loadingMsgs.value = true
  try {
    const r = await apiClient.get<Mensagem[]>(`/conversas/${c.id}/mensagens`)
    mensagens.value = r.data
  } finally {
    loadingMsgs.value = false
  }
  setTimeout(scrollToBottom, 100)
}

async function enviarMensagem() {
  if (!novaMensagem.value.trim() || !conversaSelecionada.value) return
  enviando.value = true
  try {
    const r = await apiClient.post<Mensagem>(`/conversas/${conversaSelecionada.value.id}/mensagens`, { conteudo: novaMensagem.value })
    mensagens.value.push(r.data)
    novaMensagem.value = ''
    // update ultima_mensagem in list
    const c = conversas.value.find(x => x.id === conversaSelecionada.value!.id)
    if (c) c.ultima_mensagem = r.data.conteudo
    setTimeout(scrollToBottom, 50)
  } finally {
    enviando.value = false
  }
}

async function encerrarConversa() {
  if (!conversaSelecionada.value) return
  const r = await apiClient.put<Conversa>(`/conversas/${conversaSelecionada.value.id}/status`, { status: 'ENCERRADA' })
  conversaSelecionada.value = r.data
  const idx = conversas.value.findIndex(c => c.id === r.data.id)
  if (idx !== -1) conversas.value[idx] = r.data
}

async function autoRefresh() {
  await carregarConversas()
  if (conversaSelecionada.value) {
    const r = await apiClient.get<Mensagem[]>(`/conversas/${conversaSelecionada.value.id}/mensagens`)
    const prev = mensagens.value.length
    mensagens.value = r.data
    if (r.data.length > prev) setTimeout(scrollToBottom, 50)
  }
}

function scrollToBottom() {
  const el = document.getElementById('msgs-container')
  if (el) el.scrollTop = el.scrollHeight
}

function fmtTime(ts: string) {
  const d = new Date(ts)
  return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}
function fmtDate(ts: string) {
  const d = new Date(ts)
  const hoje = new Date()
  if (d.toDateString() === hoje.toDateString()) return fmtTime(ts)
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}

const statusColor: Record<string, string> = {
  AGUARDANDO: '#f59e0b',
  EM_ATENDIMENTO: '#6366f1',
  ENCERRADA: '#94a3b8',
}
const statusLabel: Record<string, string> = {
  AGUARDANDO: 'Aguardando',
  EM_ATENDIMENTO: 'Em atendimento',
  ENCERRADA: 'Encerrada',
}

onMounted(async () => {
  await carregarConversas()
  refreshInterval = setInterval(autoRefresh, 30000)
})
onUnmounted(() => { if (refreshInterval) clearInterval(refreshInterval) })
</script>

<template>
  <div style="display:flex;height:100%;overflow:hidden;">

    <!-- Painel esquerdo: lista de conversas -->
    <div style="width:320px;flex-shrink:0;border-right:1px solid #e2e8f0;display:flex;flex-direction:column;background:white;">

      <!-- Header -->
      <div style="padding:16px;border-bottom:1px solid #e2e8f0;flex-shrink:0;">
        <h1 style="font-size:15px;font-weight:700;color:#0f172a;margin:0 0 10px;">Inbox</h1>
        <select
          v-model="statusFiltro"
          @change="loading=true; carregarConversas()"
          style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:7px 10px;font-size:12px;color:#334155;background:white;outline:none;cursor:pointer;"
        >
          <option value="">Todas</option>
          <option value="AGUARDANDO">Aguardando</option>
          <option value="EM_ATENDIMENTO">Em atendimento</option>
          <option value="ENCERRADA">Encerradas</option>
        </select>
      </div>

      <!-- Lista -->
      <div style="flex:1;overflow-y:auto;">
        <div v-if="loading" style="display:flex;justify-content:center;padding:32px;">
          <svg style="width:18px;height:18px;color:#4f46e5;animation:spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle style="opacity:.25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path style="opacity:.75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
        </div>
        <div v-else-if="conversas.length === 0" style="padding:32px 16px;text-align:center;color:#94a3b8;font-size:13px;">
          Nenhuma conversa encontrada.
        </div>
        <div
          v-for="c in conversas"
          :key="c.id"
          @click="selecionarConversa(c)"
          style="padding:12px 16px;border-bottom:1px solid #f1f5f9;cursor:pointer;transition:background .1s;"
          :style="conversaSelecionada?.id === c.id ? 'background:#ede9fe;' : ''"
          @mouseenter="e => { if(conversaSelecionada?.id !== c.id) (e.currentTarget as HTMLElement).style.background='#f8fafc' }"
          @mouseleave="e => { if(conversaSelecionada?.id !== c.id) (e.currentTarget as HTMLElement).style.background='' }"
        >
          <div style="display:flex;align-items:flex-start;gap:10px;">
            <!-- Avatar -->
            <div style="width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
              <span style="color:white;font-size:13px;font-weight:700;">{{ (c.nome ?? c.numero).charAt(0).toUpperCase() }}</span>
            </div>
            <!-- Info -->
            <div style="flex:1;min-width:0;">
              <div style="display:flex;justify-content:space-between;align-items:center;gap:4px;">
                <p style="font-size:13px;font-weight:600;color:#0f172a;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ c.nome ?? c.numero }}</p>
                <span style="font-size:10px;color:#94a3b8;flex-shrink:0;">{{ fmtDate(c.updated_at) }}</span>
              </div>
              <p style="font-size:12px;color:#64748b;margin:2px 0 4px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ c.ultima_mensagem ?? '—' }}</p>
              <span :style="`color:${statusColor[c.status]};background:${statusColor[c.status]}18;`" style="font-size:10px;font-weight:600;padding:1px 7px;border-radius:999px;">{{ statusLabel[c.status] }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Painel direito: conversa -->
    <div style="flex:1;display:flex;flex-direction:column;background:#f8fafc;overflow:hidden;">

      <!-- Vazio -->
      <div v-if="!conversaSelecionada" style="flex:1;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:10px;color:#94a3b8;">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width:40px;height:40px;opacity:.4;">
          <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z" />
        </svg>
        <p style="font-size:14px;font-weight:500;">Selecione uma conversa</p>
      </div>

      <template v-else>
        <!-- Conversa header -->
        <div style="background:white;border-bottom:1px solid #e2e8f0;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;">
          <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:36px;height:36px;background:linear-gradient(135deg,#6366f1,#8b5cf6);border-radius:50%;display:flex;align-items:center;justify-content:center;">
              <span style="color:white;font-size:13px;font-weight:700;">{{ (conversaSelecionada.nome ?? conversaSelecionada.numero).charAt(0).toUpperCase() }}</span>
            </div>
            <div>
              <p style="font-size:14px;font-weight:600;color:#0f172a;margin:0;">{{ conversaSelecionada.nome ?? conversaSelecionada.numero }}</p>
              <p style="font-size:12px;color:#64748b;margin:0;">{{ conversaSelecionada.numero }}</p>
            </div>
          </div>
          <button
            v-if="conversaSelecionada.status !== 'ENCERRADA'"
            @click="encerrarConversa"
            style="background:#f1f5f9;color:#475569;font-size:12px;font-weight:600;padding:7px 14px;border-radius:8px;border:none;cursor:pointer;"
          >
            Encerrar conversa
          </button>
          <span v-else style="font-size:12px;color:#94a3b8;font-weight:600;">Conversa encerrada</span>
        </div>

        <!-- Mensagens -->
        <div id="msgs-container" style="flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:8px;">
          <div v-if="loadingMsgs" style="display:flex;justify-content:center;padding:32px;">
            <svg style="width:18px;height:18px;color:#4f46e5;animation:spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle style="opacity:.25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path style="opacity:.75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          </div>
          <template v-else>
            <div v-if="mensagens.length === 0" style="text-align:center;color:#94a3b8;font-size:13px;padding:32px;">Nenhuma mensagem ainda.</div>
            <div
              v-for="m in mensagens"
              :key="m.id"
              style="display:flex;"
              :style="m.tipo === 'ENVIADA' ? 'justify-content:flex-end;' : 'justify-content:flex-start;'"
            >
              <div
                style="max-width:70%;padding:10px 14px;border-radius:14px;font-size:13px;line-height:1.45;"
                :style="m.tipo === 'ENVIADA'
                  ? 'background:#4f46e5;color:white;border-bottom-right-radius:4px;'
                  : 'background:white;color:#0f172a;border:1px solid #e2e8f0;border-bottom-left-radius:4px;'"
              >
                <p style="margin:0;white-space:pre-wrap;word-break:break-word;">{{ m.conteudo }}</p>
                <p :style="m.tipo === 'ENVIADA' ? 'color:rgba(255,255,255,.6);' : 'color:#94a3b8;'" style="font-size:10px;margin:4px 0 0;text-align:right;">{{ fmtTime(m.timestamp) }}</p>
              </div>
            </div>
          </template>
        </div>

        <!-- Input -->
        <div style="background:white;border-top:1px solid #e2e8f0;padding:12px 16px;flex-shrink:0;">
          <div style="display:flex;gap:8px;align-items:flex-end;">
            <textarea
              v-model="novaMensagem"
              @keydown.enter.exact.prevent="enviarMensagem"
              :disabled="conversaSelecionada.status === 'ENCERRADA'"
              placeholder="Digite uma mensagem... (Enter para enviar)"
              rows="2"
              style="flex:1;border:1.5px solid #e5e7eb;border-radius:10px;padding:10px 14px;font-size:13px;outline:none;resize:none;font-family:inherit;"
            ></textarea>
            <button
              @click="enviarMensagem"
              :disabled="enviando || !novaMensagem.trim() || conversaSelecionada.status === 'ENCERRADA'"
              style="background:#4f46e5;color:white;border:none;border-radius:10px;padding:10px 18px;font-size:13px;font-weight:600;cursor:pointer;flex-shrink:0;height:56px;"
            >
              {{ enviando ? '...' : 'Enviar' }}
            </button>
          </div>
        </div>
      </template>
    </div>
  </div>

</template>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }
</style>
