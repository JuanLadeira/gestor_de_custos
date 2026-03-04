<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type PagamentoRateio } from '../api/client'

const rateios = ref<PagamentoRateio[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const response = await api.getRateios()
    rateios.value = response.data
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Erro ao carregar rateios'
  } finally {
    loading.value = false
  }
})

function formatCurrency(value: string) {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(parseFloat(value))
}

function formatPercentage(value: string) {
  return `${parseFloat(value).toFixed(2)}%`
}

function getStatusClass(status: string) {
  return status === 'PAGO' ? 'status-pago' : 'status-pendente'
}
</script>

<template>
  <div class="rateios">
    <h2>Pagamentos Rateio</h2>

    <div v-if="loading" class="loading">Carregando...</div>

    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="rateios.length === 0" class="empty">
      Nenhum rateio encontrado.
    </div>

    <table v-else class="rateios-table">
      <thead>
        <tr>
          <th>Custo ID</th>
          <th>Usuario ID</th>
          <th>Porcentagem</th>
          <th>Valor</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="rateio in rateios" :key="rateio.id">
          <td>{{ rateio.custo_id }}</td>
          <td>{{ rateio.usuario_id }}</td>
          <td>{{ formatPercentage(rateio.porcentagem) }}</td>
          <td>{{ formatCurrency(rateio.valor_calculado) }}</td>
          <td>
            <span :class="['status', getStatusClass(rateio.status)]">
              {{ rateio.status }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.rateios {
  padding: 20px;
}

h2 {
  color: #2c3e50;
  margin-bottom: 20px;
}

.loading, .error, .empty {
  text-align: center;
  padding: 40px;
}

.error {
  color: #c00;
}

.rateios-table {
  width: 100%;
  border-collapse: collapse;
}

.rateios-table th,
.rateios-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.rateios-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #555;
}

.rateios-table tbody tr:hover {
  background-color: #f8f9fa;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-pago {
  background-color: #d4edda;
  color: #155724;
}

.status-pendente {
  background-color: #fff3cd;
  color: #856404;
}
</style>
