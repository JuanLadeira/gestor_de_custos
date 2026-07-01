<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '../api/client'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const campanhaId = Number(route.params.id)

// ── Types ──────────────────────────────────────────────────────────────────────
interface Campanha {
  id: number; nome: string
  status: 'RASCUNHO' | 'ATIVA' | 'PAUSADA' | 'CONCLUIDA'
  rate_limit_por_hora: number; horario_inicio: number; horario_fim: number
  instancias_ids: number[] | null; data_source: Record<string, any> | null
  total_contatos: number; pendentes: number; enviados: number; falhos: number
}
interface Template { id: number; campanha_id: number; conteudo: string }
interface Contato { id: number; numero: string; nome: string | null; status: string; instancia_id: number | null; enviado_em: string | null; variaveis: Record<string, any> | null; erro: string | null }
interface Instancia { id: number; instance_name: string; status: string }

// ── Endpoints internos disponíveis ─────────────────────────────────────────────
const INTERNAL_ENDPOINTS = [
  {
    label: 'Usuários do tenant',
    description: 'Lista todos os membros do seu grupo com nome, email e username',
    path: '/api/usuarios/',
    method: 'GET',
    chave_contato: 'username',
    mode: 'bulk',
    mapeamento: [{ key: 'nome', path: '$.nome' }, { key: 'email', path: '$.email' }],
  },
  {
    label: 'Rateios pendentes',
    description: 'Rateios de pagamento com status PENDENTE do tenant',
    path: '/api/rateios/?status=PENDENTE',
    method: 'GET',
    chave_contato: 'usuario_id',
    mode: 'bulk',
    mapeamento: [{ key: 'valor', path: '$.valor_calculado' }, { key: 'status', path: '$.status' }],
  },
  {
    label: 'Custos do tenant',
    description: 'Lista de custos registrados no sistema',
    path: '/api/custos/',
    method: 'GET',
    chave_contato: 'mes_referencia_id',
    mode: 'bulk',
    mapeamento: [{ key: 'descricao', path: '$.descricao' }, { key: 'valor', path: '$.valor' }],
  },
]

// ── State ──────────────────────────────────────────────────────────────────────
const campanha = ref<Campanha | null>(null)
const templates = ref<Template[]>([])
const contatos = ref<Contato[]>([])
const instancias = ref<Instancia[]>([])
const loading = ref(true)
const saving = ref(false)
const actionLoading = ref(false)

const configForm = ref({ nome: '', rate_limit_por_hora: 30, horario_inicio: 8, horario_fim: 20, instancias_ids: [] as number[] })
const novoTemplate = ref('')
const novoNumero = ref('')
const novoNome = ref('')
const bulkTexto = ref('')
const resolvingVars = ref(false)

// Logs
const logsStatusFiltro = ref('')
const contatosFiltrados = computed(() =>
  logsStatusFiltro.value ? contatos.value.filter(c => c.status === logsStatusFiltro.value) : contatos.value
)
let logsInterval: ReturnType<typeof setInterval> | null = null

// tooltip do template
const showTemplateTooltip = ref(false)

// Data source
const dsSourceType = ref<'externa' | 'interna'>('externa')
const selectedEndpoint = ref('')
const dsForm = ref({
  url: '',
  method: 'GET',
  chave_contato: 'telefone',
  mode: 'bulk',
  body_template: '',
  mapeamento: [] as { key: string; path: string }[],
  headers: [] as { key: string; value: string }[],
  use_system_token: false,
})

// ── Load ───────────────────────────────────────────────────────────────────────
async function carregar() {
  loading.value = true
  try {
    const [rc, rt, rcontatos, rinst] = await Promise.all([
      apiClient.get<Campanha>(`/campanhas/${campanhaId}`),
      apiClient.get<Template[]>(`/campanhas/${campanhaId}/templates`).catch(() => ({ data: [] as Template[] })),
      apiClient.get<Contato[]>(`/campanhas/${campanhaId}/contatos`),
      apiClient.get<Instancia[]>('/whatsapp/instancias'),
    ])
    campanha.value = rc.data
    templates.value = rt.data
    contatos.value = rcontatos.data
    instancias.value = rinst.data

    configForm.value = {
      nome: rc.data.nome,
      rate_limit_por_hora: rc.data.rate_limit_por_hora,
      horario_inicio: rc.data.horario_inicio,
      horario_fim: rc.data.horario_fim,
      instancias_ids: rc.data.instancias_ids ?? [],
    }

    if (rc.data.data_source) {
      const ds = rc.data.data_source
      const isInternal = !!ds.use_system_token
      dsSourceType.value = isInternal ? 'interna' : 'externa'
      dsForm.value = {
        url: ds.url ?? '',
        method: ds.method ?? 'GET',
        chave_contato: ds.chave_contato ?? 'telefone',
        mode: ds.mode ?? 'bulk',
        body_template: ds.body_template ?? '',
        mapeamento: Object.entries(ds.mapeamento ?? {}).map(([key, path]) => ({ key, path: path as string })),
        headers: Array.isArray(ds.headers) ? ds.headers : [],
        use_system_token: !!ds.use_system_token,
      }
    }
  } finally {
    loading.value = false
  }
}

// ── Config ─────────────────────────────────────────────────────────────────────
async function salvarConfig() {
  saving.value = true
  try {
    const r = await apiClient.put<Campanha>(`/campanhas/${campanhaId}`, configForm.value)
    campanha.value = r.data
  } finally {
    saving.value = false
  }
}
function toggleInstancia(id: number) {
  const idx = configForm.value.instancias_ids.indexOf(id)
  if (idx === -1) configForm.value.instancias_ids.push(id)
  else configForm.value.instancias_ids.splice(idx, 1)
}

// ── Status ─────────────────────────────────────────────────────────────────────
async function ativar() { actionLoading.value = true; try { campanha.value = (await apiClient.post<Campanha>(`/campanhas/${campanhaId}/ativar`)).data } finally { actionLoading.value = false } }
async function pausar() { actionLoading.value = true; try { campanha.value = (await apiClient.post<Campanha>(`/campanhas/${campanhaId}/pausar`)).data } finally { actionLoading.value = false } }
async function concluir() { actionLoading.value = true; try { campanha.value = (await apiClient.post<Campanha>(`/campanhas/${campanhaId}/concluir`)).data } finally { actionLoading.value = false } }

// ── Templates ──────────────────────────────────────────────────────────────────
async function adicionarTemplate() {
  if (!novoTemplate.value.trim()) return
  const r = await apiClient.post<Template>(`/campanhas/${campanhaId}/templates`, { conteudo: novoTemplate.value })
  templates.value.push(r.data)
  novoTemplate.value = ''
}
async function deletarTemplate(id: number) {
  await apiClient.delete(`/templates/${id}`)
  templates.value = templates.value.filter(t => t.id !== id)
}

// ── Data Source ────────────────────────────────────────────────────────────────
function onSelectInternalEndpoint() {
  const ep = INTERNAL_ENDPOINTS.find(e => e.label === selectedEndpoint.value)
  if (!ep) return
  dsForm.value.url = ep.path
  dsForm.value.method = ep.method
  dsForm.value.chave_contato = ep.chave_contato
  dsForm.value.mode = ep.mode
  dsForm.value.mapeamento = ep.mapeamento.map(m => ({ ...m }))
  dsForm.value.use_system_token = true
}

function onSourceTypeChange() {
  if (dsSourceType.value === 'interna') {
    dsForm.value.use_system_token = true
    selectedEndpoint.value = ''
  } else {
    dsForm.value.use_system_token = false
  }
}

async function salvarDS() {
  saving.value = true
  try {
    const mapeamento: Record<string, string> = {}
    dsForm.value.mapeamento.forEach(m => { if (m.key) mapeamento[m.key] = m.path })
    const ds = {
      url: dsForm.value.url,
      method: dsForm.value.method,
      chave_contato: dsForm.value.chave_contato,
      mode: dsForm.value.mode,
      body_template: dsForm.value.body_template || undefined,
      mapeamento,
      headers: dsForm.value.headers.filter(h => h.key.trim()),
      use_system_token: dsForm.value.use_system_token,
    }
    const r = await apiClient.put<Campanha>(`/campanhas/${campanhaId}`, { data_source: ds })
    campanha.value = r.data
  } finally {
    saving.value = false
  }
}
function addMapeamento() { dsForm.value.mapeamento.push({ key: '', path: '' }) }
function removeMapeamento(i: number) { dsForm.value.mapeamento.splice(i, 1) }
function addHeader() { dsForm.value.headers.push({ key: '', value: '' }) }
function removeHeader(i: number) { dsForm.value.headers.splice(i, 1) }

// ── Contatos ───────────────────────────────────────────────────────────────────
async function adicionarContato() {
  if (!novoNumero.value.trim()) return
  const r = await apiClient.post<Contato>(`/campanhas/${campanhaId}/contatos`, {
    numero: novoNumero.value.trim(), nome: novoNome.value.trim() || undefined,
  })
  contatos.value.push(r.data)
  novoNumero.value = ''; novoNome.value = ''
  if (campanha.value) campanha.value.total_contatos++
}
async function adicionarBulk() {
  const numeros = bulkTexto.value.split('\n').map(n => n.trim()).filter(Boolean)
  if (!numeros.length) return
  const r = await apiClient.post<Contato[]>(`/campanhas/${campanhaId}/contatos/bulk`, { numeros })
  contatos.value.push(...r.data)
  bulkTexto.value = ''
  if (campanha.value) campanha.value.total_contatos += r.data.length
}
async function deletarContato(id: number) {
  await apiClient.delete(`/contatos/${id}`)
  contatos.value = contatos.value.filter(c => c.id !== id)
  if (campanha.value) campanha.value.total_contatos--
}
async function resolverVariaveis() {
  resolvingVars.value = true
  try { await apiClient.post(`/campanhas/${campanhaId}/ativar`); await carregar() }
  finally { resolvingVars.value = false }
}

// ── Helpers ────────────────────────────────────────────────────────────────────
const statusInfo: Record<string, { label: string; bg: string; color: string }> = {
  RASCUNHO:  { label: 'Rascunho',  bg: '#f1f5f9', color: '#475569' },
  ATIVA:     { label: 'Ativa',     bg: '#d1fae5', color: '#065f46' },
  PAUSADA:   { label: 'Pausada',   bg: '#fef3c7', color: '#92400e' },
  CONCLUIDA: { label: 'Concluída', bg: '#e0e7ff', color: '#3730a3' },
}
const contatoStatusColor: Record<string, string> = {
  PENDENTE: '#94a3b8', ENVIANDO: '#f59e0b', ENVIADO: '#059669', FALHOU: '#dc2626',
  RESPONDEU: '#6366f1', EM_ATENDIMENTO: '#8b5cf6',
}
const contatoStatusLabel: Record<string, string> = {
  PENDENTE: 'Pendente', ENVIANDO: 'Enviando', ENVIADO: 'Enviado', FALHOU: 'Falhou',
  RESPONDEU: 'Respondeu', EM_ATENDIMENTO: 'Em atendimento',
}

function fmtDateTime(ts: string | null) {
  if (!ts) return '—'
  const d = new Date(ts)
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) + ' ' +
    d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

async function refreshContatos() {
  const r = await apiClient.get<Contato[]>(`/campanhas/${campanhaId}/contatos`).catch(() => null)
  if (r) contatos.value = r.data
}

onMounted(async () => {
  await carregar()
  logsInterval = setInterval(async () => {
    if (campanha.value?.status === 'ATIVA') await refreshContatos()
  }, 15000)
})
onUnmounted(() => { if (logsInterval) clearInterval(logsInterval) })
</script>

<template>
  <div style="display:flex;flex-direction:column;height:100%;position:relative;">

    <!-- Header -->
    <div style="height:64px;border-bottom:1px solid #e2e8f0;background:white;display:flex;align-items:center;justify-content:space-between;padding:0 24px;flex-shrink:0;gap:12px;">
      <div style="display:flex;align-items:center;gap:12px;min-width:0;">
        <button @click="router.push('/campanhas')" style="background:none;border:none;cursor:pointer;padding:4px;color:#94a3b8;display:flex;flex-shrink:0;">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px;"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" /></svg>
        </button>
        <div style="min-width:0;">
          <h1 style="font-size:15px;font-weight:600;color:#0f172a;margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{{ campanha?.nome ?? 'Carregando...' }}</h1>
          <span v-if="campanha" :style="`background:${statusInfo[campanha.status].bg};color:${statusInfo[campanha.status].color};`" style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;">{{ statusInfo[campanha.status].label }}</span>
        </div>
      </div>
      <div v-if="campanha" style="display:flex;gap:8px;flex-shrink:0;">
        <button v-if="authStore.can('campanha:activate') && campanha.status !== 'ATIVA'" @click="ativar" :disabled="actionLoading" style="background:#059669;color:white;font-size:12px;font-weight:600;padding:7px 14px;border-radius:8px;border:none;cursor:pointer;">Ativar</button>
        <button v-if="authStore.can('campanha:activate') && campanha.status === 'ATIVA'" @click="pausar" :disabled="actionLoading" style="background:#d97706;color:white;font-size:12px;font-weight:600;padding:7px 14px;border-radius:8px;border:none;cursor:pointer;">Pausar</button>
        <button v-if="authStore.can('campanha:activate') && campanha.status !== 'CONCLUIDA'" @click="concluir" :disabled="actionLoading" style="background:#6366f1;color:white;font-size:12px;font-weight:600;padding:7px 14px;border-radius:8px;border:none;cursor:pointer;">Concluir</button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" style="display:flex;align-items:center;justify-content:center;height:200px;">
      <svg style="width:22px;height:22px;color:#4f46e5;animation:spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle style="opacity:.25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
        <path style="opacity:.75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
      </svg>
    </div>

    <div v-else style="flex:1;overflow:auto;padding:24px;display:flex;flex-direction:column;gap:20px;">

      <!-- Stats strip -->
      <div v-if="campanha" style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;">
          <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;margin:0 0 2px;">Total</p>
          <p style="font-size:20px;font-weight:700;color:#0f172a;margin:0;">{{ campanha.total_contatos }}</p>
        </div>
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;">
          <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;margin:0 0 2px;">Pendentes</p>
          <p style="font-size:20px;font-weight:700;color:#d97706;margin:0;">{{ campanha.pendentes }}</p>
        </div>
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;">
          <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;margin:0 0 2px;">Enviados</p>
          <p style="font-size:20px;font-weight:700;color:#059669;margin:0;">{{ campanha.enviados }}</p>
        </div>
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;">
          <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;margin:0 0 2px;">Falhos</p>
          <p style="font-size:20px;font-weight:700;color:#dc2626;margin:0;">{{ campanha.falhos }}</p>
        </div>
      </div>

      <!-- Grid 2 colunas -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start;">

        <!-- Configurações -->
        <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px;">
          <h2 style="font-size:13px;font-weight:700;color:#0f172a;margin:0 0 16px;">Configurações</h2>
          <div style="display:flex;flex-direction:column;gap:12px;">
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Nome</label>
              <input v-model="configForm.nome" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;box-sizing:border-box;" />
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
              <div>
                <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Rate/hora</label>
                <input v-model.number="configForm.rate_limit_por_hora" type="number" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;box-sizing:border-box;" />
              </div>
              <div>
                <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Início (h)</label>
                <input v-model.number="configForm.horario_inicio" type="number" min="0" max="23" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;box-sizing:border-box;" />
              </div>
              <div>
                <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Fim (h)</label>
                <input v-model.number="configForm.horario_fim" type="number" min="0" max="23" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;box-sizing:border-box;" />
              </div>
            </div>
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:8px;">Instâncias WhatsApp</label>
              <div style="display:flex;flex-wrap:wrap;gap:6px;">
                <label
                  v-for="inst in instancias" :key="inst.id"
                  style="display:flex;align-items:center;gap:6px;padding:5px 10px;border-radius:8px;border:1.5px solid #e5e7eb;cursor:pointer;font-size:12px;font-weight:500;color:#334155;"
                  :style="configForm.instancias_ids.includes(inst.id) ? 'border-color:#4f46e5;background:#ede9fe;color:#4f46e5;' : ''"
                >
                  <input type="checkbox" :checked="configForm.instancias_ids.includes(inst.id)" @change="toggleInstancia(inst.id)" style="display:none;" />
                  <span style="width:6px;height:6px;border-radius:50%;display:inline-block;" :style="inst.status === 'CONECTADA' ? 'background:#059669;' : 'background:#94a3b8;'"></span>
                  {{ inst.instance_name }}
                </label>
                <span v-if="instancias.length === 0" style="font-size:12px;color:#94a3b8;">Nenhuma instância conectada</span>
              </div>
            </div>
            <button v-if="authStore.can('campanha:update')" @click="salvarConfig" :disabled="saving" style="background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:9px;border-radius:8px;border:none;cursor:pointer;margin-top:4px;">
              {{ saving ? 'Salvando...' : 'Salvar configurações' }}
            </button>
          </div>
        </div>

        <!-- Templates -->
        <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
            <h2 style="font-size:13px;font-weight:700;color:#0f172a;margin:0;">Templates de Mensagem</h2>
            <!-- Botão de ajuda -->
            <div style="position:relative;">
              <button
                @mouseenter="showTemplateTooltip = true"
                @mouseleave="showTemplateTooltip = false"
                style="background:none;border:1.5px solid #e5e7eb;border-radius:50%;width:22px;height:22px;cursor:pointer;color:#64748b;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;"
              >?</button>
              <!-- Tooltip -->
              <div v-if="showTemplateTooltip" style="position:absolute;right:0;top:28px;width:300px;background:#0f172a;color:white;border-radius:10px;padding:14px;font-size:12px;line-height:1.55;z-index:100;box-shadow:0 8px 24px rgba(0,0,0,.3);">
                <p style="font-weight:700;margin:0 0 8px;font-size:12px;">Como funciona</p>
                <p style="margin:0 0 8px;color:#94a3b8;">Cada mensagem é enviada <strong style="color:white;">individualmente</strong> para cada contato, com as variáveis substituídas pelos dados daquele contato.</p>
                <p style="font-weight:600;margin:0 0 6px;color:#a5b4fc;">Variáveis padrão (sempre disponíveis):</p>
                <div style="background:#1e293b;border-radius:6px;padding:8px 10px;margin-bottom:8px;font-family:monospace;font-size:11px;display:flex;flex-direction:column;gap:3px;">
                  <span><span style="color:#7dd3fc;">&#123;&#123; numero &#125;&#125;</span> — número do contato</span>
                  <span><span style="color:#7dd3fc;">&#123;&#123; nome &#125;&#125;</span> — nome do contato</span>
                </div>
                <p style="font-weight:600;margin:0 0 6px;color:#a5b4fc;">Variáveis do Data Source:</p>
                <div style="background:#1e293b;border-radius:6px;padding:8px 10px;font-family:monospace;font-size:11px;display:flex;flex-direction:column;gap:3px;">
                  <span><span style="color:#86efac;">&#123;&#123; saldo &#125;&#125;</span> — campo mapeado no data source</span>
                  <span><span style="color:#86efac;">&#123;&#123; vencimento &#125;&#125;</span> — qualquer campo mapeado</span>
                </div>
                <p style="margin:10px 0 0;color:#94a3b8;font-size:11px;">Se houver mais de um template, um será escolhido aleatoriamente por contato.</p>
              </div>
            </div>
          </div>

          <!-- Info box variáveis padrão -->
          <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;padding:10px 12px;margin-bottom:12px;">
            <p style="font-size:11px;font-weight:700;color:#166534;margin:0 0 5px;">Variáveis padrão — disponíveis em todos os templates</p>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
              <code style="background:#dcfce7;color:#15803d;padding:2px 8px;border-radius:5px;font-size:11px;font-weight:600;">&#123;&#123; numero &#125;&#125;</code>
              <code style="background:#dcfce7;color:#15803d;padding:2px 8px;border-radius:5px;font-size:11px;font-weight:600;">&#123;&#123; nome &#125;&#125;</code>
            </div>
            <p style="font-size:11px;color:#166534;margin:5px 0 0;opacity:.8;">Adicione mais variáveis configurando o Data Source abaixo.</p>
          </div>

          <!-- Lista de templates -->
          <div style="display:flex;flex-direction:column;gap:8px;margin-bottom:12px;">
            <div
              v-for="t in templates" :key="t.id"
              style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;display:flex;align-items:flex-start;gap:10px;"
            >
              <pre style="flex:1;font-size:12px;color:#334155;margin:0;white-space:pre-wrap;word-break:break-word;font-family:inherit;">{{ t.conteudo }}</pre>
              <button v-if="authStore.can('campanha:update')" @click="deletarTemplate(t.id)" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:2px;flex-shrink:0;">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:14px;height:14px;"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <p v-if="templates.length === 0" style="font-size:12px;color:#94a3b8;text-align:center;padding:12px;">Nenhum template. Adicione pelo menos um abaixo.</p>
          </div>

          <!-- Add template -->
          <div style="display:flex;flex-direction:column;gap:6px;">
            <textarea
              v-model="novoTemplate"
              placeholder="Olá {{ nome }}, seu número {{ numero }} está cadastrado. Você tem um saldo de R$ {{ saldo }}."
              rows="3"
              style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;box-sizing:border-box;resize:vertical;font-family:monospace;"
            ></textarea>
            <button v-if="authStore.can('campanha:update')" @click="adicionarTemplate" style="background:#0f172a;color:white;font-size:12px;font-weight:600;padding:8px;border-radius:8px;border:none;cursor:pointer;">Adicionar template</button>
          </div>
        </div>

        <!-- Data Source -->
        <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px;">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px;">
            <div>
              <h2 style="font-size:13px;font-weight:700;color:#0f172a;margin:0 0 2px;">Data Source <span style="font-size:11px;font-weight:500;color:#94a3b8;">(opcional)</span></h2>
              <p style="font-size:11px;color:#64748b;margin:0;">Enriquece cada contato com dados externos ou do próprio sistema</p>
            </div>
          </div>

          <div style="display:flex;flex-direction:column;gap:12px;">

            <!-- Tipo de fonte -->
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Tipo de fonte</label>
              <div style="display:flex;gap:6px;">
                <button
                  @click="dsSourceType = 'externa'; onSourceTypeChange()"
                  :style="dsSourceType === 'externa' ? 'background:#4f46e5;color:white;border-color:#4f46e5;' : 'background:white;color:#475569;border-color:#e5e7eb;'"
                  style="flex:1;padding:7px;border-radius:8px;border:1.5px solid;font-size:12px;font-weight:600;cursor:pointer;"
                >URL externa</button>
                <button
                  @click="dsSourceType = 'interna'; onSourceTypeChange()"
                  :style="dsSourceType === 'interna' ? 'background:#4f46e5;color:white;border-color:#4f46e5;' : 'background:white;color:#475569;border-color:#e5e7eb;'"
                  style="flex:1;padding:7px;border-radius:8px;border:1.5px solid;font-size:12px;font-weight:600;cursor:pointer;"
                >Sistema interno</button>
              </div>
            </div>

            <!-- Endpoints internos -->
            <template v-if="dsSourceType === 'interna'">
              <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 12px;">
                <p style="font-size:11px;font-weight:700;color:#1d4ed8;margin:0 0 4px;">Token de autenticação automático</p>
                <p style="font-size:11px;color:#3b82f6;margin:0;">O sistema gera e injeta automaticamente o token do owner do tenant nas requisições.</p>
              </div>
              <div>
                <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Selecionar endpoint do sistema</label>
                <select
                  v-model="selectedEndpoint"
                  @change="onSelectInternalEndpoint"
                  style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;background:white;"
                >
                  <option value="">— escolha um endpoint —</option>
                  <option v-for="ep in INTERNAL_ENDPOINTS" :key="ep.label" :value="ep.label">
                    {{ ep.label }}
                  </option>
                </select>
                <!-- Descrição do endpoint selecionado -->
                <p v-if="selectedEndpoint" style="font-size:11px;color:#64748b;margin:5px 0 0;">
                  {{ INTERNAL_ENDPOINTS.find(e => e.label === selectedEndpoint)?.description }}
                </p>
              </div>
            </template>

            <!-- URL + Method -->
            <div style="display:grid;grid-template-columns:1fr auto;gap:8px;align-items:end;">
              <div>
                <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">URL</label>
                <input
                  v-model="dsForm.url"
                  :placeholder="dsSourceType === 'interna' ? '/api/usuarios/' : 'https://api.exemplo.com/dados'"
                  style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;box-sizing:border-box;"
                />
                <p v-if="dsSourceType === 'interna' && dsForm.url.startsWith('/')" style="font-size:11px;color:#94a3b8;margin:3px 0 0;">
                  Será chamado como <code style="background:#f1f5f9;padding:1px 4px;border-radius:3px;">http://app:8000{{ dsForm.url }}</code>
                </p>
              </div>
              <div>
                <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Método</label>
                <select v-model="dsForm.method" style="border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;background:white;">
                  <option>GET</option><option>POST</option><option>PUT</option><option>PATCH</option>
                </select>
              </div>
            </div>

            <!-- Mode + Chave -->
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
              <div>
                <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Modo</label>
                <select v-model="dsForm.mode" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;background:white;">
                  <option value="bulk">bulk — 1 req. com todos os números</option>
                  <option value="per_contact">per_contact — 1 req. por contato</option>
                </select>
              </div>
              <div>
                <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Campo de matching</label>
                <input v-model="dsForm.chave_contato" placeholder="telefone" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;box-sizing:border-box;" />
              </div>
            </div>

            <!-- Headers -->
            <div>
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <label style="font-size:12px;font-weight:600;color:#374151;">Headers HTTP</label>
                <button @click="addHeader" style="background:none;border:none;cursor:pointer;font-size:11px;font-weight:600;color:#4f46e5;padding:0;">+ Adicionar</button>
              </div>
              <div style="display:flex;flex-direction:column;gap:5px;">
                <div v-for="(h, i) in dsForm.headers" :key="i" style="display:flex;gap:6px;align-items:center;">
                  <input v-model="h.key" placeholder="Authorization" style="width:120px;border:1.5px solid #e5e7eb;border-radius:7px;padding:6px 10px;font-size:12px;outline:none;" />
                  <span style="color:#94a3b8;font-size:12px;flex-shrink:0;">:</span>
                  <input v-model="h.value" placeholder="Bearer token123" style="flex:1;border:1.5px solid #e5e7eb;border-radius:7px;padding:6px 10px;font-size:12px;outline:none;" />
                  <button @click="removeHeader(i)" style="background:none;border:none;cursor:pointer;color:#94a3b8;flex-shrink:0;">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:14px;height:14px;"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                </div>
                <p v-if="dsForm.headers.length === 0" style="font-size:11px;color:#94a3b8;margin:0;">Nenhum header customizado.</p>
              </div>
            </div>

            <!-- Body template (apenas POST) -->
            <div v-if="dsForm.method === 'POST'">
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Body template <span style="font-weight:400;color:#94a3b8;">(use {lista_numeros} no modo bulk)</span></label>
              <textarea
                v-model="dsForm.body_template"
                placeholder='{"numeros": {lista_numeros}}'
                rows="2"
                style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:12px;outline:none;box-sizing:border-box;resize:vertical;font-family:monospace;"
              ></textarea>
            </div>

            <!-- Mapeamento de variáveis -->
            <div>
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;">
                <label style="font-size:12px;font-weight:600;color:#374151;">Mapeamento de variáveis <span style="font-weight:400;color:#64748b;">(JSONPath)</span></label>
                <button @click="addMapeamento" style="background:none;border:none;cursor:pointer;font-size:11px;font-weight:600;color:#4f46e5;padding:0;">+ Campo</button>
              </div>
              <div style="display:flex;flex-direction:column;gap:5px;">
                <div v-for="(m, i) in dsForm.mapeamento" :key="i" style="display:flex;gap:6px;align-items:center;">
                  <code style="font-size:12px;color:#6366f1;background:#ede9fe;padding:2px 7px;border-radius:5px;white-space:nowrap;">&#123;&#123; </code>
                  <input v-model="m.key" placeholder="nome_var" style="width:90px;border:1.5px solid #e5e7eb;border-radius:7px;padding:6px 10px;font-size:12px;outline:none;font-family:monospace;" />
                  <code style="font-size:12px;color:#6366f1;background:#ede9fe;padding:2px 7px;border-radius:5px;white-space:nowrap;"> &#125;&#125;</code>
                  <span style="color:#94a3b8;font-size:11px;flex-shrink:0;">← JSONPath:</span>
                  <input v-model="m.path" placeholder="$.dados.nome" style="flex:1;border:1.5px solid #e5e7eb;border-radius:7px;padding:6px 10px;font-size:12px;outline:none;font-family:monospace;" />
                  <button @click="removeMapeamento(i)" style="background:none;border:none;cursor:pointer;color:#94a3b8;flex-shrink:0;">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:14px;height:14px;"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
                  </button>
                </div>
                <p v-if="dsForm.mapeamento.length === 0" style="font-size:11px;color:#94a3b8;margin:0;">Nenhum mapeamento. Os dados da resposta serão salvos e você define quais campos viram variáveis.</p>
              </div>
            </div>

            <button v-if="authStore.can('campanha:update')" @click="salvarDS" :disabled="saving" style="background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:9px;border-radius:8px;border:none;cursor:pointer;">
              {{ saving ? 'Salvando...' : 'Salvar data source' }}
            </button>
          </div>
        </div>

        <!-- Contatos -->
        <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px;">
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
            <h2 style="font-size:13px;font-weight:700;color:#0f172a;margin:0;">Contatos <span style="color:#94a3b8;font-weight:500;">({{ contatos.length }})</span></h2>
            <button @click="resolverVariaveis" :disabled="resolvingVars" style="background:#f1f5f9;color:#334155;font-size:11px;font-weight:600;padding:5px 10px;border-radius:7px;border:none;cursor:pointer;">
              {{ resolvingVars ? 'Resolvendo...' : 'Resolver variáveis' }}
            </button>
          </div>

          <!-- Adicionar individual -->
          <div style="display:flex;gap:6px;margin-bottom:8px;">
            <input v-model="novoNumero" placeholder="Número (5511999999999)" style="flex:1;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;" />
            <input v-model="novoNome" placeholder="Nome" style="flex:1;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;" />
            <button v-if="authStore.can('campanha:update')" @click="adicionarContato" style="background:#0f172a;color:white;font-size:12px;font-weight:600;padding:8px 12px;border-radius:8px;border:none;cursor:pointer;white-space:nowrap;">+</button>
          </div>

          <!-- Bulk -->
          <div style="margin-bottom:12px;">
            <textarea v-model="bulkTexto" placeholder="Um número por linha:&#10;5511999999999&#10;5521888888888" rows="3" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;outline:none;box-sizing:border-box;resize:vertical;"></textarea>
            <button v-if="authStore.can('campanha:update')" @click="adicionarBulk" style="background:#f1f5f9;color:#334155;font-size:12px;font-weight:600;padding:7px;border-radius:8px;border:none;cursor:pointer;width:100%;margin-top:4px;">Importar em massa</button>
          </div>

          <!-- Lista -->
          <div style="max-height:280px;overflow-y:auto;display:flex;flex-direction:column;gap:1px;">
            <div v-for="c in contatos" :key="c.id" style="display:flex;align-items:center;gap:10px;padding:7px 10px;border-radius:8px;background:#f8fafc;">
              <span :style="`width:6px;height:6px;border-radius:50%;background:${contatoStatusColor[c.status] ?? '#94a3b8'};flex-shrink:0;`"></span>
              <div style="flex:1;min-width:0;">
                <p style="font-size:13px;font-weight:500;color:#0f172a;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ c.nome ?? c.numero }}</p>
                <p v-if="c.nome" style="font-size:11px;color:#64748b;margin:0;">{{ c.numero }}</p>
                <p v-if="c.erro" style="font-size:11px;color:#dc2626;margin:0;">{{ c.erro }}</p>
              </div>
              <span style="font-size:10px;font-weight:600;color:#94a3b8;flex-shrink:0;">{{ c.status }}</span>
              <button v-if="authStore.can('campanha:update')" @click="deletarContato(c.id)" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:2px;flex-shrink:0;">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:13px;height:13px;"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            <p v-if="contatos.length === 0" style="font-size:12px;color:#94a3b8;text-align:center;padding:16px;">Nenhum contato adicionado</p>
          </div>
        </div>

      </div><!-- fim grid -->

      <!-- Logs de Envio -->
      <div style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;gap:12px;flex-wrap:wrap;">
          <div>
            <h2 style="font-size:13px;font-weight:700;color:#0f172a;margin:0 0 2px;">Logs de Envio</h2>
            <p style="font-size:11px;color:#64748b;margin:0;">Histórico de tentativas de envio por contato{{ campanha?.status === 'ATIVA' ? ' · atualiza a cada 15s' : '' }}</p>
          </div>
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
            <!-- Filtros por status -->
            <button
              v-for="f in [['', 'Todos'], ['PENDENTE', 'Pendentes'], ['ENVIANDO', 'Enviando'], ['ENVIADO', 'Enviados'], ['FALHOU', 'Falhos'], ['RESPONDEU', 'Responderam']]"
              :key="f[0]"
              @click="logsStatusFiltro = f[0]"
              :style="logsStatusFiltro === f[0] ? 'background:#4f46e5;color:white;border-color:#4f46e5;' : 'background:white;color:#475569;border-color:#e5e7eb;'"
              style="padding:5px 12px;border-radius:999px;border:1.5px solid;font-size:11px;font-weight:600;cursor:pointer;"
            >{{ f[1] }}</button>
            <button @click="refreshContatos" style="background:none;border:1.5px solid #e5e7eb;border-radius:8px;padding:5px 10px;font-size:11px;font-weight:600;color:#475569;cursor:pointer;display:flex;align-items:center;gap:4px;">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:12px;height:12px;"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99" /></svg>
              Atualizar
            </button>
          </div>
        </div>

        <div style="overflow-x:auto;">
          <table style="width:100%;border-collapse:collapse;font-size:12px;">
            <thead>
              <tr style="border-bottom:2px solid #f1f5f9;">
                <th style="text-align:left;padding:8px 12px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;white-space:nowrap;">Status</th>
                <th style="text-align:left;padding:8px 12px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;white-space:nowrap;">Número</th>
                <th style="text-align:left;padding:8px 12px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;white-space:nowrap;">Nome</th>
                <th style="text-align:left;padding:8px 12px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;white-space:nowrap;">Instância</th>
                <th style="text-align:left;padding:8px 12px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;white-space:nowrap;">Enviado em</th>
                <th style="text-align:left;padding:8px 12px;font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;white-space:nowrap;">Erro</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="contatosFiltrados.length === 0">
                <td colspan="6" style="padding:24px;text-align:center;color:#94a3b8;font-size:13px;">Nenhum registro encontrado.</td>
              </tr>
              <tr
                v-for="c in contatosFiltrados"
                :key="c.id"
                style="border-bottom:1px solid #f1f5f9;transition:background .1s;"
                @mouseenter="e => (e.currentTarget as HTMLElement).style.background='#fafafa'"
                @mouseleave="e => (e.currentTarget as HTMLElement).style.background=''"
              >
                <td style="padding:9px 12px;white-space:nowrap;">
                  <span
                    :style="`background:${contatoStatusColor[c.status] ?? '#94a3b8'}18;color:${contatoStatusColor[c.status] ?? '#94a3b8'};`"
                    style="font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;display:inline-block;"
                  >{{ contatoStatusLabel[c.status] ?? c.status }}</span>
                </td>
                <td style="padding:9px 12px;color:#334155;font-family:monospace;white-space:nowrap;">{{ c.numero }}</td>
                <td style="padding:9px 12px;color:#334155;max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ c.nome ?? '—' }}</td>
                <td style="padding:9px 12px;color:#64748b;white-space:nowrap;">
                  {{ c.instancia_id ? (instancias.find(i => i.id === c.instancia_id)?.instance_name ?? `#${c.instancia_id}`) : '—' }}
                </td>
                <td style="padding:9px 12px;color:#64748b;white-space:nowrap;">{{ fmtDateTime(c.enviado_em) }}</td>
                <td style="padding:9px 12px;max-width:240px;">
                  <span v-if="c.erro" style="color:#dc2626;font-size:11px;word-break:break-word;" :title="c.erro">{{ c.erro.length > 80 ? c.erro.slice(0, 80) + '…' : c.erro }}</span>
                  <span v-else style="color:#94a3b8;">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Resumo contagem -->
        <div style="display:flex;gap:16px;margin-top:14px;padding-top:12px;border-top:1px solid #f1f5f9;flex-wrap:wrap;">
          <span style="font-size:11px;color:#64748b;"><strong style="color:#0f172a;">{{ contatos.length }}</strong> total</span>
          <span style="font-size:11px;color:#d97706;"><strong>{{ contatos.filter(c => c.status === 'PENDENTE').length }}</strong> pendentes</span>
          <span style="font-size:11px;color:#f59e0b;"><strong>{{ contatos.filter(c => c.status === 'ENVIANDO').length }}</strong> enviando</span>
          <span style="font-size:11px;color:#059669;"><strong>{{ contatos.filter(c => c.status === 'ENVIADO').length }}</strong> enviados</span>
          <span style="font-size:11px;color:#dc2626;"><strong>{{ contatos.filter(c => c.status === 'FALHOU').length }}</strong> falhos</span>
          <span style="font-size:11px;color:#6366f1;"><strong>{{ contatos.filter(c => c.status === 'RESPONDEU').length }}</strong> responderam</span>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }
</style>
