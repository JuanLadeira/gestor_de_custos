<template>
  <div style="display:flex;flex-direction:column;height:100%;position:relative;">

    <!-- Header -->
    <div style="height:64px;border-bottom:1px solid #e2e8f0;background:white;display:flex;align-items:center;justify-content:space-between;padding:0 24px;flex-shrink:0;">
      <div>
        <h1 style="font-size:15px;font-weight:600;color:#0f172a;margin:0;">Tenants</h1>
        <p style="font-size:12px;color:#64748b;margin:0;">{{ tenants.length }} grupo{{ tenants.length !== 1 ? 's' : '' }} cadastrado{{ tenants.length !== 1 ? 's' : '' }}</p>
      </div>
      <button
        @click="showCreate = true"
        style="display:flex;align-items:center;gap:6px;background:#7c3aed;color:white;font-size:13px;font-weight:600;padding:8px 14px;border-radius:9px;border:none;cursor:pointer;"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" style="width:14px;height:14px;">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
        </svg>
        Novo Tenant
      </button>
    </div>

    <!-- Content -->
    <div style="flex:1;overflow:auto;padding:24px;">

      <!-- Loading -->
      <div v-if="loading" style="display:flex;align-items:center;justify-content:center;height:200px;">
        <svg class="animate-spin" style="width:22px;height:22px;color:#7c3aed;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle style="opacity:.25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path style="opacity:.75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      </div>

      <!-- Error -->
      <div v-else-if="error" style="display:flex;align-items:center;gap:8px;background:#fef2f2;border:1px solid #fecaca;border-radius:12px;padding:12px 16px;font-size:13px;color:#b91c1c;">
        {{ error }}
      </div>

      <template v-else>
        <!-- Filters -->
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">
          <div style="position:relative;flex:1;max-width:280px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="#94a3b8" style="width:15px;height:15px;position:absolute;left:11px;top:50%;transform:translateY(-50%);pointer-events:none;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
            <input
              v-model="filtroNome"
              placeholder="Filtrar por nome..."
              style="width:100%;border:1px solid #e2e8f0;border-radius:9px;padding:8px 12px 8px 32px;font-size:13px;color:#0f172a;background:white;outline:none;box-sizing:border-box;"
              @focus="e => (e.target as HTMLInputElement).style.borderColor='#7c3aed'"
              @blur="e => (e.target as HTMLInputElement).style.borderColor='#e2e8f0'"
            />
          </div>
          <div style="position:relative;flex:1;max-width:280px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="#94a3b8" style="width:15px;height:15px;position:absolute;left:11px;top:50%;transform:translateY(-50%);pointer-events:none;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
            </svg>
            <input
              v-model="filtroDescricao"
              placeholder="Filtrar por descrição..."
              style="width:100%;border:1px solid #e2e8f0;border-radius:9px;padding:8px 12px 8px 32px;font-size:13px;color:#0f172a;background:white;outline:none;box-sizing:border-box;"
              @focus="e => (e.target as HTMLInputElement).style.borderColor='#7c3aed'"
              @blur="e => (e.target as HTMLInputElement).style.borderColor='#e2e8f0'"
            />
          </div>
          <button
            v-if="filtroNome || filtroDescricao"
            @click="filtroNome = ''; filtroDescricao = ''"
            style="display:flex;align-items:center;gap:5px;font-size:12px;color:#94a3b8;background:none;border:none;cursor:pointer;padding:4px 8px;border-radius:7px;white-space:nowrap;"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:13px;height:13px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Limpar
          </button>
          <p style="font-size:12px;color:#94a3b8;margin:0;margin-left:auto;white-space:nowrap;">
            {{ tenantsFiltrados.length }} de {{ tenants.length }} resultado{{ tenants.length !== 1 ? 's' : '' }}
          </p>
        </div>

        <!-- Empty -->
        <div v-if="tenantsFiltrados.length === 0" style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:56px 32px;text-align:center;">
          <div style="width:48px;height:48px;background:#f1f5f9;border-radius:12px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="#94a3b8" style="width:24px;height:24px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" />
            </svg>
          </div>
          <p style="font-size:14px;font-weight:600;color:#334155;margin:0 0 4px;">
            {{ tenants.length === 0 ? 'Nenhum tenant cadastrado' : 'Nenhum resultado para os filtros' }}
          </p>
          <p style="font-size:13px;color:#94a3b8;margin:0;">
            {{ tenants.length === 0 ? 'Crie o primeiro tenant para começar.' : 'Tente ajustar os termos de busca.' }}
          </p>
        </div>

        <!-- Table -->
        <div v-else style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;">
        <table style="width:100%;border-collapse:collapse;font-size:13px;">
          <thead>
            <tr style="border-bottom:1px solid #f1f5f9;">
              <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">ID</th>
              <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Nome</th>
              <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Descrição</th>
              <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Criado em</th>
              <th style="padding:11px 20px;width:120px;"></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="tenant in tenantsFiltrados"
              :key="tenant.id"
              style="border-bottom:1px solid #f8fafc;transition:background .1s;"
              @mouseenter="e => (e.currentTarget as HTMLElement).style.background='#f8fafc'"
              @mouseleave="e => (e.currentTarget as HTMLElement).style.background=''"
            >
              <td style="padding:13px 20px;color:#94a3b8;font-family:monospace;font-size:12px;">{{ tenant.id }}</td>
              <td style="padding:13px 20px;font-weight:500;color:#0f172a;">{{ tenant.nome }}</td>
              <td style="padding:13px 20px;color:#64748b;">{{ tenant.descricao || '—' }}</td>
              <td style="padding:13px 20px;color:#64748b;">{{ formatDate(tenant.created_at) }}</td>
              <td style="padding:13px 20px;">
                <div style="display:flex;align-items:center;justify-content:flex-end;gap:12px;">
                  <button
                    @click="openDrawer(tenant)"
                    style="font-size:12px;font-weight:600;color:#7c3aed;background:none;border:none;cursor:pointer;padding:0;"
                  >Gerenciar</button>
                  <button
                    @click="confirmDelete(tenant)"
                    style="font-size:12px;color:#94a3b8;background:none;border:none;cursor:pointer;padding:0;transition:color .15s;"
                    @mouseenter="e => (e.target as HTMLElement).style.color='#dc2626'"
                    @mouseleave="e => (e.target as HTMLElement).style.color='#94a3b8'"
                  >Remover</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      </template>
    </div>

    <!-- Create Tenant Modal -->
    <div v-if="showCreate" style="position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:50;padding:16px;" @click.self="showCreate=false;formError=''">
      <div style="background:white;border-radius:16px;width:100%;max-width:400px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.15);">
        <div style="padding:20px 24px;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:15px;font-weight:700;color:#0f172a;margin:0;">Novo Tenant</h3>
          <button @click="showCreate=false;formError=''" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:4px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px;"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <form @submit.prevent="createTenant" style="padding:20px 24px;display:flex;flex-direction:column;gap:14px;">
          <div>
            <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Nome</label>
            <input v-model="newTenant.nome" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;color:#0f172a;outline:none;box-sizing:border-box;" />
          </div>
          <div>
            <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Descrição <span style="color:#94a3b8;font-weight:400;">(opcional)</span></label>
            <input v-model="newTenant.descricao" style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;color:#0f172a;outline:none;box-sizing:border-box;" />
          </div>
          <p v-if="formError" style="font-size:12px;color:#dc2626;margin:0;">{{ formError }}</p>
          <div style="display:flex;gap:10px;padding-top:4px;">
            <button type="button" @click="showCreate=false;formError=''" style="flex:1;background:#f1f5f9;color:#334155;font-size:14px;font-weight:600;padding:11px;border-radius:10px;border:none;cursor:pointer;">Cancelar</button>
            <button type="submit" style="flex:1;background:#7c3aed;color:white;font-size:14px;font-weight:600;padding:11px;border-radius:10px;border:none;cursor:pointer;">Criar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Detail Drawer -->
    <Transition name="slide">
      <div v-if="drawerTenant" style="position:fixed;inset:0;z-index:40;display:flex;">
        <!-- Backdrop -->
        <div style="flex:1;background:rgba(0,0,0,.3);" @click="closeDrawer" />
        <!-- Panel -->
        <div style="width:480px;background:white;display:flex;flex-direction:column;overflow:hidden;box-shadow:-4px 0 32px rgba(0,0,0,.12);">

          <!-- Drawer Header -->
          <div style="padding:18px 24px;border-bottom:1px solid #e2e8f0;flex-shrink:0;display:flex;align-items:center;justify-content:space-between;">
            <div>
              <h2 style="font-size:15px;font-weight:700;color:#0f172a;margin:0;">{{ drawerTenant.nome }}</h2>
              <p style="font-size:12px;color:#94a3b8;margin:2px 0 0;">ID {{ drawerTenant.id }}</p>
            </div>
            <button @click="closeDrawer" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:4px;">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Drawer Content -->
          <div style="flex:1;overflow-y:auto;padding:20px 24px;display:flex;flex-direction:column;gap:24px;">

            <!-- Edit Tenant -->
            <section>
              <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 12px;">Informações</p>
              <form @submit.prevent="saveTenant" style="display:flex;flex-direction:column;gap:10px;">
                <div>
                  <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Nome</label>
                  <input v-model="editTenant.nome" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:9px 13px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" />
                </div>
                <div>
                  <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px;">Descrição</label>
                  <input v-model="editTenant.descricao" style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:9px 13px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" />
                </div>
                <div style="display:flex;align-items:center;gap:10px;">
                  <button type="submit" style="background:#7c3aed;color:white;font-size:12px;font-weight:600;padding:7px 14px;border-radius:8px;border:none;cursor:pointer;">Salvar</button>
                  <span v-if="saveMsg" style="font-size:12px;color:#059669;">{{ saveMsg }}</span>
                </div>
              </form>
            </section>

            <!-- Subscription -->
            <section>
              <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 12px;">Assinatura</p>

              <div v-if="drawerLoading" style="font-size:13px;color:#94a3b8;">Carregando...</div>

              <div v-else-if="drawerAssinatura" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:14px 16px;">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                  <div>
                    <p style="font-size:14px;font-weight:600;color:#0f172a;margin:0;">{{ drawerAssinatura.plano_nome ?? 'Plano #' + drawerAssinatura.plano_id }}</p>
                    <p v-if="drawerAssinatura.data_proxima_cobranca" style="font-size:12px;color:#64748b;margin:3px 0 0;">
                      Próx. cobrança: {{ formatDate(drawerAssinatura.data_proxima_cobranca) }}
                    </p>
                  </div>
                  <select
                    :value="drawerAssinatura.status"
                    @change="updateAssinaturaStatus(drawerAssinatura!.id, ($event.target as HTMLSelectElement).value)"
                    :style="assinaturaStatusStyle(drawerAssinatura.status)"
                    style="font-size:11px;font-weight:600;padding:4px 10px;border-radius:999px;border:none;cursor:pointer;outline:none;"
                  >
                    <option value="ATIVA">ATIVA</option>
                    <option value="SUSPENSA">SUSPENSA</option>
                    <option value="CANCELADA">CANCELADA</option>
                  </select>
                </div>
              </div>

              <div v-else style="display:flex;flex-direction:column;gap:10px;">
                <p style="font-size:13px;color:#64748b;">Sem assinatura. Criar manualmente:</p>
                <form @submit.prevent="criarAssinatura" style="display:flex;gap:8px;">
                  <select v-model="newAssinatura.plano_id" required style="flex:1;border:1.5px solid #e5e7eb;border-radius:9px;padding:8px 12px;font-size:13px;background:white;color:#0f172a;outline:none;">
                    <option value="" disabled>Selecionar plano</option>
                    <option v-for="p in planos" :key="p.id" :value="p.id">{{ p.nome }}</option>
                  </select>
                  <button type="submit" style="background:#7c3aed;color:white;font-size:12px;font-weight:600;padding:8px 14px;border-radius:9px;border:none;cursor:pointer;white-space:nowrap;">Criar</button>
                </form>
                <p v-if="assinaturaError" style="font-size:12px;color:#dc2626;margin:0;">{{ assinaturaError }}</p>
              </div>
            </section>

            <!-- Users -->
            <section>
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0;">
                  Usuários <span style="color:#cbd5e1;">({{ drawerUsuarios.length }})</span>
                </p>
                <button
                  @click="showAddUser = !showAddUser"
                  style="font-size:12px;font-weight:600;color:#7c3aed;background:none;border:none;cursor:pointer;padding:0;"
                >{{ showAddUser ? 'Cancelar' : '+ Adicionar' }}</button>
              </div>

              <!-- Add User Form -->
              <Transition name="fade">
                <form v-if="showAddUser" @submit.prevent="criarUsuario" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:14px 16px;margin-bottom:10px;display:flex;flex-direction:column;gap:10px;">
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    <div>
                      <label style="display:block;font-size:11px;font-weight:600;color:#374151;margin-bottom:4px;">Nome</label>
                      <input v-model="newUser.nome" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:7px 10px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" />
                    </div>
                    <div>
                      <label style="display:block;font-size:11px;font-weight:600;color:#374151;margin-bottom:4px;">Username</label>
                      <input v-model="newUser.username" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:7px 10px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" />
                    </div>
                  </div>
                  <div>
                    <label style="display:block;font-size:11px;font-weight:600;color:#374151;margin-bottom:4px;">Email</label>
                    <input v-model="newUser.email" type="email" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:7px 10px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" />
                  </div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
                    <div>
                      <label style="display:block;font-size:11px;font-weight:600;color:#374151;margin-bottom:4px;">Senha</label>
                      <input v-model="newUser.password" type="password" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:7px 10px;font-size:13px;color:#0f172a;outline:none;box-sizing:border-box;" />
                    </div>
                    <div>
                      <label style="display:block;font-size:11px;font-weight:600;color:#374151;margin-bottom:4px;">Role</label>
                      <select v-model="newUser.role" style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:7px 10px;font-size:13px;background:white;color:#0f172a;outline:none;box-sizing:border-box;">
                        <option value="MEMBER">MEMBER</option>
                        <option value="OWNER">OWNER</option>
                      </select>
                    </div>
                  </div>
                  <p v-if="userError" style="font-size:12px;color:#dc2626;margin:0;">{{ userError }}</p>
                  <button type="submit" style="width:100%;background:#7c3aed;color:white;font-size:13px;font-weight:600;padding:9px;border-radius:9px;border:none;cursor:pointer;">Adicionar Usuário</button>
                </form>
              </Transition>

              <!-- User List -->
              <div v-if="drawerLoading" style="font-size:13px;color:#94a3b8;">Carregando...</div>
              <div v-else-if="drawerUsuarios.length === 0" style="font-size:13px;color:#94a3b8;padding:8px 0;">Nenhum usuário cadastrado.</div>
              <div v-else style="display:flex;flex-direction:column;gap:6px;">
                <div
                  v-for="user in drawerUsuarios"
                  :key="user.id"
                  style="display:flex;align-items:center;gap:12px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:10px 14px;"
                >
                  <div style="width:32px;height:32px;border-radius:50%;background:#ede9fe;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                    <span style="font-size:12px;font-weight:700;color:#7c3aed;">{{ user.nome.charAt(0).toUpperCase() }}</span>
                  </div>
                  <div style="flex:1;min-width:0;">
                    <p style="font-size:13px;font-weight:500;color:#0f172a;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ user.nome }}</p>
                    <p style="font-size:11px;color:#64748b;margin:1px 0 0;">@{{ user.username }}</p>
                  </div>
                  <div style="display:flex;align-items:center;gap:6px;flex-shrink:0;">
                    <span :style="user.role === 'OWNER' ? 'background:#ede9fe;color:#7c3aed;' : 'background:#f1f5f9;color:#475569;'" style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;">{{ user.role }}</span>
                    <span v-if="!user.ativo" style="font-size:11px;color:#94a3b8;background:#f1f5f9;padding:2px 8px;border-radius:999px;">inativo</span>
                    <button @click="deletarUsuario(user)" style="background:none;border:none;cursor:pointer;padding:3px;color:#cbd5e1;display:flex;" title="Remover usuário">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </section>

          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import adminClient from '../../api/adminClient'

interface Tenant {
  id: number
  nome: string
  descricao: string | null
  created_at: string
}

interface Usuario {
  id: number
  nome: string
  username: string
  email: string
  role: string
  ativo: boolean
  tenant_id: number
}

interface Assinatura {
  id: number
  status: string
  plano_id: number
  plano_nome?: string
  tenant_id: number
  data_proxima_cobranca: string | null
}

interface Plano {
  id: number
  nome: string
}

const tenants = ref<Tenant[]>([])
const planos = ref<Plano[]>([])
const loading = ref(true)
const error = ref('')
const filtroNome = ref('')
const filtroDescricao = ref('')

const tenantsFiltrados = computed(() =>
  tenants.value.filter(
    (t) =>
      t.nome.toLowerCase().includes(filtroNome.value.toLowerCase()) &&
      (t.descricao || '').toLowerCase().includes(filtroDescricao.value.toLowerCase()),
  ),
)
const showCreate = ref(false)
const formError = ref('')
const newTenant = ref({ nome: '', descricao: '' })

// Drawer state
const drawerTenant = ref<Tenant | null>(null)
const drawerUsuarios = ref<Usuario[]>([])
const drawerAssinatura = ref<Assinatura | null>(null)
const drawerLoading = ref(false)
const editTenant = ref({ nome: '', descricao: '' })
const saveMsg = ref('')

// Add user form
const showAddUser = ref(false)
const newUser = ref({ nome: '', username: '', email: '', password: '', role: 'MEMBER' })
const userError = ref('')

// Subscription form
const newAssinatura = ref({ plano_id: '' as number | '' })
const assinaturaError = ref('')

async function load() {
  try {
    const [tenantsRes, planosRes] = await Promise.all([
      adminClient.get('/tenants'),
      adminClient.get('/planos'),
    ])
    tenants.value = tenantsRes.data
    planos.value = planosRes.data
  } catch {
    error.value = 'Erro ao carregar dados.'
  } finally {
    loading.value = false
  }
}

async function createTenant() {
  formError.value = ''
  try {
    const res = await adminClient.post('/tenants', newTenant.value)
    tenants.value.unshift(res.data)
    showCreate.value = false
    newTenant.value = { nome: '', descricao: '' }
  } catch (err: any) {
    formError.value = err.response?.data?.detail || 'Erro ao criar tenant.'
  }
}

async function confirmDelete(tenant: Tenant) {
  if (!confirm(`Remover tenant "${tenant.nome}"? Esta ação é irreversível.`)) return
  try {
    await adminClient.delete(`/tenants/${tenant.id}`)
    tenants.value = tenants.value.filter((t) => t.id !== tenant.id)
    if (drawerTenant.value?.id === tenant.id) closeDrawer()
  } catch {
    alert('Erro ao remover tenant.')
  }
}

async function openDrawer(tenant: Tenant) {
  drawerTenant.value = tenant
  editTenant.value = { nome: tenant.nome, descricao: tenant.descricao || '' }
  drawerLoading.value = true
  showAddUser.value = false
  userError.value = ''
  assinaturaError.value = ''
  saveMsg.value = ''
  try {
    const [usersRes, assRes] = await Promise.all([
      adminClient.get(`/tenants/${tenant.id}/usuarios`),
      adminClient.get(`/tenants/${tenant.id}/assinatura`),
    ])
    drawerUsuarios.value = usersRes.data
    drawerAssinatura.value = assRes.data
  } finally {
    drawerLoading.value = false
  }
}

function closeDrawer() {
  drawerTenant.value = null
  drawerUsuarios.value = []
  drawerAssinatura.value = null
}

async function saveTenant() {
  if (!drawerTenant.value) return
  try {
    const res = await adminClient.put(`/tenants/${drawerTenant.value.id}`, editTenant.value)
    Object.assign(drawerTenant.value, res.data)
    const idx = tenants.value.findIndex((t) => t.id === drawerTenant.value!.id)
    if (idx !== -1) tenants.value[idx] = res.data
    saveMsg.value = 'Salvo!'
    setTimeout(() => (saveMsg.value = ''), 2000)
  } catch {
    alert('Erro ao salvar tenant.')
  }
}

async function criarUsuario() {
  if (!drawerTenant.value) return
  userError.value = ''
  try {
    const res = await adminClient.post(`/tenants/${drawerTenant.value.id}/usuarios`, newUser.value)
    drawerUsuarios.value.push(res.data)
    newUser.value = { nome: '', username: '', email: '', password: '', role: 'MEMBER' }
    showAddUser.value = false
  } catch (err: any) {
    userError.value = err.response?.data?.detail || 'Erro ao criar usuário.'
  }
}

async function deletarUsuario(user: Usuario) {
  if (!confirm(`Remover usuário "${user.nome}"?`)) return
  try {
    await adminClient.delete(`/usuarios/${user.id}`)
    drawerUsuarios.value = drawerUsuarios.value.filter((u) => u.id !== user.id)
  } catch {
    alert('Erro ao remover usuário.')
  }
}

async function criarAssinatura() {
  if (!drawerTenant.value || !newAssinatura.value.plano_id) return
  assinaturaError.value = ''
  try {
    const res = await adminClient.post(`/tenants/${drawerTenant.value.id}/assinatura`, {
      plano_id: newAssinatura.value.plano_id,
      status: 'ATIVA',
    })
    const plano = planos.value.find((p) => p.id === res.data.plano_id)
    drawerAssinatura.value = { ...res.data, plano_nome: plano?.nome }
    newAssinatura.value = { plano_id: '' }
  } catch (err: any) {
    assinaturaError.value = err.response?.data?.detail || 'Erro ao criar assinatura.'
  }
}

async function updateAssinaturaStatus(id: number, novoStatus: string) {
  try {
    const res = await adminClient.put(`/assinaturas/${id}`, { status: novoStatus })
    if (drawerAssinatura.value) {
      drawerAssinatura.value.status = res.data.status
    }
  } catch {
    alert('Erro ao atualizar status.')
  }
}

function assinaturaStatusStyle(status: string) {
  return {
    ATIVA: 'background:#d1fae5;color:#065f46;',
    SUSPENSA: 'background:#fef3c7;color:#92400e;',
    CANCELADA: 'background:#fee2e2;color:#991b1b;',
  }[status] ?? 'background:#f1f5f9;color:#475569;'
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('pt-BR')
}

onMounted(load)
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-enter-active { transition: transform 0.25s ease, opacity 0.25s ease; }
.slide-leave-active { transition: transform 0.2s ease, opacity 0.2s ease; }
.slide-enter-from { transform: translateX(100%); opacity: 0; }
.slide-leave-to { transform: translateX(100%); opacity: 0; }

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
