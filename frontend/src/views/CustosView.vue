<template>
  <div style="display:flex;flex-direction:column;height:100%;position:relative;">

    <!-- Header -->
    <div style="height:64px;border-bottom:1px solid #e2e8f0;background:white;display:flex;align-items:center;justify-content:space-between;padding:0 24px;flex-shrink:0;">
      <div>
        <h1 style="font-size:15px;font-weight:600;color:#0f172a;margin:0;">Custos</h1>
        <p style="font-size:12px;color:#64748b;margin:0;">Despesas do grupo</p>
      </div>
      <div style="display:flex;align-items:center;gap:10px;">
        <select
          v-model="mesSelecionadoId"
          @change="carregarCustos"
          style="border:1px solid #e2e8f0;border-radius:8px;padding:7px 12px;font-size:13px;color:#334155;background:white;cursor:pointer;outline:none;"
        >
          <option v-for="m in meses" :key="m.id" :value="m.id">
            {{ nomeMes(m.mes) }}/{{ m.ano }}
            <template v-if="m.status === 'ABERTO'"> · Aberto</template>
          </option>
        </select>
        <button
          v-if="authStore.can('custo:create')"
          @click="abrirCreate"
          style="display:flex;align-items:center;gap:6px;background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:8px 14px;border-radius:9px;border:none;cursor:pointer;"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" style="width:14px;height:14px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          Novo custo
        </button>
      </div>
    </div>

    <!-- Content -->
    <div style="flex:1;overflow:auto;padding:24px;">

      <!-- Loading -->
      <div v-if="loading" style="display:flex;align-items:center;justify-content:center;height:200px;">
        <svg class="animate-spin" style="width:22px;height:22px;color:#4f46e5;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle style="opacity:.25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
          <path style="opacity:.75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
        </svg>
      </div>

      <template v-else>
        <!-- Summary bar -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Total</p>
            <p style="font-size:20px;font-weight:700;color:#0f172a;margin:0;font-variant-numeric:tabular-nums;">{{ fmt(totalGeral) }}</p>
          </div>
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Pagos</p>
            <p style="font-size:20px;font-weight:700;color:#059669;margin:0;font-variant-numeric:tabular-nums;">{{ fmt(totalPago) }}</p>
          </div>
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Parciais</p>
            <p style="font-size:20px;font-weight:700;color:#ea580c;margin:0;font-variant-numeric:tabular-nums;">{{ fmt(totalParcial) }}</p>
          </div>
          <div style="background:white;border:1px solid #e2e8f0;border-radius:12px;padding:16px 20px;">
            <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 4px;">Pendentes</p>
            <p style="font-size:20px;font-weight:700;color:#d97706;margin:0;font-variant-numeric:tabular-nums;">{{ fmt(totalPendente) }}</p>
          </div>
        </div>

        <!-- Empty state -->
        <div v-if="custos.length === 0" style="background:white;border:1px solid #e2e8f0;border-radius:14px;padding:56px 32px;text-align:center;">
          <div style="width:48px;height:48px;background:#f1f5f9;border-radius:12px;display:flex;align-items:center;justify-content:center;margin:0 auto 12px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="#94a3b8" style="width:24px;height:24px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75" />
            </svg>
          </div>
          <p style="font-size:14px;font-weight:600;color:#334155;margin:0 0 4px;">Nenhum custo neste mês</p>
          <p style="font-size:13px;color:#94a3b8;margin:0;">Crie o primeiro custo ou importe os custos fixos.</p>
        </div>

        <!-- Table -->
        <div v-else style="background:white;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;">
          <table style="width:100%;border-collapse:collapse;font-size:13px;">
            <thead>
              <tr style="border-bottom:1px solid #f1f5f9;">
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Descrição</th>
                <th style="text-align:right;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Valor</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Vencimento</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Tipo</th>
                <th style="text-align:left;padding:11px 20px;font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;">Status</th>
                <th style="padding:11px 20px;width:140px;"></th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="c in custos"
                :key="c.id"
                style="border-bottom:1px solid #f8fafc;transition:background .1s;"
                @mouseenter="e => (e.currentTarget as HTMLElement).style.background='#f8fafc'"
                @mouseleave="e => (e.currentTarget as HTMLElement).style.background=''"
              >
                <td style="padding:13px 20px;font-weight:500;color:#0f172a;">{{ c.descricao }}</td>
                <td style="padding:13px 20px;text-align:right;font-weight:600;color:#0f172a;font-variant-numeric:tabular-nums;font-family:monospace;">{{ fmt(c.valor) }}</td>
                <td style="padding:13px 20px;color:#475569;">{{ fmtData(c.data_vencimento) }}</td>
                <td style="padding:13px 20px;">
                  <span :style="c.tipo === 'FIXO'
                    ? 'background:#f1f5f9;color:#475569;'
                    : 'background:#ede9fe;color:#6d28d9;'"
                    style="padding:3px 9px;border-radius:6px;font-size:11px;font-weight:600;">
                    {{ c.tipo === 'FIXO' ? 'Fixo' : 'Variável' }}
                  </span>
                </td>
                <td style="padding:13px 20px;">
                  <span :style="statusStyle(c.status)"
                    style="display:inline-flex;align-items:center;gap:5px;padding:3px 9px;border-radius:999px;font-size:11px;font-weight:600;">
                    <span :style="statusDotStyle(c.status)" style="width:5px;height:5px;border-radius:50%;display:inline-block;"></span>
                    {{ statusLabel(c.status) }}
                  </span>
                </td>
                <td style="padding:13px 20px;">
                  <div style="display:flex;align-items:center;justify-content:flex-end;gap:4px;">
                    <!-- Rateios -->
                    <button
                      @click="abrirDrawer(c)"
                      title="Gerenciar rateios"
                      style="display:flex;align-items:center;gap:4px;background:#f1f5f9;color:#475569;font-size:11px;font-weight:600;padding:4px 9px;border-radius:6px;border:none;cursor:pointer;"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:13px;height:13px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M18 18.72a9.094 9.094 0 003.741-.479 3 3 0 00-4.682-2.72m.94 3.198l.001.031c0 .225-.012.447-.037.666A11.944 11.944 0 0112 21c-2.17 0-4.207-.576-5.963-1.584A6.062 6.062 0 016 18.719m12 0a5.971 5.971 0 00-.941-3.197m0 0A5.995 5.995 0 0012 12.75a5.995 5.995 0 00-5.058 2.772m0 0a3 3 0 00-4.681 2.72 8.986 8.986 0 003.74.477m.94-3.197a5.971 5.971 0 00-.94 3.197M15 6.75a3 3 0 11-6 0 3 3 0 016 0zm6 3a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0zm-13.5 0a2.25 2.25 0 11-4.5 0 2.25 2.25 0 014.5 0z" />
                      </svg>
                      Rateios
                    </button>
                    <!-- Editar -->
                    <button
                      v-if="authStore.can('custo:update')"
                      @click="abrirEdit(c)"
                      title="Editar"
                      style="background:none;border:none;cursor:pointer;padding:5px;border-radius:6px;color:#94a3b8;display:flex;"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" />
                      </svg>
                    </button>
                    <!-- Deletar -->
                    <button
                      v-if="authStore.can('custo:delete')"
                      @click="deletar(c)"
                      title="Remover"
                      style="background:none;border:none;cursor:pointer;padding:5px;border-radius:6px;color:#94a3b8;display:flex;"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                      </svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>

    <!-- Modal Create/Edit -->
    <div v-if="showModal" style="position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:center;justify-content:center;z-index:50;padding:16px;" @click.self="showModal=false">
      <div style="background:white;border-radius:16px;width:100%;max-width:420px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.15);">
        <div style="padding:20px 24px;border-bottom:1px solid #f1f5f9;display:flex;justify-content:space-between;align-items:center;">
          <h3 style="font-size:15px;font-weight:700;color:#0f172a;margin:0;">{{ editando ? 'Editar custo' : 'Novo custo' }}</h3>
          <button @click="showModal=false" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:4px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px;"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <form @submit.prevent="salvar" style="padding:20px 24px;display:flex;flex-direction:column;gap:14px;">
          <div>
            <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Descrição</label>
            <input v-model="form.descricao" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Valor (R$)</label>
              <input v-model="form.valor" type="number" step="0.01" min="0" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
            </div>
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Vencimento</label>
              <input v-model="form.data_vencimento" type="date" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;outline:none;box-sizing:border-box;" />
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div>
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Tipo</label>
              <select v-model="form.tipo" style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;background:white;outline:none;box-sizing:border-box;">
                <option value="VARIAVEL">Variável</option>
                <option value="FIXO">Fixo</option>
              </select>
            </div>
            <div v-if="editando">
              <label style="display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:6px;">Status</label>
              <select v-model="form.status" style="width:100%;border:1.5px solid #e5e7eb;border-radius:9px;padding:10px 13px;font-size:14px;background:white;outline:none;box-sizing:border-box;">
                <option value="PENDENTE">Pendente</option>
                <option value="PARCIALMENTE_PAGO">Parcialmente Pago</option>
                <option value="PAGO">Pago</option>
              </select>
            </div>
          </div>
          <p v-if="formError" style="font-size:12px;color:#dc2626;margin:0;">{{ formError }}</p>
          <div style="display:flex;gap:10px;padding-top:4px;">
            <button type="button" @click="showModal=false" style="flex:1;background:#f1f5f9;color:#334155;font-size:14px;font-weight:600;padding:11px;border-radius:10px;border:none;cursor:pointer;">Cancelar</button>
            <button type="submit" :disabled="salvando" style="flex:1;background:#4f46e5;color:white;font-size:14px;font-weight:600;padding:11px;border-radius:10px;border:none;cursor:pointer;">
              {{ salvando ? 'Salvando...' : 'Salvar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Drawer overlay -->
    <div
      v-if="drawerCusto"
      style="position:fixed;inset:0;z-index:40;"
      @click.self="fecharDrawer"
    >
      <div style="position:absolute;inset:0;background:rgba(0,0,0,.3);" @click="fecharDrawer"></div>

      <!-- Drawer panel -->
      <div style="position:absolute;top:0;right:0;bottom:0;width:400px;background:white;display:flex;flex-direction:column;box-shadow:-4px 0 24px rgba(0,0,0,.12);">

        <!-- Drawer header -->
        <div style="padding:18px 20px;border-bottom:1px solid #e2e8f0;flex-shrink:0;">
          <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">
            <div style="min-width:0;">
              <p style="font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;letter-spacing:.06em;margin:0 0 2px;">Rateios</p>
              <h3 style="font-size:14px;font-weight:700;color:#0f172a;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ drawerCusto.descricao }}</h3>
              <p style="font-size:13px;font-weight:600;color:#4f46e5;margin:2px 0 0;">{{ fmt(drawerCusto.valor) }}</p>
            </div>
            <button @click="fecharDrawer" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:4px;flex-shrink:0;">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:18px;height:18px;"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>

          <!-- Percentage progress bar -->
          <div style="margin-top:12px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;">
              <span style="font-size:11px;color:#64748b;">Alocado</span>
              <span style="font-size:11px;font-weight:600;" :style="somaPercDrawer > 100 ? 'color:#dc2626' : somaPercDrawer === 100 ? 'color:#059669' : 'color:#d97706'">
                {{ somaPercDrawer.toFixed(1) }}%
              </span>
            </div>
            <div style="height:6px;background:#f1f5f9;border-radius:999px;overflow:hidden;">
              <div
                :style="{ width: Math.min(somaPercDrawer, 100) + '%', background: somaPercDrawer >= 100 ? '#059669' : '#f59e0b' }"
                style="height:100%;border-radius:999px;transition:width .3s;"
              ></div>
            </div>
            <p v-if="somaPercDrawer < 100 && somaPercDrawer > 0" style="font-size:11px;color:#d97706;margin:4px 0 0;">
              Faltam {{ (100 - somaPercDrawer).toFixed(1) }}% para alocar
            </p>
            <p v-if="somaPercDrawer === 0" style="font-size:11px;color:#94a3b8;margin:4px 0 0;">
              Nenhum rateio alocado ainda
            </p>
          </div>
        </div>

        <!-- Drawer rateios list -->
        <div style="flex:1;overflow-y:auto;padding:12px 0;">
          <div v-if="drawerLoadingRateios" style="display:flex;justify-content:center;padding:24px;">
            <svg style="width:18px;height:18px;color:#94a3b8;animation:spin 1s linear infinite;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle style="opacity:.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
              <path style="opacity:.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
          </div>
          <div v-else-if="drawerRateios.length === 0" style="text-align:center;padding:32px 20px;color:#94a3b8;font-size:13px;">
            Nenhum rateio criado ainda.
          </div>
          <div v-else>
            <div
              v-for="r in drawerRateios"
              :key="r.id"
              style="padding:10px 20px;border-bottom:1px solid #f1f5f9;display:flex;align-items:center;gap:10px;"
            >
              <!-- Avatar -->
              <div style="width:32px;height:32px;background:#e0e7ff;border-radius:50%;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
                <span style="font-size:12px;font-weight:700;color:#4338ca;">{{ usuarioInicial(r.usuario_id) }}</span>
              </div>
              <!-- Info -->
              <div style="flex:1;min-width:0;">
                <p style="font-size:13px;font-weight:500;color:#0f172a;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{{ usuarioNome(r.usuario_id) }}</p>
                <p style="font-size:11px;color:#64748b;margin:1px 0 0;">{{ parseFloat(r.porcentagem).toFixed(1) }}% · {{ fmt(r.valor_calculado) }}</p>
              </div>
              <!-- Status chip -->
              <span
                style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:999px;white-space:nowrap;flex-shrink:0;"
                :style="r.status === 'PAGO' ? 'background:#d1fae5;color:#065f46;' : 'background:#fef3c7;color:#92400e;'"
              >{{ r.status === 'PAGO' ? 'Pago' : 'Pendente' }}</span>
              <!-- Actions -->
              <div style="display:flex;gap:2px;flex-shrink:0;">
                <!-- Marcar pago -->
                <button
                  v-if="r.status === 'PENDENTE' && authStore.can('rateio:pay')"
                  @click="marcarRateioPago(r)"
                  title="Marcar como pago"
                  style="background:none;border:none;cursor:pointer;padding:4px;color:#059669;display:flex;border-radius:5px;"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </button>
                <!-- Upload comprovante -->
                <label v-if="authStore.can('comprovante:upload')" :title="r.comprovante_url ? 'Substituir comprovante' : 'Upload comprovante'" style="cursor:pointer;padding:4px;color:#6366f1;display:flex;border-radius:5px;">
                  <input type="file" style="display:none;" @change="e => onUploadComprovante(r, e)" accept="image/*,application/pdf" />
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
                  </svg>
                </label>
                <!-- Ver comprovante -->
                <button
                  v-if="r.comprovante_url"
                  @click="verComprovante(r.comprovante_url!)"
                  title="Ver comprovante"
                  style="background:none;border:none;cursor:pointer;padding:4px;color:#0ea5e9;display:flex;border-radius:5px;"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
                <!-- Remover -->
                <button
                  v-if="authStore.can('rateio:delete')"
                  @click="removerRateio(r)"
                  title="Remover rateio"
                  style="background:none;border:none;cursor:pointer;padding:4px;color:#94a3b8;display:flex;border-radius:5px;"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:15px;height:15px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Add rateio form -->
        <div v-if="authStore.can('rateio:create')" style="border-top:1px solid #e2e8f0;padding:16px 20px;flex-shrink:0;background:#fafafa;">
          <p style="font-size:11px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.06em;margin:0 0 10px;">Adicionar rateio</p>
          <form @submit.prevent="criarRateio" style="display:flex;gap:8px;align-items:flex-end;">
            <div style="flex:1;">
              <label style="font-size:11px;color:#64748b;display:block;margin-bottom:4px;">Membro</label>
              <select v-model="novoRateio.usuario_id" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 10px;font-size:13px;background:white;outline:none;">
                <option :value="0" disabled>Selecionar...</option>
                <option v-for="u in membrosDisponiveis" :key="u.id" :value="u.id">{{ u.nome }}</option>
              </select>
            </div>
            <div style="width:80px;">
              <label style="font-size:11px;color:#64748b;display:block;margin-bottom:4px;">% Porc.</label>
              <input v-model="novoRateio.porcentagem" type="number" step="0.01" min="0.01" max="100" required style="width:100%;border:1.5px solid #e5e7eb;border-radius:8px;padding:8px 10px;font-size:13px;outline:none;box-sizing:border-box;" placeholder="%" />
            </div>
            <button type="submit" :disabled="criandoRateio" style="background:#4f46e5;color:white;font-size:13px;font-weight:600;padding:8px 14px;border-radius:8px;border:none;cursor:pointer;white-space:nowrap;">
              {{ criandoRateio ? '...' : 'Adicionar' }}
            </button>
          </form>
          <p v-if="drawerError" style="font-size:11px;color:#dc2626;margin:6px 0 0;">{{ drawerError }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type Custo, type MesReferencia, type PagamentoRateio, type Usuario } from '../api/client'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const meses = ref<MesReferencia[]>([])
const mesSelecionadoId = ref<number | null>(null)
const custos = ref<Custo[]>([])
const usuarios = ref<Usuario[]>([])
const loading = ref(true)
const showModal = ref(false)
const editando = ref<Custo | null>(null)
const salvando = ref(false)
const formError = ref('')

const form = ref({
  descricao: '',
  valor: '',
  data_vencimento: '',
  tipo: 'VARIAVEL' as 'FIXO' | 'VARIAVEL',
  status: 'PENDENTE' as 'PENDENTE' | 'PARCIALMENTE_PAGO' | 'PAGO',
})

// Drawer state
const drawerCusto = ref<Custo | null>(null)
const drawerRateios = ref<PagamentoRateio[]>([])
const drawerLoadingRateios = ref(false)
const drawerError = ref('')
const criandoRateio = ref(false)
const novoRateio = ref({ usuario_id: 0, porcentagem: '' })

const totalGeral = computed(() => custos.value.reduce((s, c) => s + parseFloat(c.valor), 0))
const totalPago = computed(() => custos.value.filter(c => c.status === 'PAGO').reduce((s, c) => s + parseFloat(c.valor), 0))
const totalParcial = computed(() => custos.value.filter(c => c.status === 'PARCIALMENTE_PAGO').reduce((s, c) => s + parseFloat(c.valor), 0))
const totalPendente = computed(() => custos.value.filter(c => c.status === 'PENDENTE').reduce((s, c) => s + parseFloat(c.valor), 0))

const somaPercDrawer = computed(() =>
  drawerRateios.value.reduce((s, r) => s + parseFloat(r.porcentagem), 0)
)

const usuariosMap = computed(() => {
  const m: Record<number, Usuario> = {}
  usuarios.value.forEach(u => (m[u.id] = u))
  return m
})

const membrosDisponiveis = computed(() => {
  if (!drawerRateios.value.length) return usuarios.value
  const usados = new Set(drawerRateios.value.map(r => r.usuario_id))
  return usuarios.value.filter(u => !usados.has(u.id))
})

function usuarioNome(userId: number) {
  return usuariosMap.value[userId]?.nome ?? `#${userId}`
}
function usuarioInicial(userId: number) {
  const nome = usuariosMap.value[userId]?.nome
  return nome ? nome.charAt(0).toUpperCase() : '?'
}

function statusStyle(status: string) {
  if (status === 'PAGO') return 'background:#d1fae5;color:#065f46;'
  if (status === 'PARCIALMENTE_PAGO') return 'background:#ffedd5;color:#9a3412;'
  return 'background:#fef3c7;color:#92400e;'
}
function statusDotStyle(status: string) {
  if (status === 'PAGO') return 'background:#10b981'
  if (status === 'PARCIALMENTE_PAGO') return 'background:#f97316'
  return 'background:#f59e0b'
}
function statusLabel(status: string) {
  if (status === 'PAGO') return 'Pago'
  if (status === 'PARCIALMENTE_PAGO') return 'Parcial'
  return 'Pendente'
}

function fmt(v: string | number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(typeof v === 'string' ? parseFloat(v) : v)
}
function fmtData(d: string) {
  return new Date(d + 'T00:00:00').toLocaleDateString('pt-BR')
}
const MESES_NOME = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
function nomeMes(m: number) { return MESES_NOME[m - 1] }

async function carregarCustos() {
  loading.value = true
  try {
    const r = await api.getCustos(mesSelecionadoId.value ?? undefined)
    custos.value = r.data
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (!authStore.tenantId) return
  const [mesesRes, usuariosRes] = await Promise.all([
    api.getMeses(),
    api.getUsuarios(),
  ])
  meses.value = mesesRes.data.sort((a, b) => b.ano !== a.ano ? b.ano - a.ano : b.mes - a.mes)
  usuarios.value = usuariosRes.data
  if (meses.value.length) {
    mesSelecionadoId.value = meses.value[0].id
  }
  await carregarCustos()
})

function abrirCreate() {
  editando.value = null
  form.value = { descricao: '', valor: '', data_vencimento: '', tipo: 'VARIAVEL', status: 'PENDENTE' }
  formError.value = ''
  showModal.value = true
}

function abrirEdit(c: Custo) {
  editando.value = c
  form.value = { descricao: c.descricao, valor: c.valor, data_vencimento: c.data_vencimento, tipo: c.tipo, status: c.status }
  formError.value = ''
  showModal.value = true
}

async function salvar() {
  salvando.value = true
  formError.value = ''
  try {
    if (editando.value) {
      const r = await api.updateCusto(editando.value.id, form.value)
      const idx = custos.value.findIndex(c => c.id === editando.value!.id)
      if (idx !== -1) custos.value[idx] = r.data
    } else {
      if (!mesSelecionadoId.value) return
      const r = await api.createCusto({ ...form.value, mes_referencia_id: mesSelecionadoId.value })
      custos.value.unshift(r.data)
    }
    showModal.value = false
  } catch (e: any) {
    formError.value = e.response?.data?.detail || 'Erro ao salvar'
  } finally {
    salvando.value = false
  }
}

async function deletar(c: Custo) {
  if (!confirm(`Remover "${c.descricao}"?`)) return
  await api.deleteCusto(c.id)
  custos.value = custos.value.filter(x => x.id !== c.id)
}

// Drawer actions
async function abrirDrawer(c: Custo) {
  drawerCusto.value = c
  drawerRateios.value = []
  drawerError.value = ''
  novoRateio.value = { usuario_id: 0, porcentagem: '' }
  drawerLoadingRateios.value = true
  try {
    const r = await api.getRateios({ custo_id: c.id })
    drawerRateios.value = r.data
  } finally {
    drawerLoadingRateios.value = false
  }
}

function fecharDrawer() {
  drawerCusto.value = null
  drawerRateios.value = []
}

async function criarRateio() {
  if (!drawerCusto.value || !novoRateio.value.usuario_id) return
  criandoRateio.value = true
  drawerError.value = ''
  try {
    const r = await api.createRateio({
      porcentagem: novoRateio.value.porcentagem,
      custo_id: drawerCusto.value.id,
      usuario_id: novoRateio.value.usuario_id,
    })
    drawerRateios.value.push(r.data)
    novoRateio.value = { usuario_id: 0, porcentagem: '' }
    await sincronizarStatusCusto()
  } catch (e: any) {
    drawerError.value = e.response?.data?.detail || 'Erro ao criar rateio'
  } finally {
    criandoRateio.value = false
  }
}

async function marcarRateioPago(r: PagamentoRateio) {
  const res = await api.updateRateio(r.id, { status: 'PAGO' })
  const idx = drawerRateios.value.findIndex(x => x.id === r.id)
  if (idx !== -1) drawerRateios.value[idx] = res.data
  await sincronizarStatusCusto()
}

async function removerRateio(r: PagamentoRateio) {
  if (!confirm('Remover este rateio?')) return
  await api.deleteRateio(r.id)
  drawerRateios.value = drawerRateios.value.filter(x => x.id !== r.id)
  await sincronizarStatusCusto()
}

async function onUploadComprovante(r: PagamentoRateio, event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const res = await api.uploadComprovante(r.id, file)
    const idx = drawerRateios.value.findIndex(x => x.id === r.id)
    if (idx !== -1) drawerRateios.value[idx] = res.data
  } catch (e: any) {
    alert(e.response?.data?.detail || 'Erro ao enviar comprovante')
  } finally {
    input.value = ''
  }
}

function verComprovante(url: string) {
  window.open(url, '_blank')
}

async function sincronizarStatusCusto() {
  if (!drawerCusto.value) return
  try {
    const r = await api.getCustos(mesSelecionadoId.value ?? undefined)
    custos.value = r.data
    const updated = r.data.find(c => c.id === drawerCusto.value!.id)
    if (updated) drawerCusto.value = updated
  } catch { /* silently ignore */ }
}
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
