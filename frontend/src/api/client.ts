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
  role_profile_id: number | null
  tenant_id: number
  created_at: string
  updated_at: string
}

export interface UsuarioMe extends Usuario {
  role_profile: { id: number; nome: string } | null
  permissions: string[]
}

export interface Permission {
  id: number
  code: string
  grupo: string
  descricao: string | null
}

export interface Role {
  id: number
  nome: string
  descricao: string | null
  is_system: boolean
  permission_codes: string[]
}

export interface Profile {
  id: number
  nome: string
  descricao: string | null
  is_system: boolean
  is_protected: boolean
  role_ids: number[]
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
  status: 'PENDENTE' | 'PARCIALMENTE_PAGO' | 'PAGO'
  mes_referencia_id: number
  custo_fixo_origem_id: number | null
}

export interface PagamentoRateio {
  id: number
  porcentagem: string
  valor_calculado: string
  status: 'PENDENTE' | 'PAGO'
  comprovante_url: string | null
  custo_id: number
  usuario_id: number
}

// ── API ──────────────────────────────────────────────────────────────────────

export const api = {
  // Auth
  login: (username: string, password: string) =>
    axios.post('/auth/login', new URLSearchParams({ username, password })),

  // Me
  getMe: () => apiClient.get<UsuarioMe>('/usuarios/me'),

  // Usuarios
  getUsuarios: () => apiClient.get<Usuario[]>('/usuarios/'),
  createUsuario: (data: { username: string; email: string; nome: string; password: string; role_profile_id?: number }) =>
    apiClient.post<Usuario>('/usuarios/', data),
  deleteUsuario: (id: number) => apiClient.delete(`/usuarios/${id}`),

  // Meses
  getMeses: () => apiClient.get<MesReferencia[]>('/meses/'),
  createMes: (data: { ano: number; mes: number }) =>
    apiClient.post<MesReferencia>('/meses/', data),
  getMesAtual: () => apiClient.get<MesReferencia>('/meses/atual'),
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
  importarFatura: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post<{ criados: number; ignorados: number; meses_afetados: number }>(
      '/custos/importar', form, { headers: { 'Content-Type': 'multipart/form-data' } },
    )
  },

  // Rateios
  getRateios: (params?: { custo_id?: number; usuario_id?: number }) =>
    apiClient.get<PagamentoRateio[]>('/rateios/', { params }),
  createRateio: (data: { porcentagem: string; custo_id: number; usuario_id: number }) =>
    apiClient.post<PagamentoRateio>('/rateios/', data),
  updateRateio: (id: number, data: { porcentagem?: string; status?: string }) =>
    apiClient.put<PagamentoRateio>(`/rateios/${id}`, data),
  deleteRateio: (id: number) => apiClient.delete(`/rateios/${id}`),
  uploadComprovante: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiClient.post<PagamentoRateio>(`/rateios/${id}/comprovante`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // Authz
  getPermissions: () => apiClient.get<Permission[]>('/authz/permissions'),
  getRoles: () => apiClient.get<Role[]>('/authz/roles'),
  createRole: (data: { nome: string; descricao?: string; permission_codes: string[] }) =>
    apiClient.post<Role>('/authz/roles', data),
  updateRole: (id: number, data: { nome?: string; descricao?: string; permission_codes?: string[] }) =>
    apiClient.put<Role>(`/authz/roles/${id}`, data),
  deleteRole: (id: number) => apiClient.delete(`/authz/roles/${id}`),
  getProfiles: () => apiClient.get<Profile[]>('/authz/profiles'),
  createProfile: (data: { nome: string; descricao?: string; role_ids: number[] }) =>
    apiClient.post<Profile>('/authz/profiles', data),
  updateProfile: (id: number, data: { nome?: string; descricao?: string; role_ids?: number[] }) =>
    apiClient.put<Profile>(`/authz/profiles/${id}`, data),
  deleteProfile: (id: number) => apiClient.delete(`/authz/profiles/${id}`),
  assignProfile: (usuarioId: number, profileId: number) =>
    apiClient.put<Usuario>(`/authz/usuarios/${usuarioId}/profile`, { role_profile_id: profileId }),
  getMyTenant: () => apiClient.get('/tenants/me'),
}

export default apiClient
