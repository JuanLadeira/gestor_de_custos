import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      sessionStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// ── Types ────────────────────────────────────────────────────────────────────

export interface Usuario {
  id: number
  username: string
  email: string
  nome: string
  ativo: boolean
  role: 'OWNER' | 'MEMBER'
  tenant_id: number
  created_at: string
  updated_at: string
}

export interface MesReferencia {
  id: number
  ano: number
  mes: number
  status: 'ABERTO' | 'FECHADO'
  tenant_id: number
  created_at: string
  updated_at: string
}

export interface Custo {
  id: number
  descricao: string
  valor: string
  data_vencimento: string
  tipo: 'FIXO' | 'VARIAVEL'
  status: 'PENDENTE' | 'PAGO'
  mes_referencia_id: number
  custo_fixo_origem_id: number | null
}

export interface PagamentoRateio {
  id: number
  porcentagem: string
  valor_calculado: string
  status: 'PENDENTE' | 'PAGO'
  custo_id: number
  usuario_id: number
}

// ── API ──────────────────────────────────────────────────────────────────────

export const api = {
  // Auth
  login: (username: string, password: string) =>
    axios.post('/auth/login', new URLSearchParams({ username, password })),

  // Me
  getMe: () => apiClient.get<Usuario>('/usuarios/me'),

  // Usuarios
  getUsuarios: (tenantId?: number) =>
    apiClient.get<Usuario[]>('/usuarios/', { params: { tenant_id: tenantId } }),
  createUsuario: (data: { username: string; email: string; nome: string; password: string; tenant_id: number; role?: string }) =>
    apiClient.post<Usuario>('/usuarios/', data),
  deleteUsuario: (id: number) => apiClient.delete(`/usuarios/${id}`),

  // Meses
  getMeses: (tenantId: number) =>
    apiClient.get<MesReferencia[]>('/meses/', { params: { tenant_id: tenantId } }),
  createMes: (data: { ano: number; mes: number; tenant_id: number }) =>
    apiClient.post<MesReferencia>('/meses/', data),
  getMesAtual: (tenantId: number) =>
    apiClient.get<MesReferencia>(`/meses/tenant/${tenantId}/atual`),
  importarCustosFixos: (mesId: number) =>
    apiClient.post(`/meses/${mesId}/importar-custos-fixos`),

  // Custos
  getCustos: (mesReferenciaId?: number) =>
    apiClient.get<Custo[]>('/custos/', { params: { mes_referencia_id: mesReferenciaId } }),
  createCusto: (data: { descricao: string; valor: string; data_vencimento: string; tipo: string; mes_referencia_id: number }) =>
    apiClient.post<Custo>('/custos/', data),
  updateCusto: (id: number, data: Partial<Custo>) =>
    apiClient.put<Custo>(`/custos/${id}`, data),
  deleteCusto: (id: number) => apiClient.delete(`/custos/${id}`),

  // Rateios
  getRateios: (params?: { custo_id?: number; usuario_id?: number }) =>
    apiClient.get<PagamentoRateio[]>('/rateios/', { params }),
  createRateio: (data: { porcentagem: string; custo_id: number; usuario_id: number }) =>
    apiClient.post<PagamentoRateio>('/rateios/', data),
  updateRateio: (id: number, data: { porcentagem?: string; status?: string }) =>
    apiClient.put<PagamentoRateio>(`/rateios/${id}`, data),
  deleteRateio: (id: number) => apiClient.delete(`/rateios/${id}`),
}

export default apiClient
