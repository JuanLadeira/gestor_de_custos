<template>
  <div class="min-h-screen bg-slate-50 flex items-center justify-center p-4">
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm p-10 max-w-md w-full text-center">
      <div class="w-16 h-16 bg-emerald-50 rounded-2xl flex items-center justify-center mx-auto mb-6">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-8 h-8 text-emerald-500">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h1 class="text-xl font-bold text-slate-900 mb-2">Pagamento confirmado!</h1>
      <p class="text-slate-500 text-sm mb-8 leading-relaxed">
        Sua assinatura foi ativada com sucesso. Verifique seu e-mail — você receberá as credenciais de acesso em instantes.
      </p>
      <div class="bg-slate-50 rounded-xl p-5 text-left mb-6">
        <p class="text-xs font-semibold text-slate-600 uppercase tracking-wide mb-3">Próximos passos</p>
        <ol class="space-y-2.5">
          <li v-for="(step, i) in steps" :key="i" class="flex items-start gap-3">
            <span class="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">{{ i + 1 }}</span>
            <span class="text-sm text-slate-600">{{ step }}</span>
          </li>
        </ol>
      </div>
      <a href="/login" class="block w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold py-2.5 rounded-xl text-sm transition-colors">
        Ir para o login
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
const steps = [
  'Verifique seu e-mail com as credenciais de acesso',
  'Faça login com o usuário e senha temporária',
  'Altere sua senha nas configurações',
  'Convide os membros do seu grupo',
]
</script>
