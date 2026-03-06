<template>
  <div class="min-h-screen bg-white">

    <!-- Nav -->
    <header class="sticky top-0 z-40 bg-white/90 backdrop-blur-md border-b border-slate-100">
      <div style="max-width:1100px;margin:0 auto;padding:0 24px;height:64px;display:flex;align-items:center;justify-content:space-between;">
        <div style="display:flex;align-items:center;gap:10px;">
          <div style="width:32px;height:32px;background:#4f46e5;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="white" style="width:16px;height:16px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33" />
            </svg>
          </div>
          <span style="font-weight:600;color:#0f172a;font-size:14px;">Gestor de Custos</span>
        </div>
        <a href="/login" style="font-size:14px;font-weight:500;color:#475569;text-decoration:none;display:flex;align-items:center;gap:6px;" class="hover:text-indigo-600 transition-colors">
          Entrar
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:14px;height:14px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </a>
      </div>
    </header>

    <!-- Hero -->
    <section style="background:#0c0a1e;padding:96px 24px 80px;">
      <div style="max-width:760px;margin:0 auto;text-align:center;">

        <div style="display:inline-flex;align-items:center;gap:8px;background:rgba(99,102,241,0.12);border:1px solid rgba(99,102,241,0.25);border-radius:999px;padding:6px 16px;margin-bottom:32px;">
          <span style="width:6px;height:6px;background:#818cf8;border-radius:50%;display:inline-block;"></span>
          <span style="color:#a5b4fc;font-size:12px;font-weight:500;">Simples, justo e transparente</span>
        </div>

        <h1 style="font-size:clamp(36px,5vw,60px);font-weight:800;color:white;line-height:1.1;letter-spacing:-0.02em;margin-bottom:24px;">
          Fim das brigas por<br>
          <span style="background:linear-gradient(135deg,#818cf8,#c084fc);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">conta de casa</span>
        </h1>

        <p style="font-size:17px;color:#94a3b8;line-height:1.7;margin-bottom:40px;max-width:520px;margin-left:auto;margin-right:auto;">
          Gerencie as despesas do seu grupo com clareza. Cada um sabe quanto deve, quando pagar e como dividir — sem planilha, sem confusão.
        </p>

        <div style="display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;">
          <a href="#planos" style="display:inline-flex;align-items:center;gap:8px;background:#4f46e5;color:white;font-weight:600;font-size:14px;padding:14px 28px;border-radius:12px;text-decoration:none;box-shadow:0 4px 24px rgba(79,70,229,0.4);" class="hover:bg-indigo-500 transition-colors">
            Começar agora
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:16px;height:16px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </a>
          <a href="/login" style="color:#64748b;font-size:14px;font-weight:500;text-decoration:none;" class="hover:text-white transition-colors">
            Já tenho conta →
          </a>
        </div>

        <!-- Stats -->
        <div style="display:grid;grid-template-columns:repeat(3,1fr);margin-top:64px;border:1px solid rgba(255,255,255,0.06);border-radius:16px;overflow:hidden;">
          <div style="background:rgba(255,255,255,0.03);padding:20px;text-align:center;border-right:1px solid rgba(255,255,255,0.06);">
            <p style="font-size:28px;font-weight:700;color:white;margin:0;">100%</p>
            <p style="font-size:12px;color:#64748b;margin:4px 0 0;">Transparente</p>
          </div>
          <div style="background:rgba(255,255,255,0.03);padding:20px;text-align:center;border-right:1px solid rgba(255,255,255,0.06);">
            <p style="font-size:28px;font-weight:700;color:white;margin:0;">0</p>
            <p style="font-size:12px;color:#64748b;margin:4px 0 0;">Planilhas</p>
          </div>
          <div style="background:rgba(255,255,255,0.03);padding:20px;text-align:center;">
            <p style="font-size:28px;font-weight:700;color:white;margin:0;">∞</p>
            <p style="font-size:12px;color:#64748b;margin:4px 0 0;">Discussões evitadas</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section style="padding:96px 24px;background:white;">
      <div style="max-width:1100px;margin:0 auto;">
        <div style="text-align:center;margin-bottom:56px;">
          <p style="font-size:11px;font-weight:700;color:#4f46e5;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:12px;">Funcionalidades</p>
          <h2 style="font-size:32px;font-weight:700;color:#0f172a;margin:0;">Tudo que você precisa para dividir bem</h2>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;">
          <div
            v-for="feat in features"
            :key="feat.title"
            style="background:white;border:1px solid #e2e8f0;border-radius:16px;padding:28px;transition:box-shadow 0.2s,border-color 0.2s;"
            class="hover:shadow-lg hover:border-indigo-200"
          >
            <div style="width:48px;height:48px;background:#eef2ff;border-radius:12px;display:flex;align-items:center;justify-content:center;margin-bottom:16px;font-size:24px;">
              {{ feat.emoji }}
            </div>
            <h3 style="font-size:15px;font-weight:600;color:#0f172a;margin:0 0 8px;">{{ feat.title }}</h3>
            <p style="font-size:14px;color:#64748b;line-height:1.6;margin:0;">{{ feat.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Planos -->
    <section id="planos" style="padding:96px 24px;background:#f8fafc;">
      <div style="max-width:1100px;margin:0 auto;">
        <div style="text-align:center;margin-bottom:56px;">
          <p style="font-size:11px;font-weight:700;color:#4f46e5;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:12px;">Preços</p>
          <h2 style="font-size:32px;font-weight:700;color:#0f172a;margin:0 0 8px;">Planos simples, sem pegadinhas</h2>
          <p style="font-size:14px;color:#64748b;margin:0;">Cancele quando quiser. Sem fidelidade.</p>
        </div>

        <div v-if="loading" style="display:flex;justify-content:center;padding:64px 0;">
          <svg class="animate-spin" style="width:24px;height:24px;color:#4f46e5;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle style="opacity:0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
            <path style="opacity:0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
          </svg>
        </div>

        <div v-else-if="planos.length === 0" style="max-width:360px;margin:0 auto;text-align:center;background:white;border:1px solid #e2e8f0;border-radius:20px;padding:56px 32px;">
          <div style="width:52px;height:52px;background:#f1f5f9;border-radius:14px;display:flex;align-items:center;justify-content:center;margin:0 auto 16px;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="#94a3b8" style="width:26px;height:26px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" />
            </svg>
          </div>
          <p style="font-weight:600;color:#334155;font-size:15px;margin:0 0 6px;">Em breve</p>
          <p style="font-size:13px;color:#94a3b8;margin:0;">Entre em contato para mais informações.</p>
        </div>

        <div v-else style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px;align-items:start;">
          <div
            v-for="(plano, idx) in planos"
            :key="plano.id"
            style="background:white;border-radius:20px;overflow:hidden;display:flex;flex-direction:column;"
            :style="idx === 1
              ? 'border: 2px solid #4f46e5; box-shadow: 0 12px 48px rgba(79,70,229,0.15); transform: scale(1.03);'
              : 'border: 1px solid #e2e8f0;'"
          >
            <div v-if="idx === 1" style="background:#4f46e5;color:white;text-align:center;padding:8px;font-size:11px;font-weight:700;letter-spacing:0.1em;">
              MAIS POPULAR
            </div>
            <div style="padding:28px;flex:1;display:flex;flex-direction:column;">
              <h3 style="font-size:15px;font-weight:700;color:#0f172a;margin:0 0 12px;">{{ plano.nome }}</h3>
              <div style="display:flex;align-items:flex-end;gap:4px;margin-bottom:4px;">
                <span style="font-size:38px;font-weight:800;color:#0f172a;line-height:1;">R$&nbsp;{{ formatPreco(plano.preco_mensal) }}</span>
                <span style="font-size:13px;color:#94a3b8;padding-bottom:4px;">/mês</span>
              </div>
              <p style="font-size:12px;color:#94a3b8;margin:0 0 20px;">ou R$ {{ formatPreco(plano.preco_anual) }}/ano</p>

              <div style="display:flex;align-items:center;gap:8px;padding:14px 0;border-top:1px solid #f1f5f9;border-bottom:1px solid #f1f5f9;margin-bottom:20px;">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="#4f46e5" style="width:16px;height:16px;flex-shrink:0;">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
                <span style="font-size:13px;color:#475569;">Até {{ plano.max_usuarios }} usuários</span>
              </div>

              <ul v-if="plano.features" style="list-style:none;padding:0;margin:0 0 24px;display:flex;flex-direction:column;gap:10px;">
                <li v-for="val in plano.features" :key="String(val)" style="display:flex;align-items:flex-start;gap:10px;font-size:14px;color:#334155;">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="#10b981" style="width:16px;height:16px;flex-shrink:0;margin-top:2px;">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
                  </svg>
                  {{ val }}
                </li>
              </ul>

              <div style="margin-top:auto;display:flex;flex-direction:column;gap:8px;">
                <button
                  @click="selecionarPlano(plano, 'mensal')"
                  style="width:100%;padding:12px;border-radius:12px;font-size:14px;font-weight:600;cursor:pointer;border:none;transition:background 0.15s;"
                  :style="idx === 1
                    ? 'background:#4f46e5;color:white;box-shadow:0 4px 16px rgba(79,70,229,0.3);'
                    : 'background:#0f172a;color:white;'"
                >
                  Assinar mensalmente
                </button>
                <button
                  @click="selecionarPlano(plano, 'anual')"
                  style="width:100%;padding:10px;border-radius:12px;font-size:12px;font-weight:500;cursor:pointer;background:white;border:1px solid #e2e8f0;color:#64748b;transition:background 0.15s;"
                  class="hover:bg-slate-50"
                >
                  Assinar anualmente · economize
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section style="background:#4f46e5;padding:80px 24px;">
      <div style="max-width:640px;margin:0 auto;text-align:center;">
        <h2 style="font-size:32px;font-weight:700;color:white;margin:0 0 16px;">Chega de confusão no final do mês</h2>
        <p style="font-size:15px;color:rgba(255,255,255,0.7);margin:0 0 36px;line-height:1.6;">Comece hoje e mantenha as contas do grupo sempre organizadas.</p>
        <a href="#planos" style="display:inline-flex;align-items:center;gap:8px;background:white;color:#4f46e5;font-weight:700;font-size:14px;padding:14px 32px;border-radius:12px;text-decoration:none;box-shadow:0 4px 16px rgba(0,0,0,0.15);">
          Ver planos
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:16px;height:16px;">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </a>
      </div>
    </section>

    <!-- Footer -->
    <footer style="background:#0c0a1e;border-top:1px solid rgba(255,255,255,0.05);padding:40px 24px;">
      <div style="max-width:1100px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px;">
        <div style="display:flex;align-items:center;gap:10px;">
          <div style="width:28px;height:28px;background:#4f46e5;border-radius:8px;display:flex;align-items:center;justify-content:center;">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="white" style="width:14px;height:14px;">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v12m-3-2.818l.879.659c1.171.879 3.07.879 4.242 0 1.172-.879 1.172-2.303 0-3.182C13.536 12.219 12.768 12 12 12c-.725 0-1.45-.22-2.003-.659-1.106-.879-1.106-2.303 0-3.182s2.9-.879 4.006 0l.415.33" />
            </svg>
          </div>
          <span style="font-size:14px;font-weight:600;color:white;">Gestor de Custos</span>
        </div>
        <p style="font-size:12px;color:#475569;margin:0;">© {{ new Date().getFullYear() }} · Todos os direitos reservados</p>
      </div>
    </footer>

    <!-- Checkout modal -->
    <Transition name="fade">
      <div v-if="showModal" style="position:fixed;inset:0;background:rgba(0,0,0,0.6);backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;z-index:50;padding:16px;" @click.self="showModal = false">
        <div style="background:white;border-radius:20px;width:100%;max-width:440px;overflow:hidden;box-shadow:0 24px 64px rgba(0,0,0,0.2);">
          <div style="padding:24px;border-bottom:1px solid #f1f5f9;display:flex;align-items:flex-start;justify-content:space-between;">
            <div>
              <h3 style="font-size:16px;font-weight:700;color:#0f172a;margin:0 0 4px;">Criar sua conta</h3>
              <p style="font-size:13px;color:#64748b;margin:0;">
                Plano <strong style="color:#334155;">{{ planoSelecionado?.nome }}</strong> · {{ periodoSelecionado }}
              </p>
            </div>
            <button @click="showModal = false" style="background:none;border:none;cursor:pointer;color:#94a3b8;padding:4px;" class="hover:text-slate-600 transition-colors">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" style="width:20px;height:20px;">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form @submit.prevent="iniciarCheckout" style="padding:24px;display:flex;flex-direction:column;gap:16px;">
            <div>
              <label style="display:block;font-size:12px;font-weight:500;color:#475569;margin-bottom:6px;">Nome do grupo</label>
              <input v-model="form.tenant_nome" required placeholder="Ex: Casa dos Amigos" style="width:100%;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;font-size:14px;outline:none;box-sizing:border-box;" class="focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <label style="display:block;font-size:12px;font-weight:500;color:#475569;margin-bottom:6px;">Seu nome</label>
                <input v-model="form.nome" required style="width:100%;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;font-size:14px;outline:none;box-sizing:border-box;" class="focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label style="display:block;font-size:12px;font-weight:500;color:#475569;margin-bottom:6px;">Usuário</label>
                <input v-model="form.username" required placeholder="sem espaços" style="width:100%;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;font-size:14px;outline:none;box-sizing:border-box;" class="focus:ring-2 focus:ring-indigo-500" />
              </div>
            </div>
            <div>
              <label style="display:block;font-size:12px;font-weight:500;color:#475569;margin-bottom:6px;">E-mail</label>
              <input v-model="form.email" type="email" required style="width:100%;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;font-size:14px;outline:none;box-sizing:border-box;" class="focus:ring-2 focus:ring-indigo-500" />
            </div>

            <div v-if="checkoutError" style="display:flex;align-items:center;gap:8px;background:#fef2f2;border-radius:8px;padding:10px 12px;font-size:13px;color:#dc2626;">
              {{ checkoutError }}
            </div>

            <div style="display:flex;gap:12px;padding-top:4px;">
              <button type="button" @click="showModal = false" style="flex:1;border:1px solid #e2e8f0;background:white;color:#334155;font-size:14px;font-weight:500;padding:12px;border-radius:12px;cursor:pointer;" class="hover:bg-slate-50 transition-colors">
                Cancelar
              </button>
              <button type="submit" :disabled="checkoutLoading" style="flex:1;background:#4f46e5;color:white;font-size:14px;font-weight:600;padding:12px;border-radius:12px;cursor:pointer;border:none;display:flex;align-items:center;justify-content:center;gap:8px;opacity:1;" class="hover:bg-indigo-700 disabled:opacity-60 transition-colors">
                <svg v-if="checkoutLoading" class="animate-spin" style="width:16px;height:16px;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle style="opacity:0.25;" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path style="opacity:0.75;" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                </svg>
                {{ checkoutLoading ? 'Aguarde...' : 'Ir para pagamento' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

interface Plano {
  id: number
  nome: string
  preco_mensal: number
  preco_anual: number
  max_usuarios: number
  features: Record<string, string> | null
}

const features = [
  { emoji: '💸', title: 'Divisão automática', desc: 'Configure uma vez e o sistema calcula o quanto cada um deve pagar mês a mês, sem esforço.' },
  { emoji: '📊', title: 'Histórico completo', desc: 'Veja todas as despesas passadas, quem pagou e quem ainda deve, com total transparência.' },
  { emoji: '🔔', title: 'Notificações', desc: 'Membros recebem alertas antes do vencimento para nunca perder um pagamento.' },
]

const planos = ref<Plano[]>([])
const loading = ref(true)
const showModal = ref(false)
const planoSelecionado = ref<Plano | null>(null)
const periodoSelecionado = ref<'mensal' | 'anual'>('mensal')
const checkoutLoading = ref(false)
const checkoutError = ref('')
const form = ref({ tenant_nome: '', nome: '', email: '', username: '' })

onMounted(async () => {
  try {
    const r = await axios.get('/api/planos/')
    planos.value = r.data
  } catch {
    // empty state shown
  } finally {
    loading.value = false
  }
})

function formatPreco(valor: number) {
  return new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2 }).format(Number(valor))
}

function selecionarPlano(plano: Plano, periodo: 'mensal' | 'anual') {
  planoSelecionado.value = plano
  periodoSelecionado.value = periodo
  checkoutError.value = ''
  showModal.value = true
}

async function iniciarCheckout() {
  if (!planoSelecionado.value) return
  checkoutLoading.value = true
  checkoutError.value = ''
  try {
    const r = await axios.post('/checkout/session', {
      plano_id: planoSelecionado.value.id,
      periodo: periodoSelecionado.value,
      ...form.value,
    })
    window.location.href = r.data.checkout_url
  } catch (err: any) {
    checkoutError.value = err.response?.data?.detail || 'Erro ao iniciar checkout.'
  } finally {
    checkoutLoading.value = false
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
