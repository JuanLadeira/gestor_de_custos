<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Permission, type Role, type Profile } from '../api/client'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const permissions = ref<Permission[]>([])
const roles = ref<Role[]>([])
const profiles = ref<Profile[]>([])
const loading = ref(true)

const showHelp = ref(false)
const roleForm = ref<{ id: number | null; nome: string; permission_codes: string[] }>({ id: null, nome: '', permission_codes: [] })
const profileForm = ref<{ id: number | null; nome: string; role_ids: number[] }>({ id: null, nome: '', role_ids: [] })

async function carregar() {
  loading.value = true
  try {
    const tasks: Promise<unknown>[] = []
    // Só busca o que o usuário tem permissão de ler — evita 403 quebrando a tela.
    if (authStore.can('profile:read')) {
      tasks.push(api.getProfiles().then((pr) => { profiles.value = pr.data }))
    }
    if (authStore.can('role:read')) {
      tasks.push(api.getRoles().then((r) => { roles.value = r.data }))
      tasks.push(api.getPermissions().then((p) => { permissions.value = p.data }))
    }
    await Promise.all(tasks)
  } finally { loading.value = false }
}

function togglePerm(code: string) {
  const i = roleForm.value.permission_codes.indexOf(code)
  if (i === -1) roleForm.value.permission_codes.push(code); else roleForm.value.permission_codes.splice(i, 1)
}
function toggleRole(id: number) {
  const i = profileForm.value.role_ids.indexOf(id)
  if (i === -1) profileForm.value.role_ids.push(id); else profileForm.value.role_ids.splice(i, 1)
}

async function salvarRole() {
  if (roleForm.value.id) await api.updateRole(roleForm.value.id, roleForm.value)
  else await api.createRole(roleForm.value)
  roleForm.value = { id: null, nome: '', permission_codes: [] }
  await carregar()
}
function editarRole(r: Role) { roleForm.value = { id: r.id, nome: r.nome, permission_codes: [...r.permission_codes] } }
async function removerRole(r: Role) { if (confirm(`Remover ${r.nome}?`)) { await api.deleteRole(r.id).catch(e => alert(e.response?.data?.detail)); await carregar() } }

async function salvarProfile() {
  if (profileForm.value.id) await api.updateProfile(profileForm.value.id, profileForm.value).catch(e => alert(e.response?.data?.detail))
  else await api.createProfile(profileForm.value)
  profileForm.value = { id: null, nome: '', role_ids: [] }
  await carregar()
}
function editarProfile(p: Profile) { profileForm.value = { id: p.id, nome: p.nome, role_ids: [...p.role_ids] } }
async function removerProfile(p: Profile) { if (confirm(`Remover ${p.nome}?`)) { await api.deleteProfile(p.id).catch(e => alert(e.response?.data?.detail)); await carregar() } }

onMounted(carregar)
</script>

<template>
  <div style="display:flex;flex-direction:column;height:100%;">
    <div style="height:64px;border-bottom:1px solid #e2e8f0;background:white;display:flex;align-items:center;justify-content:space-between;padding:0 24px;flex-shrink:0;">
      <div>
        <h1 style="font-size:15px;font-weight:600;color:#0f172a;margin:0;">Perfis &amp; Papéis</h1>
        <p style="font-size:12px;color:#64748b;margin:0;">Controle de permissões do seu grupo</p>
      </div>
      <button
        @click="showHelp = !showHelp"
        :title="showHelp ? 'Ocultar ajuda' : 'Como funciona esta tela?'"
        :aria-label="showHelp ? 'Ocultar ajuda' : 'Como funciona esta tela?'"
        :style="`width:28px;height:28px;border-radius:50%;border:1.5px solid ${showHelp ? '#4f46e5' : '#cbd5e1'};background:${showHelp ? '#4f46e5' : 'white'};color:${showHelp ? 'white' : '#64748b'};cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:14px;font-weight:700;font-style:italic;font-family:Georgia,serif;transition:all 0.15s;flex-shrink:0;`"
      >i</button>
    </div>

    <!-- Painel de ajuda -->
    <div v-if="showHelp" style="background:#f8faff;border-bottom:1px solid #e0e7ff;padding:18px 24px;">
      <p style="font-size:13px;color:#334155;margin:0 0 12px;line-height:1.5;">
        Esta tela controla <strong>quem pode fazer o quê</strong> no seu grupo. A permissão nunca é dada direto ao usuário — ela passa por duas camadas:
      </p>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:12px;">
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;">
          <p style="font-size:12px;font-weight:700;color:#4f46e5;margin:0 0 4px;">Papel (coluna da esquerda)</p>
          <p style="font-size:12px;color:#475569;margin:0;line-height:1.5;">
            É um <strong>conjunto de permissões</strong> (ações soltas, ex.: <code style="font-size:11px;">custo:create</code>, <code style="font-size:11px;">rateio:pay</code>). Pense num papel como uma função: "Financeiro", "Leitura". Marque as permissões que o papel concede.
          </p>
        </div>
        <div style="background:white;border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;">
          <p style="font-size:12px;font-weight:700;color:#0f172a;margin:0 0 4px;">Perfil (coluna da direita)</p>
          <p style="font-size:12px;color:#475569;margin:0;line-height:1.5;">
            É um <strong>conjunto de papéis</strong> e é o que se atribui a cada membro. Um perfil "Gerente" pode juntar os papéis "Financeiro" + "Leitura". Cada usuário tem exatamente um perfil.
          </p>
        </div>
      </div>
      <p style="font-size:12px;color:#64748b;margin:0;line-height:1.5;background:white;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px;">
        <strong style="color:#334155;">Fluxo:</strong> Permissão → <span style="color:#4f46e5;font-weight:600;">Papel</span> → <span style="color:#0f172a;font-weight:600;">Perfil</span> → Usuário.
        Para dar um novo acesso a alguém: adicione a permissão a um papel, garanta que um perfil inclua esse papel e atribua o perfil ao membro (na tela <em>Membros</em>).
        Papéis e perfis marcados como <em>(sistema)</em> / <em>(protegido)</em> não podem ser removidos.
      </p>
    </div>
    <div style="flex:1;overflow:auto;padding:24px;display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start;">

      <!-- Roles -->
      <div v-if="authStore.can('role:read')" style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px;">
        <h2 style="font-size:13px;font-weight:700;color:#0f172a;margin:0 0 12px;">Papéis</h2>
        <div v-for="r in roles" :key="r.id" style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9;">
          <span style="font-size:13px;color:#0f172a;">{{ r.nome }} <span v-if="r.is_system" style="font-size:10px;color:#94a3b8;">(sistema)</span></span>
          <span v-if="authStore.can('role:manage')">
            <button @click="editarRole(r)" style="font-size:11px;color:#4f46e5;background:none;border:none;cursor:pointer;">editar</button>
            <button v-if="!r.is_system" @click="removerRole(r)" style="font-size:11px;color:#dc2626;background:none;border:none;cursor:pointer;">remover</button>
          </span>
        </div>
        <div v-if="authStore.can('role:manage')" style="margin-top:14px;border-top:1px solid #e2e8f0;padding-top:14px;">
          <input v-model="roleForm.nome" placeholder="Nome do papel" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;box-sizing:border-box;margin-bottom:8px;" />
          <div style="max-height:200px;overflow:auto;display:flex;flex-direction:column;gap:4px;margin-bottom:8px;">
            <label v-for="p in permissions" :key="p.id" style="font-size:12px;color:#334155;display:flex;gap:6px;align-items:center;">
              <input type="checkbox" :checked="roleForm.permission_codes.includes(p.code)" @change="togglePerm(p.code)" />
              <code style="font-size:11px;">{{ p.code }}</code>
            </label>
          </div>
          <button @click="salvarRole" style="background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:8px;border-radius:8px;border:none;cursor:pointer;width:100%;">
            {{ roleForm.id ? 'Salvar papel' : 'Criar papel' }}
          </button>
        </div>
      </div>

      <!-- Profiles -->
      <div v-if="authStore.can('profile:read')" style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:20px;">
        <h2 style="font-size:13px;font-weight:700;color:#0f172a;margin:0 0 12px;">Perfis</h2>
        <div v-for="p in profiles" :key="p.id" style="display:flex;align-items:center;justify-content:space-between;padding:8px 0;border-bottom:1px solid #f1f5f9;">
          <span style="font-size:13px;color:#0f172a;">{{ p.nome }} <span v-if="p.is_protected" style="font-size:10px;color:#d97706;">(protegido)</span></span>
          <span v-if="authStore.can('profile:manage') && !p.is_protected">
            <button @click="editarProfile(p)" style="font-size:11px;color:#4f46e5;background:none;border:none;cursor:pointer;">editar</button>
            <button v-if="!p.is_system" @click="removerProfile(p)" style="font-size:11px;color:#dc2626;background:none;border:none;cursor:pointer;">remover</button>
          </span>
        </div>
        <div v-if="authStore.can('profile:manage')" style="margin-top:14px;border-top:1px solid #e2e8f0;padding-top:14px;">
          <input v-model="profileForm.nome" placeholder="Nome do perfil" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;box-sizing:border-box;margin-bottom:8px;" />
          <div style="display:flex;flex-direction:column;gap:4px;margin-bottom:8px;">
            <label v-for="r in roles" :key="r.id" style="font-size:12px;color:#334155;display:flex;gap:6px;align-items:center;">
              <input type="checkbox" :checked="profileForm.role_ids.includes(r.id)" @change="toggleRole(r.id)" />
              {{ r.nome }}
            </label>
          </div>
          <button @click="salvarProfile" style="background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:8px;border-radius:8px;border:none;cursor:pointer;width:100%;">
            {{ profileForm.id ? 'Salvar perfil' : 'Criar perfil' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
