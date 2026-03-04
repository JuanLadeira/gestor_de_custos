import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle 401 responses
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export interface Tenant {
  id: number
  nome: string
  descricao: string | null
  created_at: string
  updated_at: string
}

export interface Usuario {
  id: number
  username: string
  email: string
  nome: string
  ativo: boolean
  tenant_id: number
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

export const api = {
  // Auth
  login: (username: string, password: string) =>
    axios.post('/auth/login', new URLSearchParams({ username, password })),

  // Tenants
  getTenants: () => apiClient.get<Tenant[]>('/tenants/'),
  createTenant: (data: { nome: string; descricao?: string }) =>
    apiClient.post<Tenant>('/tenants/', data),

  // Usuarios
  getUsuarios: (tenantId?: number) =>
    apiClient.get<Usuario[]>('/usuarios/', { params: { tenant_id: tenantId } }),

  // Custos
  getCustos: (mesReferenciaId?: number) =>
    apiClient.get<Custo[]>('/custos/', { params: { mes_referencia_id: mesReferenciaId } }),
  createCusto: (data: Partial<Custo>) =>
    apiClient.post<Custo>('/custos/', data),
  updateCusto: (id: number, data: Partial<Custo>) =>
    apiClient.put<Custo>(`/custos/${id}`, data),
  deleteCusto: (id: number) =>
    apiClient.delete(`/custos/${id}`),

  // Rateios
  getRateios: (custoId?: number, usuarioId?: number) =>
    apiClient.get<PagamentoRateio[]>('/rateios/', {
      params: { custo_id: custoId, usuario_id: usuarioId },
    }),
  createRateio: (data: { porcentagem: string; custo_id: number; usuario_id: number }) =>
    apiClient.post<PagamentoRateio>('/rateios/', data),
  updateRateio: (id: number, data: Partial<PagamentoRateio>) =>
    apiClient.put<PagamentoRateio>(`/rateios/${id}`, data),
  deleteRateio: (id: number) =>
    apiClient.delete(`/rateios/${id}`),

  // Meses
  getMesAtual: (tenantId: number) =>
    apiClient.get(`/meses/tenant/${tenantId}/atual`),
}

export default apiClient
