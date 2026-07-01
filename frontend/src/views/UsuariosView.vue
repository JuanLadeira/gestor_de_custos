<template>
  <div style="display:flex;flex-direction:column;height:100%;background:#f8fafc;">
    <!-- Header -->
    <div style="height:64px;background:#fff;border-bottom:1px solid #e2e8f0;display:flex;align-items:center;justify-content:space-between;padding:0 24px;flex-shrink:0;">
      <div>
        <h1 style="font-size:15px;font-weight:600;color:#0f172a;margin:0;">Membros</h1>
        <p style="font-size:12px;color:#94a3b8;margin:2px 0 0;">Usuários do seu inquilino</p>
      </div>
      <button
        v-if="authStore.can('usuario:create')"
        @click="abrirModalCriar"
        style="display:flex;align-items:center;gap:8px;background:#4f46e5;color:#fff;border:none;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:500;cursor:pointer;"
        @mouseenter="(e) => (e.currentTarget as HTMLElement).style.background='#4338ca'"
        @mouseleave="(e) => (e.currentTarget as HTMLElement).style.background='#4f46e5'"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Convidar membro
      </button>
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

      <!-- Empty -->
      <div v-else-if="usuarios.length === 0" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:200px;text-align:center;">
        <div style="width:48px;height:48px;background:#f1f5f9;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:12px;">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="#94a3b8" style="width:24px;height:24px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
          </svg>
        </div>
        <p style="font-size:14px;font-weight:500;color:#475569;margin:0;">Nenhum membro encontrado</p>
      </div>

      <!-- Cards grid -->
      <div v-else style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;">
        <div
          v-for="usuario in usuarios"
          :key="usuario.id"
          style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;"
        >
          <div style="display:flex;align-items:flex-start;gap:14px;">
            <!-- Avatar -->
            <div
              style="width:42px;height:42px;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:16px;font-weight:700;color:#fff;"
              :style="{ background: avatarColor(usuario.nome) }"
            >
              {{ usuario.nome.charAt(0).toUpperCase() }}
            </div>
            <!-- Info -->
            <div style="flex:1;min-width:0;">
              <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                <p style="font-size:14px;font-weight:600;color:#0f172a;margin:0;truncate:nowrap;">{{ usuario.nome }}</p>
                <span
                  style="font-size:10px;font-weight:600;padding:2px 7px;border-radius:999px;letter-spacing:.05em;text-transform:uppercase;background:#e0e7ff;color:#4338ca;"
                >{{ profileName(usuario.role_profile_id) }}</span>
                <span v-if="!usuario.ativo" style="font-size:10px;font-weight:600;padding:2px 7px;border-radius:999px;background:#fee2e2;color:#dc2626;letter-spacing:.05em;text-transform:uppercase;">Inativo</span>
              </div>
              <p style="font-size:12px;color:#64748b;margin:3px 0 0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">@{{ usuario.username }}</p>
              <p style="font-size:12px;color:#94a3b8;margin:2px 0 0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ usuario.email }}</p>
            </div>
          </div>
          <!-- Change profile (profile:assign) -->
          <div v-if="authStore.can('profile:assign') && usuario.id !== authStore.userId" style="margin-top:14px;padding-top:14px;border-top:1px solid #f1f5f9;">
            <label style="display:block;font-size:11px;font-weight:500;color:#94a3b8;margin-bottom:5px;">Perfil</label>
            <select
              :value="usuario.role_profile_id ?? ''"
              @change="(e) => alterarPerfil(usuario, Number((e.target as HTMLSelectElement).value))"
              style="width:100%;border:1px solid #e2e8f0;border-radius:8px;padding:6px 10px;font-size:12px;color:#0f172a;background:#fff;outline:none;box-sizing:border-box;"
            >
              <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.nome }}</option>
            </select>
          </div>
          <!-- Actions (usuario:delete, cannot delete yourself) -->
          <div v-if="authStore.can('usuario:delete') && usuario.id !== authStore.userId" style="margin-top:16px;padding-top:16px;border-top:1px solid #f1f5f9;display:flex;justify-content:flex-end;">
            <button
              @click="confirmarDelete(usuario)"
              style="display:flex;align-items:center;gap:6px;font-size:12px;color:#dc2626;background:none;border:1px solid #fee2e2;border-radius:6px;padding:5px 10px;cursor:pointer;"
              @mouseenter="(e) => (e.currentTarget as HTMLElement).style.background='#fef2f2'"
              @mouseleave="(e) => (e.currentTarget as HTMLElement).style.background='none'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" style="width:14px;height:14px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
              </svg>
              Remover
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create modal -->
    <div v-if="showModal" style="position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;">
      <div style="position:absolute;inset:0;background:rgba(15,23,42,.5);backdrop-filter:blur(4px);" @click="fecharModal"></div>
      <div style="position:relative;background:#fff;border-radius:16px;padding:28px;width:420px;max-width:95vw;box-shadow:0 25px 50px rgba(0,0,0,.15);">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
          <h2 style="font-size:16px;font-weight:600;color:#0f172a;margin:0;">Convidar membro</h2>
          <button @click="fecharModal" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:4px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div v-if="formError" style="background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:10px 14px;margin-bottom:16px;">
          <p style="font-size:12px;color:#dc2626;margin:0;">{{ formError }}</p>
        </div>

        <form @submit.prevent="criarUsuario" style="display:flex;flex-direction:column;gap:14px;">
          <div>
            <label style="display:block;font-size:12px;font-weight:500;color:#374151;margin-bottom:5px;">Nome completo</label>
            <input v-model="form.nome" required placeholder="Ex: João Silva" style="width:100%;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" @focus="(e) => (e.target as HTMLInputElement).style.borderColor='#6366f1'" @blur="(e) => (e.target as HTMLInputElement).style.borderColor='#e2e8f0'" />
          </div>
          <div>
            <label style="display:block;font-size:12px;font-weight:500;color:#374151;margin-bottom:5px;">Username</label>
            <input v-model="form.username" required placeholder="Ex: joaosilva" style="width:100%;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" @focus="(e) => (e.target as HTMLInputElement).style.borderColor='#6366f1'" @blur="(e) => (e.target as HTMLInputElement).style.borderColor='#e2e8f0'" />
          </div>
          <div>
            <label style="display:block;font-size:12px;font-weight:500;color:#374151;margin-bottom:5px;">Email</label>
            <input v-model="form.email" type="email" required placeholder="Ex: joao@email.com" style="width:100%;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" @focus="(e) => (e.target as HTMLInputElement).style.borderColor='#6366f1'" @blur="(e) => (e.target as HTMLInputElement).style.borderColor='#e2e8f0'" />
          </div>
          <div>
            <label style="display:block;font-size:12px;font-weight:500;color:#374151;margin-bottom:5px;">Senha</label>
            <input v-model="form.password" type="password" required placeholder="Senha inicial" style="width:100%;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" @focus="(e) => (e.target as HTMLInputElement).style.borderColor='#6366f1'" @blur="(e) => (e.target as HTMLInputElement).style.borderColor='#e2e8f0'" />
          </div>
          <div v-if="profiles.length">
            <label style="display:block;font-size:12px;font-weight:500;color:#374151;margin-bottom:5px;">Perfil</label>
            <select v-model="form.role_profile_id" style="width:100%;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;color:#0f172a;background:#fff;outline:none;box-sizing:border-box;">
              <option :value="null">Padrão (Membro)</option>
              <option v-for="p in profiles" :key="p.id" :value="p.id">{{ p.nome }}</option>
            </select>
          </div>
          <div style="display:flex;gap:10px;justify-content:flex-end;margin-top:4px;">
            <button type="button" @click="fecharModal" style="padding:8px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;font-weight:500;color:#64748b;background:#fff;cursor:pointer;">Cancelar</button>
            <button type="submit" :disabled="saving" style="padding:8px 20px;border:none;border-radius:8px;font-size:13px;font-weight:500;color:#fff;background:#4f46e5;cursor:pointer;display:flex;align-items:center;gap:6px;">
              <svg v-if="saving" style="width:13px;height:13px;animation:spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle style="opacity:.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                <path style="opacity:.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
              </svg>
              {{ saving ? 'Criando...' : 'Convidar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Delete confirm modal -->
    <div v-if="usuarioParaDelete" style="position:fixed;inset:0;z-index:50;display:flex;align-items:center;justify-content:center;">
      <div style="position:absolute;inset:0;background:rgba(15,23,42,.5);backdrop-filter:blur(4px);" @click="usuarioParaDelete=null"></div>
      <div style="position:relative;background:#fff;border-radius:16px;padding:28px;width:360px;box-shadow:0 25px 50px rgba(0,0,0,.15);">
        <h3 style="font-size:16px;font-weight:600;color:#0f172a;margin:0 0 8px;">Remover membro?</h3>
        <p style="font-size:13px;color:#64748b;margin:0 0 20px;">
          <strong>{{ usuarioParaDelete.nome }}</strong> será removido do inquilino. Esta ação não pode ser desfeita.
        </p>
        <div style="display:flex;gap:10px;justify-content:flex-end;">
          <button @click="usuarioParaDelete=null" style="padding:8px 16px;border:1px solid #e2e8f0;border-radius:8px;font-size:13px;font-weight:500;color:#64748b;background:#fff;cursor:pointer;">Cancelar</button>
          <button @click="deletarUsuario" style="padding:8px 16px;border:none;border-radius:8px;font-size:13px;font-weight:500;color:#fff;background:#dc2626;cursor:pointer;">Remover</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Usuario, type Profile } from '../api/client'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const usuarios = ref<Usuario[]>([])
const profiles = ref<Profile[]>([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const formError = ref('')
const usuarioParaDelete = ref<Usuario | null>(null)

const form = ref<{ nome: string; username: string; email: string; password: string; role_profile_id: number | null }>(
  { nome: '', username: '', email: '', password: '', role_profile_id: null },
)

function profileName(id: number | null): string {
  return profiles.value.find((p) => p.id === id)?.nome ?? '—'
}

async function alterarPerfil(usuario: Usuario, profileId: number) {
  try {
    const res = await api.assignProfile(usuario.id, profileId)
    const idx = usuarios.value.findIndex((u) => u.id === usuario.id)
    if (idx !== -1) usuarios.value[idx] = res.data
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Erro ao alterar perfil')
  }
}

const AVATAR_COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#10b981', '#3b82f6', '#ef4444']
function avatarColor(nome: string) {
  const code = nome.charCodeAt(0) + (nome.charCodeAt(1) || 0)
  return AVATAR_COLORS[code % AVATAR_COLORS.length]
}

onMounted(async () => {
  if (authStore.can('profile:read') || authStore.can('profile:assign')) {
    try {
      profiles.value = (await api.getProfiles()).data
    } catch {
      profiles.value = []
    }
  }
  await carregarUsuarios()
})

async function carregarUsuarios() {
  loading.value = true
  try {
    const res = await api.getUsuarios()
    usuarios.value = res.data.sort((a, b) => a.nome.localeCompare(b.nome))
  } finally {
    loading.value = false
  }
}

function abrirModalCriar() {
  form.value = { nome: '', username: '', email: '', password: '', role_profile_id: null }
  formError.value = ''
  showModal.value = true
}

function fecharModal() {
  showModal.value = false
  formError.value = ''
}

async function criarUsuario() {
  saving.value = true
  formError.value = ''
  try {
    const res = await api.createUsuario({
      nome: form.value.nome,
      username: form.value.username,
      email: form.value.email,
      password: form.value.password,
      role_profile_id: form.value.role_profile_id ?? undefined,
    })
    usuarios.value.push(res.data)
    usuarios.value.sort((a, b) => a.nome.localeCompare(b.nome))
    fecharModal()
  } catch (e: any) {
    formError.value = e.response?.data?.detail || 'Erro ao criar membro'
  } finally {
    saving.value = false
  }
}

function confirmarDelete(usuario: Usuario) {
  usuarioParaDelete.value = usuario
}

async function deletarUsuario() {
  if (!usuarioParaDelete.value) return
  await api.deleteUsuario(usuarioParaDelete.value.id)
  usuarios.value = usuarios.value.filter((u) => u.id !== usuarioParaDelete.value!.id)
  usuarioParaDelete.value = null
}
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
