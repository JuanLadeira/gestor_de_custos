<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api, type Custo } from '../api/client'

const custos = ref<Custo[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const response = await api.getCustos()
    custos.value = response.data
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Erro ao carregar custos'
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

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString('pt-BR')
}

function getStatusClass(status: string) {
  return status === 'PAGO' ? 'status-pago' : 'status-pendente'
}
</script>

<template>
  <div class="custos">
    <h2>Custos</h2>

    <div v-if="loading" class="loading">Carregando...</div>

    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else-if="custos.length === 0" class="empty">
      Nenhum custo encontrado.
    </div>

    <table v-else class="custos-table">
      <thead>
        <tr>
          <th>Descricao</th>
          <th>Valor</th>
          <th>Vencimento</th>
          <th>Tipo</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="custo in custos" :key="custo.id">
          <td>{{ custo.descricao }}</td>
          <td>{{ formatCurrency(custo.valor) }}</td>
          <td>{{ formatDate(custo.data_vencimento) }}</td>
          <td>{{ custo.tipo }}</td>
          <td>
            <span :class="['status', getStatusClass(custo.status)]">
              {{ custo.status }}
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.custos {
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

.custos-table {
  width: 100%;
  border-collapse: collapse;
}

.custos-table th,
.custos-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.custos-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #555;
}

.custos-table tbody tr:hover {
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
